from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import httpx
import pytest
import pytest_asyncio

from openhire.api.server import create_app
from openhire.workforce.registry import AgentEntry, AgentRegistry
from openhire.workforce.required_skill import (
    REQUIRED_EMPLOYEE_SKILL_ID,
    REQUIRED_EMPLOYEE_SKILL_PROMPT_END,
    REQUIRED_EMPLOYEE_SKILL_PROMPT_START,
    required_employee_skill_path,
)
from openhire.workforce.store import OpenHireStore

try:
    from aiohttp.test_utils import TestClient, TestServer

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


def _make_agent() -> MagicMock:
    agent = MagicMock()
    agent.process_direct = AsyncMock(return_value="ok")
    agent._docker_agents_config = None
    agent.get_admin_snapshot = AsyncMock(return_value={})
    agent._connect_mcp = AsyncMock()
    agent.close_mcp = AsyncMock()
    return agent


def _local_skill_upload(
    *,
    filename: str = "SKILL.md",
    content: str | None = None,
) -> aiohttp.FormData:
    data = aiohttp.FormData()
    data.add_field(
        "file",
        (
            content
            or "---\n"
            "name: local-tooling\n"
            "description: Local skill for repository automation.\n"
            "homepage: https://example.com/skills/local-tooling\n"
            "license: MIT\n"
            "---\n\n"
            "# Local Tooling\n"
        ).encode("utf-8"),
        filename=filename,
        content_type="text/markdown",
    )
    return data


def _web_skill_response(
    body: str,
    *,
    url: str,
    status_code: int = 200,
) -> httpx.Response:
    return httpx.Response(
        status_code,
        content=body.encode("utf-8"),
        request=httpx.Request("GET", url),
    )


def _skill_markdown(name: str, description: str) -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\n{description}\n"


class _FakeClawHubProvider:
    def __init__(
        self,
        markdown_by_url: dict[str, str],
        *,
        search_results: dict[str, list[dict[str, str]]] | None = None,
        details_by_url: dict[str, dict[str, object]] | None = None,
    ) -> None:
        self.markdown_by_url = markdown_by_url
        self.search_results = search_results or {}
        self.details_by_url = details_by_url or {}
        self.fetch_calls: list[str] = []

    async def search(self, query: str, *, limit: int = 10) -> list[dict[str, str]]:
        return list(self.search_results.get(query, []))[:limit]

    async def fetch_skill_markdown(self, source_url: str) -> str:
        self.fetch_calls.append(source_url)
        return self.markdown_by_url[source_url]

    async def fetch_package_details(self, source_url: str) -> dict[str, object]:
        return dict(self.details_by_url.get(source_url, {}))


class _FakeSoulBannerProvider:
    def __init__(
        self,
        directories_by_path: dict[str, list[dict[str, object]]],
        markdown_by_url: dict[str, str | Exception],
        *,
        last_modified_by_path: dict[str, str | Exception] | None = None,
    ) -> None:
        self.directories_by_path = directories_by_path
        self.markdown_by_url = markdown_by_url
        self.last_modified_by_path = last_modified_by_path or {}
        self.list_calls: list[str] = []
        self.fetch_calls: list[str] = []
        self.modified_calls: list[str] = []

    async def list_directory(self, path: str) -> list[dict[str, object]]:
        self.list_calls.append(path)
        return [dict(item) for item in self.directories_by_path.get(path, [])]

    async def fetch_text(self, url: str) -> str:
        self.fetch_calls.append(url)
        payload = self.markdown_by_url[url]
        if isinstance(payload, Exception):
            raise payload
        return payload

    async def fetch_last_modified_at(self, path: str) -> str:
        self.modified_calls.append(path)
        payload = self.last_modified_by_path.get(path, "")
        if isinstance(payload, Exception):
            raise payload
        return str(payload)


class _FakeDirectMbtiSbtiProvider(_FakeSoulBannerProvider):
    def skill_file_url(self, path: str) -> str:
        return f"https://raw.example.test/Sbti-Mbti/main/{path}/SKILL.md"

    async def list_directory(self, path: str) -> list[dict[str, object]]:
        if "/" in path:
            raise AssertionError(f"unexpected role directory lookup: {path}")
        return await super().list_directory(path)


@pytest.mark.asyncio
async def test_http_soulbanner_provider_fetch_last_modified_at_falls_back_to_commit_page_and_caches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from openhire.skill_catalog import HttpSoulBannerSkillProvider, SoulBannerProviderError

    provider = HttpSoulBannerSkillProvider(last_modified_ttl_seconds=600)
    calls: list[str] = []

    async def fake_api(_path: str) -> str:
        raise SoulBannerProviderError("Client error '403 rate limit exceeded'")

    async def fake_get_with_retries(url: str, *, params=None):
        calls.append(url)
        return httpx.Response(
            200,
            text='<script type="application/json">{"payload":{"commitGroups":[{"commits":[{"committedDate":"2026-04-21T10:30:00Z"}]}]}}</script>',
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(provider, "_fetch_last_modified_at_via_api", fake_api)
    monkeypatch.setattr(provider, "_get_with_retries", fake_get_with_retries)

    first = await provider.fetch_last_modified_at("soulbanner_skills/hanli/SKILL.md")
    second = await provider.fetch_last_modified_at("soulbanner_skills/hanli/SKILL.md")

    assert first == "2026-04-21T10:30:00Z"
    assert second == "2026-04-21T10:30:00Z"
    assert calls == [
        "https://github.com/pzy2000/SoulBanner/commits/main/soulbanner_skills/hanli/SKILL.md",
    ]


@pytest.mark.asyncio
async def test_http_soulbanner_provider_list_directory_falls_back_to_tree_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from openhire.skill_catalog import HttpSoulBannerSkillProvider, SoulBannerProviderError

    provider = HttpSoulBannerSkillProvider()

    async def fake_get_with_retries(url: str, *, params=None):
        return httpx.Response(
            200,
            text='<script type="application/json">{"payload":{"codeViewTreeRoute":{"tree":{"items":[{"name":"hanli","path":"soulbanner_skills/hanli","contentType":"directory"},{"name":"SKILL.md","path":"soulbanner_skills/hanli/SKILL.md","contentType":"file"}]}}}}</script>',
            request=httpx.Request("GET", url),
        )

    async def fake_api_lookup(*args, **kwargs):
        raise SoulBannerProviderError("Client error '403 rate limit exceeded'")

    monkeypatch.setattr(provider, "_get_with_retries", fake_get_with_retries)
    monkeypatch.setattr(provider, "_provider_error", lambda message: SoulBannerProviderError(message))
    monkeypatch.setattr(HttpSoulBannerSkillProvider, "_get_with_retries", fake_get_with_retries, raising=False)

    original = provider._get_with_retries

    async def list_directory_with_api_failure(path: str):
        raise SoulBannerProviderError("Client error '403 rate limit exceeded'")

    # Force list_directory down the tree-page fallback path by replacing the API call after URL build.
    monkeypatch.setattr(provider, "_get_with_retries", original)
    monkeypatch.setattr(
        provider,
        "_validate_remote_url",
        lambda url: url,
    )

    async def fake_list_get(url: str, *, params=None):
        if "api.github.com" in url:
            raise SoulBannerProviderError("Client error '403 rate limit exceeded'")
        return await fake_get_with_retries(url, params=params)

    monkeypatch.setattr(provider, "_get_with_retries", fake_list_get)

    items = await provider.list_directory("soulbanner_skills")

    assert items == [
        {
            "type": "dir",
            "name": "hanli",
            "path": "soulbanner_skills/hanli",
            "download_url": "",
        },
        {
            "type": "file",
            "name": "SKILL.md",
            "path": "soulbanner_skills/hanli/SKILL.md",
            "download_url": "https://raw.githubusercontent.com/pzy2000/SoulBanner/main/soulbanner_skills/hanli/SKILL.md",
        },
    ]


def _patch_required_skill_file(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Path:
    skill_file = tmp_path / "excellent-employee" / "SKILL.md"
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text(required_employee_skill_path().read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr("openhire.workforce.required_skill._SKILL_FILE", skill_file)
    return skill_file


@pytest_asyncio.fixture
async def aiohttp_client():
    clients: list[TestClient] = []

    async def _make_client(app):
        client = TestClient(TestServer(app))
        await client.start_server()
        clients.append(client)
        return client

    try:
        yield _make_client
    finally:
        for client in clients:
            await client.close()


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_list_includes_required_employee_skill_initially(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    response = await client.get("/skills")

    assert response.status == 200
    body = await response.json()
    assert [item["id"] for item in body] == [REQUIRED_EMPLOYEE_SKILL_ID]
    assert body[0]["source"] == "system"
    assert body[0]["safety_status"] == "required"
    assert body[0]["external_id"] == REQUIRED_EMPLOYEE_SKILL_ID


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_import_accepts_multiple_records(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    response = await client.post(
        "/skills/import",
        json={
            "skills": [
                {
                    "source": "clawhub",
                    "external_id": "github",
                    "name": "Github",
                    "description": "Use the gh CLI.",
                    "version": "1.0.0",
                    "author": "steipete",
                    "license": "",
                    "source_url": "https://clawhub.ai/steipete/github",
                    "safety_status": "available",
                    "markdown": _skill_markdown("github", "Use the gh CLI."),
                },
                {
                    "source": "clawhub",
                    "external_id": "nano-gpt-cli",
                    "name": "Nano Gpt",
                    "description": "Use nano-gpt locally.",
                    "version": "0.1.2",
                    "author": "icework",
                    "license": "",
                    "source_url": "https://clawhub.ai/icework/nano-gpt-cli",
                    "safety_status": "",
                    "markdown": _skill_markdown("nano-gpt-cli", "Use nano-gpt locally."),
                },
            ]
        },
    )

    assert response.status == 201
    body = await response.json()
    assert len(body) == 2
    assert {item["external_id"] for item in body} == {"github", "nano-gpt-cli"}
    assert all(item["id"] for item in body)
    assert all(item["imported_at"] for item in body)

    list_response = await client.get("/skills")
    listed = await list_response.json()
    imported_listed = [item for item in listed if item["id"] != REQUIRED_EMPLOYEE_SKILL_ID]
    assert len(imported_listed) == 2


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_import_preserves_tags(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    response = await client.post(
        "/skills/import",
        json={
            "skills": [
                {
                    "source": "clawhub",
                    "external_id": "jira",
                    "name": "JIRA",
                    "description": "Manage tickets.",
                    "version": "1.0.0",
                    "author": "jdrhyne",
                    "license": "",
                    "source_url": "https://clawhub.ai/jdrhyne/jira",
                    "safety_status": "",
                    "markdown": _skill_markdown("jira", "Manage tickets."),
                    "tags": ["scenario:工单分派", "risk:unknown", "popular:high-downloads"],
                }
            ]
        },
    )

    assert response.status == 201
    imported = await response.json()
    assert imported[0]["tags"] == ["scenario:工单分派", "risk:unknown", "popular:high-downloads"]
    listed = await (await client.get("/skills")).json()
    jira = next(item for item in listed if item["id"] == imported[0]["id"])
    assert jira["tags"] == imported[0]["tags"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_soulbanner_search_returns_import_ready_records(aiohttp_client, tmp_path) -> None:
    arno_url = "https://raw.githubusercontent.com/pzy2000/SoulBanner/main/soulbanner_skills/changshu-arno/SKILL.md"
    musk_url = "https://raw.githubusercontent.com/pzy2000/SoulBanner/main/sovereign_skills/musk/SKILL.md"
    provider = _FakeSoulBannerProvider(
        {
            "soulbanner_skills": [
                {"type": "dir", "name": "changshu-arno", "path": "soulbanner_skills/changshu-arno"},
            ],
            "soulbanner_skills/changshu-arno": [
                {"type": "file", "name": "SKILL.md", "download_url": arno_url},
            ],
            "sovereign_skills": [
                {"type": "dir", "name": "musk", "path": "sovereign_skills/musk"},
            ],
            "sovereign_skills/musk": [
                {"type": "file", "name": "SKILL.md", "download_url": musk_url},
            ],
        },
        {
            arno_url: (
                "---\n"
                "name: 常数阿诺\n"
                "description: 一个专注于抽象问题拆解与工程复盘的角色。\n"
                "author: SoulBanner\n"
                "license: CC-BY-4.0\n"
                "---\n\n"
                "# 常数阿诺\n"
            ),
            musk_url: (
                "---\n"
                "name: Elon Musk\n"
                "description: A first-principles operator for hard-tech bets.\n"
                "author: SoulBanner\n"
                "license: CC-BY-4.0\n"
                "---\n\n"
                "# Elon Musk\n"
            ),
        },
        last_modified_by_path={
            "soulbanner_skills/changshu-arno/SKILL.md": "2026-04-21T10:30:00Z",
            "sovereign_skills/musk/SKILL.md": "2026-04-20T08:15:00Z",
        },
    )
    app = create_app(
        _make_agent(),
        model_name="test-model",
        workspace=tmp_path,
        soulbanner_provider=provider,
    )
    client = await aiohttp_client(app)

    response = await client.get("/skills/search/soulbanner")

    assert response.status == 200
    body = await response.json()
    assert [item["external_id"] for item in body] == [
        "soulbanner_skills/changshu-arno",
        "sovereign_skills/musk",
    ]
    assert [item["source"] for item in body] == ["soulbanner", "soulbanner"]
    assert body[0]["name"] == "常数阿诺"
    assert body[0]["author"] == "SoulBanner"
    assert body[0]["license"] == "CC-BY-4.0"
    assert body[0]["source_url"] == arno_url
    assert body[0]["updated_at"] == "2026-04-21T10:30:00Z"
    assert "collection:soulbanner_skills" in body[0]["tags"]
    assert body[0]["markdown"].startswith("---\nname: 常数阿诺")
    assert body[1]["name"] == "Elon Musk"
    assert body[1]["source_url"] == musk_url
    assert body[1]["updated_at"] == "2026-04-20T08:15:00Z"
    assert "collection:sovereign_skills" in body[1]["tags"]
    assert provider.fetch_calls == [arno_url, musk_url]
    assert provider.modified_calls == [
        "soulbanner_skills/changshu-arno/SKILL.md",
        "sovereign_skills/musk/SKILL.md",
    ]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_soulbanner_search_skips_invalid_roles_and_returns_valid_ones(aiohttp_client, tmp_path) -> None:
    valid_url = "https://raw.githubusercontent.com/pzy2000/SoulBanner/main/soulbanner_skills/hanli/SKILL.md"
    broken_url = "https://raw.githubusercontent.com/pzy2000/SoulBanner/main/sovereign_skills/trump/SKILL.md"
    provider = _FakeSoulBannerProvider(
        {
            "soulbanner_skills": [
                {"type": "dir", "name": "hanli", "path": "soulbanner_skills/hanli"},
            ],
            "soulbanner_skills/hanli": [
                {"type": "file", "name": "SKILL.md", "download_url": valid_url},
            ],
            "sovereign_skills": [
                {"type": "dir", "name": "trump", "path": "sovereign_skills/trump"},
            ],
            "sovereign_skills/trump": [
                {"type": "file", "name": "SKILL.md", "download_url": broken_url},
            ],
        },
        {
            valid_url: _skill_markdown("Han Li", "A systems-minded operator."),
            broken_url: "# missing frontmatter",
        },
    )
    app = create_app(
        _make_agent(),
        model_name="test-model",
        workspace=tmp_path,
        soulbanner_provider=provider,
    )
    client = await aiohttp_client(app)

    response = await client.get("/skills/search/soulbanner")

    assert response.status == 200
    body = await response.json()
    assert len(body) == 1
    assert body[0]["external_id"] == "soulbanner_skills/hanli"
    assert body[0]["name"] == "Han Li"
    assert body[0]["source"] == "soulbanner"
    assert "collection:soulbanner_skills" in body[0]["tags"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_mbti_sbti_search_returns_import_ready_records(aiohttp_client, tmp_path) -> None:
    intj_url = "https://raw.githubusercontent.com/pzy2000/Sbti-Mbti/main/mbti_skills/intj/SKILL.md"
    ctrl_url = "https://raw.githubusercontent.com/pzy2000/Sbti-Mbti/main/sbti_skills/ctrl/SKILL.md"
    provider = _FakeSoulBannerProvider(
        {
            "mbti_skills": [
                {"type": "dir", "name": "intj", "path": "mbti_skills/intj"},
            ],
            "mbti_skills/intj": [
                {"type": "file", "name": "SKILL.md", "download_url": intj_url},
            ],
            "sbti_skills": [
                {"type": "dir", "name": "ctrl", "path": "sbti_skills/ctrl"},
            ],
            "sbti_skills/ctrl": [
                {"type": "file", "name": "SKILL.md", "download_url": ctrl_url},
            ],
        },
        {
            intj_url: _skill_markdown("intj", "战略规划者。偏结构、远景、效率和系统设计。"),
            ctrl_url: _skill_markdown("ctrl", "拿捏者。控制、拿捏、占有欲、强约束。"),
        },
        last_modified_by_path={
            "mbti_skills/intj/SKILL.md": "2026-04-22T09:00:00Z",
            "sbti_skills/ctrl/SKILL.md": "2026-04-19T06:45:00Z",
        },
    )
    app = create_app(
        _make_agent(),
        model_name="test-model",
        workspace=tmp_path,
        mbti_sbti_provider=provider,
    )
    client = await aiohttp_client(app)

    response = await client.get("/skills/search/mbti-sbti")

    assert response.status == 200
    body = await response.json()
    assert [item["external_id"] for item in body] == [
        "mbti_skills/intj",
        "sbti_skills/ctrl",
    ]
    assert [item["source"] for item in body] == ["mbti-sbti", "mbti-sbti"]
    assert body[0]["name"] == "intj"
    assert body[0]["source_url"] == intj_url
    assert body[0]["updated_at"] == "2026-04-22T09:00:00Z"
    assert "collection:mbti_skills" in body[0]["tags"]
    assert body[0]["markdown"].startswith("---\nname: intj")
    assert body[1]["name"] == "ctrl"
    assert body[1]["source_url"] == ctrl_url
    assert body[1]["updated_at"] == "2026-04-19T06:45:00Z"
    assert "collection:sbti_skills" in body[1]["tags"]
    assert provider.fetch_calls == [intj_url, ctrl_url]
    assert provider.modified_calls == [
        "mbti_skills/intj/SKILL.md",
        "sbti_skills/ctrl/SKILL.md",
    ]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_mbti_sbti_search_skips_invalid_roles_and_returns_valid_ones(aiohttp_client, tmp_path) -> None:
    valid_url = "https://raw.githubusercontent.com/pzy2000/Sbti-Mbti/main/mbti_skills/infp/SKILL.md"
    broken_url = "https://raw.githubusercontent.com/pzy2000/Sbti-Mbti/main/sbti_skills/dead/SKILL.md"
    provider = _FakeSoulBannerProvider(
        {
            "mbti_skills": [
                {"type": "dir", "name": "infp", "path": "mbti_skills/infp"},
            ],
            "mbti_skills/infp": [
                {"type": "file", "name": "SKILL.md", "download_url": valid_url},
            ],
            "sbti_skills": [
                {"type": "dir", "name": "dead", "path": "sbti_skills/dead"},
            ],
            "sbti_skills/dead": [
                {"type": "file", "name": "SKILL.md", "download_url": broken_url},
            ],
        },
        {
            valid_url: _skill_markdown("infp", "共情理想派。"),
            broken_url: "# missing frontmatter",
        },
    )
    app = create_app(
        _make_agent(),
        model_name="test-model",
        workspace=tmp_path,
        mbti_sbti_provider=provider,
    )
    client = await aiohttp_client(app)

    response = await client.get("/skills/search/mbti-sbti")

    assert response.status == 200
    body = await response.json()
    assert len(body) == 1
    assert body[0]["external_id"] == "mbti_skills/infp"
    assert body[0]["name"] == "infp"
    assert body[0]["source"] == "mbti-sbti"
    assert "collection:mbti_skills" in body[0]["tags"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_soulbanner_search_keeps_valid_records_when_last_modified_lookup_fails(aiohttp_client, tmp_path) -> None:
    valid_url = "https://raw.githubusercontent.com/pzy2000/SoulBanner/main/soulbanner_skills/hanli/SKILL.md"
    provider = _FakeSoulBannerProvider(
        {
            "soulbanner_skills": [
                {"type": "dir", "name": "hanli", "path": "soulbanner_skills/hanli"},
            ],
            "soulbanner_skills/hanli": [
                {"type": "file", "name": "SKILL.md", "download_url": valid_url},
            ],
        },
        {
            valid_url: _skill_markdown("Han Li", "A systems-minded operator."),
        },
        last_modified_by_path={
            "soulbanner_skills/hanli/SKILL.md": RuntimeError("GitHub commits unavailable"),
        },
    )
    app = create_app(
        _make_agent(),
        model_name="test-model",
        workspace=tmp_path,
        soulbanner_provider=provider,
    )
    client = await aiohttp_client(app)

    response = await client.get("/skills/search/soulbanner")

    assert response.status == 200
    body = await response.json()
    assert len(body) == 1
    assert body[0]["external_id"] == "soulbanner_skills/hanli"
    assert body[0]["name"] == "Han Li"
    assert body[0]["updated_at"] == ""
    assert provider.modified_calls == ["soulbanner_skills/hanli/SKILL.md"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_mbti_sbti_search_uses_direct_raw_skill_urls(aiohttp_client, tmp_path) -> None:
    provider = _FakeDirectMbtiSbtiProvider(
        {
            "mbti_skills": [
                {"type": "dir", "name": "intj", "path": "mbti_skills/intj"},
            ],
            "sbti_skills": [
                {"type": "dir", "name": "ctrl", "path": "sbti_skills/ctrl"},
            ],
        },
        {
            "https://raw.example.test/Sbti-Mbti/main/mbti_skills/intj/SKILL.md": _skill_markdown(
                "intj",
                "战略规划者。",
            ),
            "https://raw.example.test/Sbti-Mbti/main/sbti_skills/ctrl/SKILL.md": _skill_markdown(
                "ctrl",
                "拿捏者。",
            ),
        },
    )
    app = create_app(
        _make_agent(),
        model_name="test-model",
        workspace=tmp_path,
        mbti_sbti_provider=provider,
    )
    client = await aiohttp_client(app)

    response = await client.get("/skills/search/mbti-sbti")

    assert response.status == 200
    body = await response.json()
    assert [item["external_id"] for item in body] == ["mbti_skills/intj", "sbti_skills/ctrl"]
    assert provider.list_calls == ["mbti_skills", "sbti_skills"]
    assert provider.fetch_calls == [
        "https://raw.example.test/Sbti-Mbti/main/mbti_skills/intj/SKILL.md",
        "https://raw.example.test/Sbti-Mbti/main/sbti_skills/ctrl/SKILL.md",
    ]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_mbti_sbti_search_returns_provider_error_when_no_usable_records(aiohttp_client, tmp_path) -> None:
    provider = _FakeSoulBannerProvider(
        {
            "mbti_skills": [],
            "sbti_skills": [],
        },
        {},
    )
    app = create_app(
        _make_agent(),
        model_name="test-model",
        workspace=tmp_path,
        mbti_sbti_provider=provider,
    )
    client = await aiohttp_client(app)

    response = await client.get("/skills/search/mbti-sbti")

    assert response.status == 502
    body = await response.json()
    assert "Mbti/Sbti search returned no usable skills" in body["error"]["message"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_import_deduplicates_existing_records(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    first = await client.post(
        "/skills/import",
        json={
            "skills": [
                {
                    "source": "clawhub",
                    "external_id": "github",
                    "name": "Github",
                    "description": "Use the gh CLI.",
                    "version": "1.0.0",
                    "author": "steipete",
                    "license": "",
                    "source_url": "https://clawhub.ai/steipete/github",
                    "safety_status": "",
                    "markdown": _skill_markdown("github", "Use the gh CLI."),
                }
            ]
        },
    )
    first_body = await first.json()

    second = await client.post(
        "/skills/import",
        json={
            "skills": [
                {
                    "source": "clawhub",
                    "external_id": "github",
                    "name": "Github Updated",
                    "description": "Updated summary.",
                    "version": "1.0.1",
                    "author": "steipete",
                    "license": "",
                    "source_url": "https://clawhub.ai/steipete/github",
                    "safety_status": "available",
                    "markdown": _skill_markdown("github-updated", "Updated summary."),
                }
            ]
        },
    )

    assert second.status == 201
    second_body = await second.json()
    assert second_body[0]["id"] == first_body[0]["id"]
    assert second_body[0]["name"] == "Github Updated"
    assert second_body[0]["version"] == "1.0.1"

    list_response = await client.get("/skills")
    listed = await list_response.json()
    imported_listed = [item for item in listed if item["id"] != REQUIRED_EMPLOYEE_SKILL_ID]
    assert len(imported_listed) == 1
    assert imported_listed[0]["id"] == first_body[0]["id"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_delete_rejects_required_employee_skill(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    delete_resp = await client.delete(f"/skills/{REQUIRED_EMPLOYEE_SKILL_ID}")

    assert delete_resp.status == 400
    body = await delete_resp.json()
    assert "required" in body["error"]["message"].lower()


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_delete_removes_local_record(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    import_resp = await client.post(
        "/skills/import",
        json={
            "skills": [
                {
                    "source": "clawhub",
                    "external_id": "github",
                    "name": "Github",
                    "description": "Use the gh CLI.",
                    "version": "1.0.0",
                    "author": "steipete",
                    "license": "",
                    "source_url": "https://clawhub.ai/steipete/github",
                    "safety_status": "",
                    "markdown": _skill_markdown("github", "Use the gh CLI."),
                }
            ]
        },
    )
    imported = await import_resp.json()

    delete_resp = await client.delete(f"/skills/{imported[0]['id']}")

    assert delete_resp.status == 204
    list_resp = await client.get("/skills")
    listed = await list_resp.json()
    assert [item["id"] for item in listed] == [REQUIRED_EMPLOYEE_SKILL_ID]

    missing_resp = await client.delete(f"/skills/{imported[0]['id']}")
    assert missing_resp.status == 404


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_required_skill_content_can_be_read_and_saved(
    aiohttp_client,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    skill_file = _patch_required_skill_file(monkeypatch, tmp_path)
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    get_resp = await client.get(f"/skills/{REQUIRED_EMPLOYEE_SKILL_ID}/content")

    assert get_resp.status == 200
    body = await get_resp.json()
    assert body["skill"]["id"] == REQUIRED_EMPLOYEE_SKILL_ID
    assert body["editable"] is True
    assert body["can_sync_employees"] is True
    assert body["content_source"] == "system-file"
    assert body["markdown"] == skill_file.read_text(encoding="utf-8")

    updated_markdown = body["markdown"].replace("每天固定总结", "每天稳定总结")
    save_resp = await client.put(
        f"/skills/{REQUIRED_EMPLOYEE_SKILL_ID}/content",
        json={"markdown": updated_markdown},
    )

    assert save_resp.status == 200
    saved = await save_resp.json()
    assert saved["markdown"] == updated_markdown
    assert saved["synced_employees"] == 0
    assert skill_file.read_text(encoding="utf-8") == updated_markdown


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_required_skill_content_rejects_invalid_frontmatter(
    aiohttp_client,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_required_skill_file(monkeypatch, tmp_path)
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    response = await client.put(
        f"/skills/{REQUIRED_EMPLOYEE_SKILL_ID}/content",
        json={"markdown": "---\nname: wrong\n---\n\n# Broken\n"},
    )

    assert response.status == 400
    body = await response.json()
    assert "description" in body["error"]["message"] or REQUIRED_EMPLOYEE_SKILL_ID in body["error"]["message"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_required_skill_content_can_sync_existing_employee_prompt_blocks(
    aiohttp_client,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_required_skill_file(monkeypatch, tmp_path)
    registry = AgentRegistry(OpenHireStore(tmp_path))
    registry.register(
        AgentEntry(
            agent_id="with-marker",
            name="With Marker",
            system_prompt=(
                f"Base\n\n{REQUIRED_EMPLOYEE_SKILL_PROMPT_START}\nold body\n"
                f"{REQUIRED_EMPLOYEE_SKILL_PROMPT_END}"
            ),
        )
    )
    registry.register(
        AgentEntry(
            agent_id="without-marker",
            name="Without Marker",
            system_prompt="No required block here.",
        )
    )
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)
    content_resp = await client.get(f"/skills/{REQUIRED_EMPLOYEE_SKILL_ID}/content")
    markdown = (await content_resp.json())["markdown"].replace("每天固定总结", "每天稳定总结")

    save_resp = await client.put(
        f"/skills/{REQUIRED_EMPLOYEE_SKILL_ID}/content",
        json={"markdown": markdown, "sync_employee_prompts": True},
    )

    assert save_resp.status == 200
    saved = await save_resp.json()
    assert saved["synced_employees"] == 1
    refreshed = AgentRegistry(OpenHireStore(tmp_path))
    with_marker = refreshed.get("with-marker")
    without_marker = refreshed.get("without-marker")
    assert with_marker is not None
    assert "每天稳定总结" in with_marker.system_prompt
    assert "old body" not in with_marker.system_prompt
    assert without_marker is not None
    assert without_marker.system_prompt == "No required block here."


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_preview_local_skill_returns_normalized_record(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    response = await client.post(
        "/skills/import/local/preview",
        data=_local_skill_upload(),
    )

    assert response.status == 200
    body = await response.json()
    assert body["skill"]["markdown"].startswith("---\nname: local-tooling")
    assert body == {
        "skill": {
            "source": "local",
            "external_id": "local-tooling",
            "name": "local-tooling",
            "description": "Local skill for repository automation.",
            "version": "",
            "author": "",
            "license": "MIT",
            "source_url": "https://example.com/skills/local-tooling",
            "updated_at": "",
            "safety_status": "",
            "markdown": body["skill"]["markdown"],
            "tags": [],
        }
    }


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_preview_local_skill_accepts_lowercase_filename(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    response = await client.post(
        "/skills/import/local/preview",
        data=_local_skill_upload(filename="skill.md"),
    )

    assert response.status == 200
    body = await response.json()
    assert body["skill"]["external_id"] == "local-tooling"


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_preview_local_skill_supports_folded_yaml_block_scalars(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    response = await client.post(
        "/skills/import/local/preview",
        data=_local_skill_upload(
            content=(
                "---\n"
                "name: local-tooling\n"
                "description: >\n"
                "  Local skill for repository automation.\n"
                "  Supports folded YAML descriptions.\n"
                "---\n\n"
                "# Local Tooling\n"
            ),
        ),
    )

    assert response.status == 200
    body = await response.json()
    assert body["skill"]["description"] == "Local skill for repository automation. Supports folded YAML descriptions."


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_preview_local_skill_ignores_nested_metadata(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    response = await client.post(
        "/skills/import/local/preview",
        data=_local_skill_upload(
            content=(
                "---\n"
                "name: gmail\n"
                "description: |\n"
                "  Gmail API integration with managed OAuth.\n"
                "metadata:\n"
                "  clawdbot:\n"
                "    requires:\n"
                "      env:\n"
                "        - MATON_API_KEY\n"
                "---\n\n"
                "# Gmail\n"
            ),
        ),
    )

    assert response.status == 200
    body = await response.json()
    assert body["skill"]["name"] == "gmail"
    assert body["skill"]["description"] == "Gmail API integration with managed OAuth."


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("filename", "content", "message"),
    [
        ("README.md", "---\nname: local-tooling\ndescription: ok\n---\n", "SKILL.md"),
        ("SKILL.md", "# Missing frontmatter\n", "frontmatter"),
        ("SKILL.md", "---\ndescription: Missing name.\n---\n", "name"),
        ("SKILL.md", "---\nname: local-tooling\n---\n", "description"),
    ],
)
async def test_skill_preview_local_skill_validates_input(
    aiohttp_client,
    tmp_path,
    filename,
    content,
    message,
) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    response = await client.post(
        "/skills/import/local/preview",
        data=_local_skill_upload(filename=filename, content=content),
    )

    assert response.status == 400
    body = await response.json()
    assert message in body["error"]["message"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_local_skill_preview_can_be_confirmed_and_deduplicated(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    preview = await client.post(
        "/skills/import/local/preview",
        data=_local_skill_upload(),
    )
    preview_body = await preview.json()

    first = await client.post(
        "/skills/import",
        json={"skills": [preview_body["skill"]]},
    )

    assert first.status == 201
    first_body = await first.json()
    assert first_body[0]["source"] == "local"

    updated_preview = await client.post(
        "/skills/import/local/preview",
        data=_local_skill_upload(
            content=(
                "---\n"
                "name: local-tooling\n"
                "description: Updated local summary.\n"
                "homepage: https://example.com/skills/local-tooling\n"
                "---\n\n"
                "# Local Tooling\n"
            ),
        ),
    )
    updated_preview_body = await updated_preview.json()

    second = await client.post(
        "/skills/import",
        json={"skills": [updated_preview_body["skill"]]},
    )

    assert second.status == 201
    second_body = await second.json()
    assert second_body[0]["id"] == first_body[0]["id"]
    assert second_body[0]["description"] == "Updated local summary."

    content_resp = await client.get(f"/skills/{second_body[0]['id']}/content")
    assert content_resp.status == 200
    content = await content_resp.json()
    assert content["content_source"] == "stored"
    assert "Updated local summary." in content["markdown"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_metadata_only_skill_content_is_generated_and_saved(aiohttp_client, tmp_path) -> None:
    source_url = "https://clawhub.ai/steipete/github"
    full_markdown = _skill_markdown("github", "Complete GitHub skill instructions.")
    provider = _FakeClawHubProvider({source_url: full_markdown})
    app = create_app(
        _make_agent(),
        model_name="test-model",
        workspace=tmp_path,
        skill_provider=provider,
    )
    client = await aiohttp_client(app)
    import_resp = await client.post(
        "/skills/import",
        json={
            "skills": [
                {
                    "source": "clawhub",
                    "external_id": "github",
                    "name": "Github",
                    "description": "Use the gh CLI.",
                    "version": "1.0.0",
                    "author": "steipete",
                    "license": "",
                    "source_url": source_url,
                    "safety_status": "",
                }
            ]
        },
    )
    imported = await import_resp.json()

    content_resp = await client.get(f"/skills/{imported[0]['id']}/content")

    assert content_resp.status == 200
    content = await content_resp.json()
    assert content["content_source"] == "stored"
    assert content["markdown"] == full_markdown
    assert provider.fetch_calls == [source_url]

    updated = content["markdown"].replace("Complete GitHub skill instructions.", "Use the GitHub CLI safely.")
    save_resp = await client.put(f"/skills/{imported[0]['id']}/content", json={"markdown": updated})

    assert save_resp.status == 200
    saved = await save_resp.json()
    assert saved["content_source"] == "stored"
    assert saved["skill"]["description"] == "Use the GitHub CLI safely."
    refreshed = await (await client.get(f"/skills/{imported[0]['id']}/content")).json()
    assert refreshed["content_source"] == "stored"
    assert "Use the GitHub CLI safely." in refreshed["markdown"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_clawhub_import_fetches_full_skill_markdown(aiohttp_client, tmp_path) -> None:
    source_url = "https://clawhub.ai/awspace/pdf"
    full_markdown = (
        "---\n"
        "name: pdf\n"
        "description: Full PDF skill.\n"
        "---\n\n"
        "# PDF Processing Guide\n\n"
        "Lots of complete PDF instructions.\n"
    )
    provider = _FakeClawHubProvider({source_url: full_markdown})
    app = create_app(
        _make_agent(),
        model_name="test-model",
        workspace=tmp_path,
        skill_provider=provider,
    )
    client = await aiohttp_client(app)

    import_resp = await client.post(
        "/skills/import",
        json={
            "skills": [
                {
                    "source": "clawhub",
                    "external_id": "pdf",
                    "name": "Pdf",
                    "description": "Short summary only.",
                    "version": "0.1.0",
                    "author": "awspace",
                    "license": "",
                    "source_url": source_url,
                    "safety_status": "",
                }
            ]
        },
    )

    assert import_resp.status == 201
    imported = await import_resp.json()
    assert imported[0]["description"] == "Full PDF skill."
    content = await (await client.get(f"/skills/{imported[0]['id']}/content")).json()
    assert content["content_source"] == "stored"
    assert content["markdown"] == full_markdown
    assert "Short summary only." not in content["markdown"]
    assert provider.fetch_calls == [source_url]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_clawhub_search_content_preview_returns_full_markdown(aiohttp_client, tmp_path) -> None:
    source_url = "https://clawhub.ai/awspace/pdf"
    full_markdown = _skill_markdown("pdf", "Full PDF skill.")
    provider = _FakeClawHubProvider({source_url: full_markdown})
    app = create_app(
        _make_agent(),
        model_name="test-model",
        workspace=tmp_path,
        skill_provider=provider,
    )
    client = await aiohttp_client(app)

    response = await client.get("/skills/search/clawhub/content", params={"source_url": source_url})

    assert response.status == 200
    body = await response.json()
    assert body["markdown_status"] == "ok"
    assert body["markdown_error"] == ""
    assert body["content_source"] == "clawhub"
    assert body["markdown"] == full_markdown
    assert body["skill"]["source_url"] == source_url
    assert body["skill"]["source"] == "clawhub"
    assert provider.fetch_calls == [source_url]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_clawhub_search_content_preview_returns_error_payload(aiohttp_client, tmp_path) -> None:
    source_url = "https://clawhub.ai/awspace/pdf"
    provider = _FakeClawHubProvider({})
    app = create_app(
        _make_agent(),
        model_name="test-model",
        workspace=tmp_path,
        skill_provider=provider,
    )
    client = await aiohttp_client(app)

    response = await client.get("/skills/search/clawhub/content", params={"source_url": source_url})

    assert response.status == 200
    body = await response.json()
    assert body["markdown_status"] == "error"
    assert body["markdown"] == ""
    assert body["markdown_error"]
    assert body["skill"]["source_url"] == source_url


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_clawhub_metadata_only_skill_content_backfills_markdown(aiohttp_client, tmp_path) -> None:
    source_url = "https://clawhub.ai/awspace/pdf"
    full_markdown = _skill_markdown("pdf", "Full PDF skill.")
    provider = _FakeClawHubProvider({source_url: full_markdown})
    store_dir = tmp_path / "openhire"
    store_dir.mkdir(parents=True)
    store_dir.joinpath("skills.json").write_text(
        json.dumps(
            {
                "skills": {
                    "legacy-pdf": {
                        "id": "legacy-pdf",
                        "source": "clawhub",
                        "external_id": "pdf",
                        "name": "Pdf",
                        "description": "Short summary only.",
                        "version": "0.1.0",
                        "author": "awspace",
                        "license": "",
                        "source_url": source_url,
                        "safety_status": "",
                        "imported_at": "2026-04-01T00:00:00+00:00",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    app = create_app(
        _make_agent(),
        model_name="test-model",
        workspace=tmp_path,
        skill_provider=provider,
    )
    client = await aiohttp_client(app)

    content = await (await client.get("/skills/legacy-pdf/content")).json()

    assert content["content_source"] == "stored"
    assert content["markdown"] == full_markdown
    assert provider.fetch_calls == [source_url]
    persisted = json.loads(store_dir.joinpath("skills.json").read_text(encoding="utf-8"))
    assert persisted["skills"]["legacy-pdf"]["markdown"] == full_markdown


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_clawhub_stored_markdown_is_not_overwritten_on_content_read(aiohttp_client, tmp_path) -> None:
    source_url = "https://clawhub.ai/awspace/pdf"
    stored_markdown = _skill_markdown("pdf", "Locally edited PDF skill.")
    provider = _FakeClawHubProvider({source_url: _skill_markdown("pdf", "Remote PDF skill.")})
    store_dir = tmp_path / "openhire"
    store_dir.mkdir(parents=True)
    store_dir.joinpath("skills.json").write_text(
        json.dumps(
            {
                "skills": {
                    "stored-pdf": {
                        "id": "stored-pdf",
                        "source": "clawhub",
                        "external_id": "pdf",
                        "name": "Pdf",
                        "description": "Locally edited PDF skill.",
                        "version": "0.1.0",
                        "author": "awspace",
                        "license": "",
                        "source_url": source_url,
                        "safety_status": "",
                        "markdown": stored_markdown,
                        "imported_at": "2026-04-01T00:00:00+00:00",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    app = create_app(
        _make_agent(),
        model_name="test-model",
        workspace=tmp_path,
        skill_provider=provider,
    )
    client = await aiohttp_client(app)

    content = await (await client.get("/skills/stored-pdf/content")).json()

    assert content["markdown"] == stored_markdown
    assert provider.fetch_calls == []


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_clawhub_preview_generation_writes_candidates_without_importing(aiohttp_client, tmp_path) -> None:
    gmail_url = "https://clawhub.ai/byungkyu/gmail"
    jira_url = "https://clawhub.ai/jdrhyne/jira"
    provider = _FakeClawHubProvider(
        {
            gmail_url: _skill_markdown("gmail", "Full Gmail instructions."),
            jira_url: _skill_markdown("jira", "Full Jira instructions."),
        },
        search_results={
            "gmail": [
                {
                    "source": "clawhub",
                    "external_id": "gmail",
                    "name": "Gmail",
                    "description": "Read and send Gmail.",
                    "version": "1.0.6",
                    "author": "byungkyu",
                    "license": "",
                    "source_url": gmail_url,
                    "safety_status": "",
                }
            ],
            "jira": [
                {
                    "source": "clawhub",
                    "external_id": "jira",
                    "name": "JIRA",
                    "description": "Manage tickets.",
                    "version": "1.3.3",
                    "author": "jdrhyne",
                    "license": "",
                    "source_url": jira_url,
                    "safety_status": "",
                }
            ],
        },
        details_by_url={
            gmail_url: {"downloads": 4200, "stars": 12, "risk": "unknown", "download_url": "https://pkg/gmail.zip"},
            jira_url: {"downloads": 300, "stars": 3, "risk": "suspicious", "download_url": "https://pkg/jira.zip"},
        },
    )
    app = create_app(
        _make_agent(),
        model_name="test-model",
        workspace=tmp_path,
        skill_provider=provider,
    )
    client = await aiohttp_client(app)

    response = await client.post("/skills/import/clawhub/preview", json={"min_count": 2, "max_count": 5})

    assert response.status == 200
    preview = await response.json()
    assert preview["count"] >= 2
    names = {item["name"] for item in preview["candidates"]}
    assert {"Gmail", "JIRA"} <= names
    gmail = next(item for item in preview["candidates"] if item["name"] == "Gmail")
    jira = next(item for item in preview["candidates"] if item["name"] == "JIRA")
    assert "scenario:邮箱与消息分诊" in gmail["tags"]
    assert "popular:high-downloads" in gmail["tags"]
    assert "risk:suspicious" in jira["tags"]
    assert gmail["markdown_status"] == "ok"
    assert jira["markdown_status"] == "ok"
    preview_path = tmp_path / "openhire" / "skill_import_preview.json"
    assert preview_path.exists()
    assert not (tmp_path / "openhire" / "skills.json").exists()


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_preview_web_skill_returns_normalized_record(
    aiohttp_client,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(self, url: str):
        assert url == "https://unpkg.com/@pencil.dev/cli@0.2.5/SKILL.md"
        return _web_skill_response(
            (
                "---\n"
                "name: pencil-cli\n"
                "description: Use Pencil CLI.\n"
                "homepage: https://pencil.dev\n"
                "license: Apache-2.0\n"
                "---\n\n"
                "# Pencil CLI\n"
            ),
            url=url,
        )

    monkeypatch.setattr("openhire.skill_catalog.validate_url_target", lambda url: (True, ""))
    monkeypatch.setattr("openhire.skill_catalog.validate_resolved_url", lambda url: (True, ""))
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    response = await client.post(
        "/skills/import/web/preview",
        json={"url": "https://unpkg.com/@pencil.dev/cli@0.2.5/SKILL.md"},
    )

    assert response.status == 200
    body = await response.json()
    assert body["skill"]["markdown"].startswith("---\nname: pencil-cli")
    assert body == {
        "skill": {
            "source": "web",
            "external_id": "pencil-cli",
            "name": "pencil-cli",
            "description": "Use Pencil CLI.",
            "version": "",
            "author": "",
            "license": "Apache-2.0",
            "source_url": "https://unpkg.com/@pencil.dev/cli@0.2.5/SKILL.md",
            "updated_at": "",
            "safety_status": "",
            "markdown": body["skill"]["markdown"],
            "tags": [],
        }
    }


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_preview_web_skill_supports_folded_yaml_block_scalars(
    aiohttp_client,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(self, url: str):
        return _web_skill_response(
            (
                "---\n"
                "name: pencil-design\n"
                "description: >\n"
                "  Create high-quality visual designs using the Pencil CLI tool.\n"
                "  Use this skill whenever the user wants something visual created.\n"
                "---\n\n"
                "# Pencil Design\n"
            ),
            url=url,
        )

    monkeypatch.setattr("openhire.skill_catalog.validate_url_target", lambda url: (True, ""))
    monkeypatch.setattr("openhire.skill_catalog.validate_resolved_url", lambda url: (True, ""))
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    response = await client.post(
        "/skills/import/web/preview",
        json={"url": "https://unpkg.com/@pencil.dev/cli@0.2.5/SKILL.md"},
    )

    assert response.status == 200
    body = await response.json()
    assert body["skill"]["name"] == "pencil-design"
    assert body["skill"]["description"] == (
        "Create high-quality visual designs using the Pencil CLI tool. "
        "Use this skill whenever the user wants something visual created."
    )


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("url", "message"),
    [
        ("ftp://example.com/SKILL.md", "http/https"),
        ("https://example.com/README.md", "SKILL.md"),
        ("https:///SKILL.md", "domain"),
        ("http://127.0.0.1/SKILL.md", "Blocked"),
    ],
)
async def test_skill_preview_web_skill_validates_input(
    aiohttp_client,
    tmp_path,
    url,
    message,
) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    response = await client.post("/skills/import/web/preview", json={"url": url})

    assert response.status == 400
    body = await response.json()
    assert message in body["error"]["message"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_preview_web_skill_maps_upstream_404_to_502(
    aiohttp_client,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(self, url: str):
        response = _web_skill_response("not found", url=url, status_code=404)
        raise httpx.HTTPStatusError("404 Not Found", request=response.request, response=response)

    monkeypatch.setattr("openhire.skill_catalog.validate_url_target", lambda url: (True, ""))
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    response = await client.post(
        "/skills/import/web/preview",
        json={"url": "https://example.com/pkg/SKILL.md"},
    )

    assert response.status == 502
    body = await response.json()
    assert "404 Not Found" in body["error"]["message"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_preview_web_skill_rejects_unsafe_redirect_target(
    aiohttp_client,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(self, url: str):
        return _web_skill_response(
            "---\nname: pencil-cli\ndescription: ok\n---\n",
            url="https://redirected.example.test/pkg/SKILL.md",
        )

    monkeypatch.setattr("openhire.skill_catalog.validate_url_target", lambda url: (True, ""))
    monkeypatch.setattr(
        "openhire.skill_catalog.validate_resolved_url",
        lambda url: (False, "Redirect target is a private address: 127.0.0.1"),
    )
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    response = await client.post(
        "/skills/import/web/preview",
        json={"url": "https://example.com/pkg/SKILL.md"},
    )

    assert response.status == 502
    body = await response.json()
    assert "Redirect target" in body["error"]["message"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_preview_web_skill_rejects_invalid_remote_content(
    aiohttp_client,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(self, url: str):
        return _web_skill_response("# not a skill\n", url=url)

    monkeypatch.setattr("openhire.skill_catalog.validate_url_target", lambda url: (True, ""))
    monkeypatch.setattr("openhire.skill_catalog.validate_resolved_url", lambda url: (True, ""))
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    response = await client.post(
        "/skills/import/web/preview",
        json={"url": "https://example.com/pkg/SKILL.md"},
    )

    assert response.status == 502
    body = await response.json()
    assert "frontmatter" in body["error"]["message"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_web_skill_preview_can_be_confirmed_and_deduplicated_by_source_url(
    aiohttp_client,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = {
        "https://example.com/a/SKILL.md": (
            "---\n"
            "name: shared-skill\n"
            "description: From URL A.\n"
            "---\n\n"
            "# Shared\n"
        ),
        "https://example.com/b/SKILL.md": (
            "---\n"
            "name: shared-skill\n"
            "description: From URL B.\n"
            "---\n\n"
            "# Shared\n"
        ),
    }
    calls = {"https://example.com/a/SKILL.md": 0, "https://example.com/b/SKILL.md": 0}

    async def fake_get(self, url: str):
        if url == "https://example.com/a/SKILL.md":
            calls[url] += 1
            body = source[url] if calls[url] == 1 else (
                "---\n"
                "name: shared-skill\n"
                "description: Updated URL A summary.\n"
                "---\n\n"
                "# Shared\n"
            )
            return _web_skill_response(body, url=url)
        return _web_skill_response(source[url], url=url)

    monkeypatch.setattr("openhire.skill_catalog.validate_url_target", lambda url: (True, ""))
    monkeypatch.setattr("openhire.skill_catalog.validate_resolved_url", lambda url: (True, ""))
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    preview_a = await client.post("/skills/import/web/preview", json={"url": "https://example.com/a/SKILL.md"})
    preview_a_body = await preview_a.json()
    first = await client.post("/skills/import", json={"skills": [preview_a_body["skill"]]})
    first_body = await first.json()

    preview_a_updated = await client.post("/skills/import/web/preview", json={"url": "https://example.com/a/SKILL.md"})
    preview_a_updated_body = await preview_a_updated.json()
    second = await client.post("/skills/import", json={"skills": [preview_a_updated_body["skill"]]})
    second_body = await second.json()

    preview_b = await client.post("/skills/import/web/preview", json={"url": "https://example.com/b/SKILL.md"})
    preview_b_body = await preview_b.json()
    third = await client.post("/skills/import", json={"skills": [preview_b_body["skill"]]})
    third_body = await third.json()

    assert first.status == 201
    assert second.status == 201
    assert third.status == 201
    assert first_body[0]["id"] == second_body[0]["id"]
    assert second_body[0]["description"] == "Updated URL A summary."
    assert first_body[0]["id"] != third_body[0]["id"]

    listed = await (await client.get("/skills")).json()
    imported_listed = [item for item in listed if item["id"] != REQUIRED_EMPLOYEE_SKILL_ID]
    assert len(imported_listed) == 2
    assert {item["source_url"] for item in imported_listed} == {
        "https://example.com/a/SKILL.md",
        "https://example.com/b/SKILL.md",
    }

    content_a = await (await client.get(f"/skills/{second_body[0]['id']}/content")).json()
    assert content_a["content_source"] == "stored"
    assert "Updated URL A summary." in content_a["markdown"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_governance_scan_persists_issues_and_ignore_state(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    import_resp = await client.post(
        "/skills/import",
        json={
            "skills": [
                {
                    "source": "web",
                    "external_id": "github-a",
                    "name": "GitHub",
                    "description": "Use GitHub safely.",
                    "source_url": "https://example.com/a/SKILL.md",
                    "markdown": _skill_markdown("github-a", "Use GitHub safely."),
                },
                {
                    "source": "web",
                    "external_id": "github-b",
                    "name": "GitHub",
                    "description": "Use GitHub safely.",
                    "source_url": "https://example.com/b/SKILL.md",
                    "markdown": _skill_markdown("github-b", "Use GitHub safely."),
                },
                {
                    "source": "local",
                    "external_id": "calendar",
                    "name": "Calendar",
                    "description": "Manage meetings.",
                    "source_url": "",
                    "markdown": "",
                },
            ]
        },
    )
    imported = await import_resp.json()
    registry = AgentRegistry(OpenHireStore(tmp_path))
    registry.register(
        AgentEntry(
            agent_id="ops",
            name="Ops",
            role="运营巡检员",
            skills=["Old GitHub", "Missing"],
            skill_ids=[REQUIRED_EMPLOYEE_SKILL_ID, imported[0]["id"], "missing-skill"],
            system_prompt="巡检系统。",
            agent_type="nanobot",
        )
    )
    registry.register(
        AgentEntry(
            agent_id="legacy",
            name="Legacy",
            role="日程助理",
            skills=["Calendar"],
            skill_ids=[],
            system_prompt="安排会议。",
            agent_type="nanobot",
        )
    )

    scan_resp = await client.post("/admin/api/skills/governance/scan", json={})

    assert scan_resp.status == 200
    report = await scan_resp.json()
    issue_types = {issue["type"] for issue in report["issues"]}
    assert {
        "duplicate_exact",
        "duplicate_name",
        "orphan_skill",
        "missing_content",
        "stale_employee_binding",
        "legacy_unbound_employee",
    } <= issue_types
    assert report["summary"]["businessSkillCount"] == 3
    assert report["summary"]["employeeCoveragePercent"] == 50
    assert report["opportunities"]
    assert (tmp_path / "openhire" / "skill_governance.json").exists()

    ignored_issue_ids = [issue["id"] for issue in report["issues"][:2]]
    ignore_resp = await client.post(
        "/admin/api/skills/governance/ignore",
        json={"issue_ids": ignored_issue_ids, "ignored": True},
    )

    assert ignore_resp.status == 200
    ignored_report = await ignore_resp.json()
    ignored_issues = [issue for issue in ignored_report["issues"] if issue["id"] in ignored_issue_ids]
    assert len(ignored_issues) == len(ignored_issue_ids)
    assert all(issue["ignored"] is True for issue in ignored_issues)


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_governance_actions_dry_run_and_execute_cleanup(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)
    imported = await (
        await client.post(
            "/skills/import",
            json={
                "skills": [
                    {
                        "source": "web",
                        "external_id": "slack-a",
                        "name": "Slack",
                        "description": "Handle Slack messages.",
                        "source_url": "https://example.com/slack-a/SKILL.md",
                        "markdown": _skill_markdown("slack-a", "Handle Slack messages."),
                    },
                    {
                        "source": "web",
                        "external_id": "slack-b",
                        "name": "Slack",
                        "description": "Handle Slack messages.",
                        "source_url": "https://example.com/slack-b/SKILL.md",
                        "markdown": _skill_markdown("slack-b", "Handle Slack messages."),
                    },
                    {
                        "source": "local",
                        "external_id": "orphan",
                        "name": "Orphan",
                        "description": "Unused skill.",
                        "markdown": _skill_markdown("orphan", "Unused skill."),
                    },
                ]
            },
        )
    ).json()
    canonical_id = imported[0]["id"]
    duplicate_id = imported[1]["id"]
    orphan_id = imported[2]["id"]
    registry = AgentRegistry(OpenHireStore(tmp_path))
    registry.register(
        AgentEntry(
            agent_id="inbox-a",
            name="Inbox A",
            role="消息分诊员",
            skills=["Slack"],
            skill_ids=[REQUIRED_EMPLOYEE_SKILL_ID, canonical_id, duplicate_id, "missing-skill"],
            system_prompt="处理消息。",
            agent_type="nanobot",
        )
    )
    registry.register(
        AgentEntry(
            agent_id="inbox-b",
            name="Inbox B",
            role="消息分诊员",
            skills=["Slack"],
            skill_ids=[REQUIRED_EMPLOYEE_SKILL_ID, canonical_id],
            system_prompt="处理消息。",
            agent_type="nanobot",
        )
    )
    scan = await (await client.post("/admin/api/skills/governance/scan", json={})).json()
    merge_issue = next(issue for issue in scan["issues"] if issue["type"] == "duplicate_exact")

    dry_run_resp = await client.post(
        "/admin/api/skills/governance/actions",
        json={"action": "merge_duplicates", "issue_ids": [merge_issue["id"]], "dry_run": True},
    )

    assert dry_run_resp.status == 200
    dry_run = await dry_run_resp.json()
    assert dry_run["dryRun"] is True
    assert dry_run["plan"]["skillsDeleted"] == [duplicate_id]
    assert dry_run["plan"]["canonicalSkills"][0]["canonicalSkillId"] == canonical_id

    execute_resp = await client.post(
        "/admin/api/skills/governance/actions",
        json={
            "action": "merge_duplicates",
            "issue_ids": [merge_issue["id"]],
            "dry_run": False,
            "confirm": True,
        },
    )

    assert execute_resp.status == 200
    executed = await execute_resp.json()
    assert executed["executed"] is True
    listed_ids = [item["id"] for item in await (await client.get("/skills")).json()]
    assert duplicate_id not in listed_ids
    inbox_a = AgentRegistry(OpenHireStore(tmp_path)).get("inbox-a")
    assert inbox_a is not None
    assert inbox_a.skill_ids == [REQUIRED_EMPLOYEE_SKILL_ID, canonical_id, "missing-skill"]

    repair_resp = await client.post(
        "/admin/api/skills/governance/actions",
        json={"action": "repair_employee_bindings", "employee_ids": ["inbox-a"], "dry_run": False, "confirm": True},
    )
    assert repair_resp.status == 200
    repaired = AgentRegistry(OpenHireStore(tmp_path)).get("inbox-a")
    assert repaired is not None
    assert repaired.skill_ids == [REQUIRED_EMPLOYEE_SKILL_ID, canonical_id]
    assert repaired.skills[0]

    delete_resp = await client.post(
        "/admin/api/skills/governance/actions",
        json={"action": "delete_orphans", "skill_ids": [orphan_id], "dry_run": False, "confirm": True},
    )
    assert delete_resp.status == 200
    final_ids = [item["id"] for item in await (await client.get("/skills")).json()]
    assert orphan_id not in final_ids
    state = json.loads((tmp_path / "openhire" / "skill_governance.json").read_text(encoding="utf-8"))
    assert state["audit_log"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_governance_remote_discovery_warning_is_non_blocking(aiohttp_client, tmp_path) -> None:
    provider = _FakeClawHubProvider({}, search_results={})

    async def fail_search(query: str, *, limit: int = 10):
        raise RuntimeError("remote unavailable")

    provider.search = fail_search
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path, skill_provider=provider)
    client = await aiohttp_client(app)

    response = await client.post("/admin/api/skills/governance/scan", json={"include_remote": True})

    assert response.status == 200
    report = await response.json()
    assert report["warnings"]
    assert report["opportunities"]
