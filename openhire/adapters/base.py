"""Base class for Docker-based external agent adapters."""

import asyncio
import json
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from loguru import logger


class DockerAgent(ABC):
    """Abstract base for an agent that runs inside a Docker container."""

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Unique identifier, e.g. 'claude-code'."""
        ...

    @property
    @abstractmethod
    def default_image(self) -> str:
        """Docker image to use, e.g. 'paulgauthier/aider'."""
        ...

    @abstractmethod
    def build_command(
        self,
        task: str,
        role: str | None = None,
        tools: list[str] | None = None,
        skills: list[str] | None = None,
        *,
        instance_id: str | None = None,
    ) -> list[str]:
        """Return the CMD array for ``docker run`` or ``docker exec``.

        ``instance_id`` is set for persistent containers (typically the Docker
        container name) so adapters can scope CLI session routing.
        """
        ...

    def environment(self, env_config: dict[str, str]) -> dict[str, str]:
        """Merge agent-specific env vars with user-provided ones."""
        return dict(env_config)

    def parse_output(self, stdout: str, stderr: str, exit_code: int) -> str:
        """Extract meaningful result from container output."""
        if exit_code != 0 and stderr.strip():
            return f"Agent exited with code {exit_code}.\nStderr:\n{stderr[:3000]}"
        return stdout.strip() or "(no output)"

    @property
    def needs_build(self) -> bool:
        """True if this agent needs a local ``docker build`` (no pre-built image)."""
        return False

    @property
    def build_context_local_path(self) -> str | None:
        """Local filesystem path to use as docker build context.

        Takes precedence over ``build_context_url`` when the path exists.
        Defaults to ``~/.openhire/repos/<agent_name>``.
        """
        return str(Path.home() / ".openhire" / "repos" / self.agent_name)

    @property
    def build_context_url(self) -> str | None:
        """GitHub (or other) URL passed directly to ``docker build``.

        When set, ``_ensure_image`` runs ``docker build -t <image> <url>``
        instead of writing a temporary Dockerfile.  Takes precedence over
        ``dockerfile`` when both are defined.
        """
        return None

    @property
    def dockerfile(self) -> str | None:
        """Inline Dockerfile content when ``needs_build`` is True and no ``build_context_url``."""
        return None

    def _build_task_prompt(
        self,
        task: str,
        role: str | None = None,
        skills: list[str] | None = None,
    ) -> str:
        """Weave role and skills into the task prompt (for agents without native flags)."""
        parts: list[str] = []
        if role:
            parts.append(f"[Role: {role}]")
        if skills:
            parts.append(f"[Skills: {', '.join(skills)}]")
        parts.append(task)
        return "\n".join(parts)

    def build_task_prompt(
        self,
        task: str,
        role: str | None = None,
        skills: list[str] | None = None,
    ) -> str:
        """Public prompt builder shared by command execution and observability."""
        return self._build_task_prompt(task, role, skills)

    def docker_create_options(self, workspace: Path) -> list[str]:
        """Return docker create/run flags needed before the image name."""
        return ["-v", f"{workspace}:/workspace", "-w", "/workspace"]

    def docker_run_options(self, workspace: Path) -> list[str]:
        """Return docker run flags needed before the image name."""
        return self.docker_create_options(workspace)

    def docker_exec_options(self, workspace: Path | None = None) -> list[str]:
        """Return docker exec flags needed before the container name."""
        return []

    @property
    def persistent_entrypoint(self) -> str | None:
        """Optional entrypoint override used for persistent keepalive containers."""
        return None

    def persistent_command(self) -> list[str]:
        """Command used to keep a persistent container alive after creation."""
        return ["tail", "-f", "/dev/null"]

    def build_init_commands(self, agent_cfg: dict[str, Any]) -> list[list[str]]:
        """Return commands to run inside the container after first creation.

        Override in subclasses to perform one-time setup (e.g. ACP config).
        Each inner list is a single command passed to ``docker exec``.
        """
        return []

    @property
    def bootstrap_template_paths(self) -> dict[str, str]:
        """Runtime paths for agent-native bootstrap templates."""
        return {}

    async def init_exec_monitor(
        self,
        container_name: str,
        workspace: Path | None = None,
    ) -> Any | None:
        """Return adapter-specific monitor state for `exec_in_container`.

        Return ``None`` to disable extra monitoring and use the default blocking
        communicate path.
        """
        return None

    async def poll_exec_monitor(
        self,
        container_name: str,
        monitor_state: Any,
    ) -> str | None:
        """Poll adapter-specific runtime state and optionally return a terminal error."""
        return None


# ---------------------------------------------------------------------------
# Docker image helpers
# ---------------------------------------------------------------------------

async def _ensure_image(adapter: DockerAgent, image: str) -> None:
    """Pull or build the Docker image if not present locally."""
    check = await asyncio.create_subprocess_exec(
        "docker", "image", "inspect", image,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    if await check.wait() == 0:
        return

    if adapter.needs_build:
        logger.info("Building Docker image {} for agent {}", image, adapter.agent_name)
        # Prefer local clone over remote URL to avoid network issues at build time
        local_path = adapter.build_context_local_path
        if local_path and Path(local_path).exists():
            build_context = local_path
        elif adapter.build_context_url:
            build_context = adapter.build_context_url
        elif adapter.dockerfile:
            build_context = None
        else:
            raise RuntimeError(
                f"Agent {adapter.agent_name} needs_build=True but has no "
                "build_context_local_path, build_context_url, or dockerfile"
            )

        if build_context:
            proc = await asyncio.create_subprocess_exec(
                "docker", "build", "-t", image, build_context,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, err = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"docker build failed: {err.decode()[:2000]}")
        else:
            with tempfile.TemporaryDirectory() as tmp:
                df = Path(tmp) / "Dockerfile"
                df.write_text(adapter.dockerfile)
                proc = await asyncio.create_subprocess_exec(
                    "docker", "build", "-t", image, tmp,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, err = await proc.communicate()
                if proc.returncode != 0:
                    raise RuntimeError(f"docker build failed: {err.decode()[:2000]}")
    else:
        logger.info("Pulling Docker image {} for agent {}", image, adapter.agent_name)
        proc = await asyncio.create_subprocess_exec(
            "docker", "pull", image,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, err = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"docker pull failed: {err.decode()[:2000]}")


# ---------------------------------------------------------------------------
# Persistent container lifecycle
# ---------------------------------------------------------------------------

async def _inspect_container(name: str) -> str | None:
    """Return container status ('running', 'exited', ...) or None if not found."""
    proc = await asyncio.create_subprocess_exec(
        "docker", "inspect", "-f", "{{.State.Status}}", name,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    out, _ = await proc.communicate()
    if proc.returncode != 0:
        return None
    return out.decode().strip()


async def inspect_container_status(name: str) -> str | None:
    """Inspect a Docker container and return its runtime state."""
    return await _inspect_container(name)


async def ensure_running(
    adapter: DockerAgent,
    instance_name: str,
    agent_cfg: dict[str, Any],
    workspace: Path,
) -> str:
    """Ensure a persistent container is running. Create it if needed."""
    container_name = agent_cfg.get("container_name") or f"openhire-{instance_name}"
    image = agent_cfg.get("image") or adapter.default_image
    await _ensure_image(adapter, image)
    env = adapter.environment(agent_cfg.get("env", {}))
    memory_limit = agent_cfg.get("memory_limit", "2g")
    cpus = agent_cfg.get("cpus", "2")

    status = await _inspect_container(container_name)

    if status == "running":
        if await _container_runtime_matches(container_name, image, env):
            return container_name
        logger.info("Recreating running container {} to apply config changes", container_name)
        await _remove_container(container_name)
        status = None

    if status is not None:
        if await _container_runtime_matches(container_name, image, env):
            logger.info("Starting stopped container {}", container_name)
            proc = await asyncio.create_subprocess_exec(
                "docker", "start", container_name,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, err = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"docker start failed: {err.decode()[:2000]}")
            return container_name
        logger.info("Recreating existing container {} to apply config changes", container_name)
        await _remove_container(container_name)

    # Container doesn't exist — create and start
    logger.info("Creating persistent container {} (image: {})", container_name, image)
    create_cmd: list[str] = [
        "docker", "create",
        "--name", container_name,
        "--network=host",
        f"--memory={memory_limit}",
        f"--cpus={cpus}",
    ]
    if adapter.persistent_entrypoint:
        create_cmd.extend(["--entrypoint", adapter.persistent_entrypoint])
    create_cmd.extend(adapter.docker_create_options(workspace))
    for k, v in env.items():
        create_cmd.extend(["-e", f"{k}={v}"])
    # Keep container alive with a no-op process
    create_cmd.append(image)
    create_cmd.extend(adapter.persistent_command())

    proc = await asyncio.create_subprocess_exec(
        *create_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, err = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"docker create failed: {err.decode()[:2000]}")

    proc = await asyncio.create_subprocess_exec(
        "docker", "start", container_name,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, err = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"docker start failed: {err.decode()[:2000]}")

    # Run one-time init commands (e.g. ACP config for OpenClaw)
    init_cmds = adapter.build_init_commands(agent_cfg)
    for cmd in init_cmds:
        proc = await asyncio.create_subprocess_exec(
            "docker", "exec", container_name, *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, err = await proc.communicate()
        if proc.returncode != 0:
            logger.warning("Init command failed in {}: {}", container_name, err.decode()[:500])

    return container_name


async def _container_runtime_matches(
    container_name: str,
    image: str,
    expected_env: dict[str, str],
) -> bool:
    """Return True when the existing container matches the requested runtime config."""
    actual = await _inspect_container_runtime(container_name)
    if actual is None:
        # If inspect fails unexpectedly, avoid destructive recreation.
        return True
    actual_image, actual_env = actual
    if actual_image != image:
        return False
    for key, value in expected_env.items():
        if actual_env.get(key) != value:
            return False
    return True


async def _inspect_container_runtime(name: str) -> tuple[str, dict[str, str]] | None:
    """Return the container image and environment variable map."""
    proc = await asyncio.create_subprocess_exec(
        "docker", "inspect", "-f", "{{.Config.Image}}\n{{json .Config.Env}}", name,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    out, _ = await proc.communicate()
    if proc.returncode != 0:
        return None

    text = out.decode(errors="replace")
    image, _, env_json = text.partition("\n")
    env_map: dict[str, str] = {}
    try:
        raw_env = json.loads(env_json.strip() or "[]")
    except json.JSONDecodeError:
        raw_env = []
    if isinstance(raw_env, list):
        for item in raw_env:
            if not isinstance(item, str) or "=" not in item:
                continue
            key, value = item.split("=", 1)
            env_map[key] = value
    return image.strip(), env_map


async def _remove_container(name: str) -> None:
    """Force-remove an existing container."""
    proc = await asyncio.create_subprocess_exec(
        "docker", "rm", "-f", name,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, err = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"docker rm failed: {err.decode()[:2000]}")


async def exec_in_container(
    container_name: str,
    adapter: DockerAgent,
    task: str,
    role: str | None,
    tools: list[str] | None,
    skills: list[str] | None,
    timeout: int = 300,
    workspace: Path | None = None,
) -> str:
    """Execute a task inside a running persistent container."""
    cmd = adapter.build_command(
        task, role, tools, skills, instance_id=container_name,
    )

    exec_opts = adapter.docker_exec_options(workspace)
    docker_cmd = ["docker", "exec", *exec_opts, container_name] + cmd

    logger.info("Exec in container [{}]: {}", container_name, " ".join(cmd[:5]))

    proc = await asyncio.create_subprocess_exec(
        *docker_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    monitor_state = await adapter.init_exec_monitor(container_name, workspace)
    if monitor_state is None:
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return f"Error: Task in container '{container_name}' timed out after {timeout}s."

        return adapter.parse_output(
            stdout_bytes.decode(errors="replace"),
            stderr_bytes.decode(errors="replace"),
            proc.returncode or 0,
        )

    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    stdout_task = asyncio.create_task(_drain_stream(proc.stdout, stdout_chunks))
    stderr_task = asyncio.create_task(_drain_stream(proc.stderr, stderr_chunks))
    early_error: str | None = None
    timed_out = False
    start = asyncio.get_running_loop().time()
    poll_interval_s = 1.0

    try:
        while True:
            elapsed = asyncio.get_running_loop().time() - start
            remaining = timeout - elapsed
            if remaining <= 0:
                timed_out = True
                _kill_process(proc)
                await proc.wait()
                break

            try:
                await asyncio.wait_for(proc.wait(), timeout=min(poll_interval_s, remaining))
                break
            except asyncio.TimeoutError:
                try:
                    early_error = await adapter.poll_exec_monitor(container_name, monitor_state)
                except Exception as exc:  # pragma: no cover - defensive path
                    logger.debug("Exec monitor poll failed for {}: {}", container_name, exc)
                    continue
                if early_error:
                    _kill_process(proc)
                    await proc.wait()
                    break
    finally:
        await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)

    stdout_text = "".join(stdout_chunks)
    stderr_text = "".join(stderr_chunks)

    if early_error:
        return early_error
    if timed_out:
        return f"Error: Task in container '{container_name}' timed out after {timeout}s."

    return adapter.parse_output(
        stdout_text,
        stderr_text,
        proc.returncode or 0,
    )


def _kill_process(proc: asyncio.subprocess.Process) -> None:
    """Kill a subprocess and swallow lookup races when it already exited."""
    try:
        proc.kill()
    except ProcessLookupError:
        return


async def _drain_stream(
    stream: asyncio.StreamReader | None,
    chunks: list[str],
) -> None:
    """Read the full stream into the target chunk list."""
    if stream is None:
        return
    while True:
        block = await stream.read(4096)
        if not block:
            return
        if not isinstance(block, (bytes, bytearray)):
            return
        chunks.append(block.decode(errors="replace"))


# ---------------------------------------------------------------------------
# Ephemeral container (original mode)
# ---------------------------------------------------------------------------

async def run_container(
    adapter: DockerAgent,
    task: str,
    role: str | None,
    tools: list[str] | None,
    skills: list[str] | None,
    workspace: Path,
    agent_cfg: dict[str, Any],
    timeout: int = 300,
) -> str:
    """Run an agent in an ephemeral Docker container and return its output."""
    image = agent_cfg.get("image") or adapter.default_image
    await _ensure_image(adapter, image)

    env = adapter.environment(agent_cfg.get("env", {}))
    instance_id = agent_cfg.get("container_name") or agent_cfg.get("instance_name")
    cmd = adapter.build_command(
        task, role, tools, skills, instance_id=instance_id,
    )

    memory_limit = agent_cfg.get("memory_limit", "2g")
    cpus = agent_cfg.get("cpus", "2")

    docker_cmd: list[str] = [
        "docker", "run", "--rm",
        "--network=host",
        f"--memory={memory_limit}",
        f"--cpus={cpus}",
    ]
    docker_cmd.extend(adapter.docker_run_options(workspace))
    for k, v in env.items():
        docker_cmd.extend(["-e", f"{k}={v}"])
    docker_cmd.append(image)
    docker_cmd.extend(cmd)

    logger.info("Running docker agent [{}]: {}", adapter.agent_name, " ".join(cmd[:5]))

    proc = await asyncio.create_subprocess_exec(
        *docker_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=timeout,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return f"Error: Agent '{adapter.agent_name}' timed out after {timeout}s."

    return adapter.parse_output(
        stdout_bytes.decode(errors="replace"),
        stderr_bytes.decode(errors="replace"),
        proc.returncode or 0,
    )
