"""LLM-driven skill selection for digital employees."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import inspect
import json
import re
from typing import Any

from openhire.skill_catalog import SkillCatalogService, SkillEntry
from openhire.workforce.required_skill import REQUIRED_EMPLOYEE_SKILL_ID


_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
_CLAWHUB_QUERY_ALIASES = (
    ("backend", "python"),
    ("后端", "python"),
    ("api", "api"),
    ("sql", "sql"),
    ("database", "sql"),
    ("数据", "data"),
    ("github", "github"),
    ("docker", "docker"),
    ("container", "docker"),
    ("kubernetes", "kubernetes"),
    ("k8s", "kubernetes"),
    ("sre", "kubernetes"),
    ("devops", "docker"),
    ("monitor", "monitor"),
    ("observability", "monitor"),
    ("监控", "monitor"),
    ("prometheus", "prometheus"),
    ("grafana", "grafana"),
    ("incident", "monitor"),
    ("algorithm", "model"),
    ("算法", "model"),
    ("ranking", "model"),
    ("排序", "model"),
    ("retrieval", "search"),
    ("recall", "search"),
    ("召回", "search"),
    ("metric", "report"),
    ("指标", "report"),
    ("ml", "ml"),
    ("machine learning", "ml"),
    ("pytorch", "pytorch"),
    ("frontend", "react"),
    ("前端", "react"),
    ("react", "react"),
    ("ui", "frontend"),
    ("browser", "browser"),
    ("web", "web"),
    ("search", "search"),
    ("analyst", "spreadsheet"),
    ("分析", "spreadsheet"),
    ("spreadsheet", "spreadsheet"),
    ("report", "report"),
    ("报表", "report"),
    ("calendar", "calendar"),
    ("meeting", "calendar"),
    ("email", "gmail"),
    ("邮箱", "gmail"),
    ("slack", "slack"),
    ("notion", "notion"),
    ("jira", "jira"),
    ("linear", "linear"),
)


@dataclass(slots=True)
class EmployeeSkillSelection:
    skill_ids: list[str] = field(default_factory=list)
    skill_names: list[str] = field(default_factory=list)
    installed_skill_ids: list[str] = field(default_factory=list)
    installed_skills: list[dict[str, Any]] = field(default_factory=list)
    remote_queries: list[str] = field(default_factory=list)
    reason: str = ""
    warning: str = ""


class EmployeeSkillSelector:
    """Select relevant local catalog skills for an employee using an LLM."""

    def __init__(
        self,
        *,
        provider: Any | None,
        max_skills: int = 5,
        retries: int = 5,
    ) -> None:
        self._provider = provider
        self._max_skills = max(1, int(max_skills))
        self._retries = max(1, int(retries))

    async def select(
        self,
        *,
        name: str,
        role: str,
        system_prompt: str,
        explicit_skills: list[str] | None,
        catalog_skills: list[SkillEntry],
    ) -> EmployeeSkillSelection:
        candidates = [
            skill for skill in catalog_skills
            if skill.id and skill.id != REQUIRED_EMPLOYEE_SKILL_ID
        ]
        chat_with_retry = getattr(self._provider, "chat_with_retry", None) if self._provider else None
        if not chat_with_retry or not inspect.iscoroutinefunction(chat_with_retry):
            return EmployeeSkillSelection(warning="Skill selection skipped: no LLM provider available.")
        if not candidates:
            return EmployeeSkillSelection(warning="Skill selection skipped: local skill catalog is empty.")

        last_error = ""
        for attempt in range(1, self._retries + 1):
            response = await chat_with_retry(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You select local skill IDs for a digital employee. "
                            "Return JSON only: {\"skill_ids\":[\"...\"],\"reason\":\"...\"}. "
                            f"Pick at most {self._max_skills} IDs. Do not include {REQUIRED_EMPLOYEE_SKILL_ID}."
                        ),
                    },
                    {
                        "role": "user",
                        "content": self._build_prompt(
                            name=name,
                            role=role,
                            system_prompt=system_prompt,
                            explicit_skills=explicit_skills or [],
                            catalog_skills=candidates,
                            last_error=last_error,
                        ),
                    },
                ],
                max_tokens=900,
                temperature=0,
            )
            try:
                return self._parse_selection(str(response.content or ""), candidates)
            except ValueError as exc:
                last_error = str(exc)
                if attempt >= self._retries:
                    return EmployeeSkillSelection(
                        warning=f"Skill selection failed after {self._retries} attempts: {last_error}"
                    )

        return EmployeeSkillSelection(warning=f"Skill selection failed after {self._retries} attempts.")

    async def select_with_clawhub(
        self,
        *,
        name: str,
        role: str,
        system_prompt: str,
        explicit_skills: list[str] | None,
        catalog_skills: list[SkillEntry],
        skill_catalog: SkillCatalogService,
        skill_provider: Any | None,
    ) -> EmployeeSkillSelection:
        candidates = self._local_candidates(catalog_skills)
        chat_with_retry = self._chat_with_retry()
        if not chat_with_retry:
            return EmployeeSkillSelection(warning="Skill selection skipped: no LLM provider available.")

        remote_queries: list[str] = []
        try:
            remote_queries = await self._generate_clawhub_queries(
                chat_with_retry,
                name=name,
                role=role,
                system_prompt=system_prompt,
                explicit_skills=explicit_skills or [],
            )
            remote_records = await self._search_clawhub_skills(skill_provider, remote_queries)
            if not remote_records:
                fallback_queries = self._fallback_clawhub_queries(
                    name=name,
                    role=role,
                    system_prompt=system_prompt,
                    explicit_skills=explicit_skills or [],
                    current_queries=remote_queries,
                )
                if fallback_queries:
                    remote_queries = [*remote_queries, *fallback_queries]
                    remote_records = await self._search_clawhub_skills(skill_provider, fallback_queries)
        except Exception as exc:
            local_selection = await self.select(
                name=name,
                role=role,
                system_prompt=system_prompt,
                explicit_skills=explicit_skills,
                catalog_skills=catalog_skills,
            )
            local_selection.remote_queries = remote_queries
            local_selection.warning = self._join_warnings(
                f"ClawHub skill recommendation skipped: {exc}",
                local_selection.warning,
            )
            return local_selection

        if not candidates and not remote_records:
            return EmployeeSkillSelection(
                remote_queries=remote_queries,
                warning="Skill selection skipped: local skill catalog is empty and ClawHub returned no candidates.",
            )

        mixed_candidates = self._build_mixed_candidates(candidates, remote_records)
        mixed_selection = await self._select_mixed_candidates(
            chat_with_retry,
            name=name,
            role=role,
            system_prompt=system_prompt,
            explicit_skills=explicit_skills or [],
            mixed_candidates=mixed_candidates,
        )
        mixed_selection.remote_queries = remote_queries
        return await self._install_selected_clawhub_skills(
            mixed_selection,
            mixed_candidates=mixed_candidates,
            skill_catalog=skill_catalog,
            skill_provider=skill_provider,
        )

    def _build_prompt(
        self,
        *,
        name: str,
        role: str,
        system_prompt: str,
        explicit_skills: list[str],
        catalog_skills: list[SkillEntry],
        last_error: str,
    ) -> str:
        catalog = [
            {
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "tags": list(skill.tags),
            }
            for skill in catalog_skills
        ]
        payload = {
            "employee": {
                "name": name,
                "role": role,
                "system_prompt": system_prompt,
                "explicit_skills": explicit_skills,
            },
            "available_skills": catalog,
        }
        if last_error:
            payload["previous_error"] = last_error
        return json.dumps(payload, ensure_ascii=False)

    def _chat_with_retry(self) -> Any | None:
        chat_with_retry = getattr(self._provider, "chat_with_retry", None) if self._provider else None
        if not chat_with_retry or not inspect.iscoroutinefunction(chat_with_retry):
            return None
        return chat_with_retry

    @staticmethod
    def _local_candidates(catalog_skills: list[SkillEntry]) -> list[SkillEntry]:
        return [
            skill for skill in catalog_skills
            if skill.id and skill.id != REQUIRED_EMPLOYEE_SKILL_ID
        ]

    async def _generate_clawhub_queries(
        self,
        chat_with_retry: Any,
        *,
        name: str,
        role: str,
        system_prompt: str,
        explicit_skills: list[str],
    ) -> list[str]:
        response = await chat_with_retry(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Generate ClawHub search queries for finding public agent skills. "
                        "Return JSON only: {\"queries\":[\"...\"]}. "
                        "Return 3 to 5 short, concrete tool or workflow keywords."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "employee": {
                                "name": name,
                                "role": role,
                                "system_prompt": system_prompt,
                                "explicit_skills": explicit_skills,
                            }
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            max_tokens=300,
            temperature=0,
        )
        payload = self._extract_json(str(response.content or ""))
        raw_queries = payload.get("queries")
        if not isinstance(raw_queries, list):
            raise ValueError("ClawHub query generation response must include queries.")
        queries: list[str] = []
        seen: set[str] = set()
        for item in raw_queries:
            query = str(item or "").strip()
            if not query:
                continue
            key = query.casefold()
            if key in seen:
                continue
            seen.add(key)
            queries.append(query[:80])
            if len(queries) >= 5:
                break
        if not queries:
            raise ValueError("ClawHub query generation returned no usable queries.")
        return queries

    async def _search_clawhub_skills(self, skill_provider: Any | None, queries: list[str]) -> list[dict[str, Any]]:
        if skill_provider is None:
            return []
        by_key: dict[tuple[str, str], dict[str, Any]] = {}
        search = getattr(skill_provider, "search", None)
        if not search or not inspect.iscoroutinefunction(search):
            return []
        for query in queries:
            for record in await search(query, limit=6):
                if not isinstance(record, Mapping):
                    continue
                normalized = self._normalize_remote_record(record)
                key = self._identity_key(normalized)
                if not key[1] or key in by_key:
                    continue
                by_key[key] = normalized
        return list(by_key.values())

    def _fallback_clawhub_queries(
        self,
        *,
        name: str,
        role: str,
        system_prompt: str,
        explicit_skills: list[str],
        current_queries: list[str],
    ) -> list[str]:
        query_text = " ".join([*current_queries, name, role, system_prompt, *explicit_skills]).casefold()
        existing = {query.casefold() for query in current_queries}
        fallback: list[str] = []
        for needle, query in _CLAWHUB_QUERY_ALIASES:
            if needle not in query_text or query.casefold() in existing:
                continue
            existing.add(query.casefold())
            fallback.append(query)
            if len(fallback) >= 5:
                break
        return fallback

    @staticmethod
    def _normalize_remote_record(record: Mapping[str, Any]) -> dict[str, Any]:
        def text(value: Any) -> str:
            return str(value or "").strip()

        return {
            "source": text(record.get("source")) or "clawhub",
            "external_id": text(record.get("external_id")),
            "name": text(record.get("name")) or text(record.get("external_id")) or "ClawHub Skill",
            "description": text(record.get("description")),
            "version": text(record.get("version")),
            "author": text(record.get("author")),
            "license": text(record.get("license")),
            "source_url": text(record.get("source_url")),
            "safety_status": text(record.get("safety_status")),
            "tags": list(record.get("tags")) if isinstance(record.get("tags"), list) else [],
        }

    @staticmethod
    def _identity_key(record: Mapping[str, Any]) -> tuple[str, str]:
        source = str(record.get("source") or "").strip()
        external_id = str(record.get("external_id") or "").strip()
        source_url = str(record.get("source_url") or "").strip()
        if source == "web":
            return source, source_url or external_id
        return source, external_id or source_url

    def _build_mixed_candidates(
        self,
        local_skills: list[SkillEntry],
        remote_records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        existing_by_identity = {
            self._identity_key(skill.to_public_dict()): skill
            for skill in local_skills
        }
        candidates: list[dict[str, Any]] = [
            {
                "selection_id": skill.id,
                "kind": "local",
                "skill": skill,
                "record": skill.to_public_dict(),
                "existing_skill": skill,
            }
            for skill in local_skills
        ]
        for index, record in enumerate(remote_records):
            existing_skill = existing_by_identity.get(self._identity_key(record))
            candidates.append(
                {
                    "selection_id": f"clawhub:{index}",
                    "kind": "clawhub",
                    "skill": existing_skill,
                    "record": record,
                    "existing_skill": existing_skill,
                }
            )
        return candidates

    async def _select_mixed_candidates(
        self,
        chat_with_retry: Any,
        *,
        name: str,
        role: str,
        system_prompt: str,
        explicit_skills: list[str],
        mixed_candidates: list[dict[str, Any]],
    ) -> EmployeeSkillSelection:
        last_error = ""
        for attempt in range(1, self._retries + 1):
            response = await chat_with_retry(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You select skill candidate IDs for a digital employee. "
                            "Candidates may be existing local skills or ClawHub skills. "
                            "Return JSON only: {\"skill_ids\":[\"...\"],\"reason\":\"...\"}. "
                            f"Pick at most {self._max_skills} IDs. Do not include {REQUIRED_EMPLOYEE_SKILL_ID}."
                        ),
                    },
                    {
                        "role": "user",
                        "content": self._build_mixed_prompt(
                            name=name,
                            role=role,
                            system_prompt=system_prompt,
                            explicit_skills=explicit_skills,
                            mixed_candidates=mixed_candidates,
                            last_error=last_error,
                        ),
                    },
                ],
                max_tokens=900,
                temperature=0,
            )
            try:
                return self._parse_mixed_selection(str(response.content or ""), mixed_candidates)
            except ValueError as exc:
                last_error = str(exc)
                if attempt >= self._retries:
                    return EmployeeSkillSelection(
                        warning=f"Skill selection failed after {self._retries} attempts: {last_error}"
                    )

        return EmployeeSkillSelection(warning=f"Skill selection failed after {self._retries} attempts.")

    def _build_mixed_prompt(
        self,
        *,
        name: str,
        role: str,
        system_prompt: str,
        explicit_skills: list[str],
        mixed_candidates: list[dict[str, Any]],
        last_error: str,
    ) -> str:
        available_skills = []
        for candidate in mixed_candidates:
            record = candidate["record"]
            available_skills.append(
                {
                    "id": candidate["selection_id"],
                    "source": candidate["kind"],
                    "already_local": candidate.get("existing_skill") is not None,
                    "name": record.get("name", ""),
                    "description": record.get("description", ""),
                    "tags": list(record.get("tags") or []),
                }
            )
        payload = {
            "employee": {
                "name": name,
                "role": role,
                "system_prompt": system_prompt,
                "explicit_skills": explicit_skills,
            },
            "available_skills": available_skills,
        }
        if last_error:
            payload["previous_error"] = last_error
        return json.dumps(payload, ensure_ascii=False)

    def _parse_mixed_selection(
        self,
        content: str,
        mixed_candidates: list[dict[str, Any]],
    ) -> EmployeeSkillSelection:
        payload = self._extract_json(content)
        raw_ids = payload.get("skill_ids")
        if not isinstance(raw_ids, list):
            raise ValueError("skill_ids must be an array.")
        reason = str(payload.get("reason") or "").strip()
        by_id = {candidate["selection_id"]: candidate for candidate in mixed_candidates}
        selected_ids: list[str] = []
        warning_parts: list[str] = []
        saw_required = False
        for item in raw_ids:
            selection_id = str(item or "").strip()
            if not selection_id:
                continue
            if selection_id == REQUIRED_EMPLOYEE_SKILL_ID:
                saw_required = True
                continue
            if selection_id not in by_id:
                raise ValueError(f"Unknown skill id: {selection_id}")
            if selection_id not in selected_ids:
                selected_ids.append(selection_id)

        if saw_required:
            warning_parts.append(f"{REQUIRED_EMPLOYEE_SKILL_ID} is managed separately and was ignored.")
        if len(selected_ids) > self._max_skills:
            selected_ids = selected_ids[: self._max_skills]
            warning_parts.append(f"Skill selection limited to {self._max_skills} skills.")

        return EmployeeSkillSelection(
            skill_ids=selected_ids,
            reason=reason,
            warning=" ".join(warning_parts),
        )

    async def _install_selected_clawhub_skills(
        self,
        selection: EmployeeSkillSelection,
        *,
        mixed_candidates: list[dict[str, Any]],
        skill_catalog: SkillCatalogService,
        skill_provider: Any | None,
    ) -> EmployeeSkillSelection:
        by_selection_id = {candidate["selection_id"]: candidate for candidate in mixed_candidates}
        selected_ids: list[str] = []
        selected_names: list[str] = []
        installed_skill_ids: list[str] = []
        installed_skills: list[dict[str, Any]] = []
        warning = selection.warning

        for selection_id in selection.skill_ids:
            candidate = by_selection_id.get(selection_id)
            if candidate is None:
                continue
            existing_skill = candidate.get("existing_skill")
            if isinstance(existing_skill, SkillEntry):
                self._append_selected_skill(
                    existing_skill.id,
                    existing_skill.name,
                    selected_ids=selected_ids,
                    selected_names=selected_names,
                )
                continue

            record = dict(candidate.get("record") or {})
            source_url = str(record.get("source_url") or "").strip()
            try:
                markdown = await skill_provider.fetch_skill_markdown(source_url)
                [entry] = skill_catalog.upsert_many([{**record, "markdown": markdown}])
            except Exception as exc:
                warning = self._join_warnings(warning, f"ClawHub skill install skipped: {exc}")
                continue
            self._append_selected_skill(
                entry.id,
                entry.name,
                selected_ids=selected_ids,
                selected_names=selected_names,
            )
            installed_skill_ids.append(entry.id)
            installed_skills.append(entry.to_public_dict())

        return EmployeeSkillSelection(
            skill_ids=selected_ids,
            skill_names=selected_names,
            installed_skill_ids=installed_skill_ids,
            installed_skills=installed_skills,
            remote_queries=selection.remote_queries,
            reason=selection.reason,
            warning=warning,
        )

    @staticmethod
    def _append_selected_skill(
        skill_id: str,
        skill_name: str,
        *,
        selected_ids: list[str],
        selected_names: list[str],
    ) -> None:
        if not skill_id or skill_id in selected_ids:
            return
        selected_ids.append(skill_id)
        selected_names.append(skill_name)

    @staticmethod
    def _join_warnings(*warnings: str) -> str:
        return " ".join(str(warning or "").strip() for warning in warnings if str(warning or "").strip())

    def _parse_selection(self, content: str, catalog_skills: list[SkillEntry]) -> EmployeeSkillSelection:
        payload = self._extract_json(content)
        raw_ids = payload.get("skill_ids")
        if not isinstance(raw_ids, list):
            raise ValueError("skill_ids must be an array.")
        reason = str(payload.get("reason") or "").strip()

        by_id = {skill.id: skill for skill in catalog_skills}
        selected_ids: list[str] = []
        warning_parts: list[str] = []
        saw_required = False
        for item in raw_ids:
            skill_id = str(item or "").strip()
            if not skill_id:
                continue
            if skill_id == REQUIRED_EMPLOYEE_SKILL_ID:
                saw_required = True
                continue
            if skill_id not in by_id:
                raise ValueError(f"Unknown skill id: {skill_id}")
            if skill_id not in selected_ids:
                selected_ids.append(skill_id)

        if saw_required:
            warning_parts.append(f"{REQUIRED_EMPLOYEE_SKILL_ID} is managed separately and was ignored.")
        if len(selected_ids) > self._max_skills:
            selected_ids = selected_ids[: self._max_skills]
            warning_parts.append(f"Skill selection limited to {self._max_skills} skills.")

        return EmployeeSkillSelection(
            skill_ids=selected_ids,
            skill_names=[by_id[skill_id].name for skill_id in selected_ids],
            reason=reason,
            warning=" ".join(warning_parts),
        )

    @staticmethod
    def _extract_json(content: str) -> dict[str, Any]:
        text = content.strip()
        if not text:
            raise ValueError("Empty LLM response.")
        if match := _JSON_BLOCK_RE.search(text):
            text = match.group(1).strip()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM response was not valid JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError("LLM response JSON must be an object.")
        return payload
