"""Local skill catalog primitives and ClawHub search provider."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html import unescape
import io
import json
from pathlib import Path
import re
from time import monotonic
from typing import Any, Protocol
from urllib.parse import quote, urljoin, urlparse
import uuid
import zipfile

import httpx
from loguru import logger

from openhire.security.network import validate_resolved_url, validate_url_target
from openhire.workforce.required_skill import (
    REQUIRED_EMPLOYEE_SKILL_ID,
    load_required_employee_skill_markdown,
    required_employee_skill_record,
    save_required_employee_skill_markdown,
)

_LOCAL_SKILL_FILENAMES = {"skill.md"}
_SKILL_MD_PATH_SUFFIX = "/skill.md"
_DEFAULT_REMOTE_SKILL_TIMEOUT = 10.0
_SOULBANNER_COLLECTIONS = ("soulbanner_skills", "sovereign_skills")
_MBTI_SBTI_COLLECTIONS = ("mbti_skills", "sbti_skills")
_CLAWHUB_ARCHIVE_MAX_BYTES = 10 * 1024 * 1024
_CLAWHUB_ARCHIVE_MAX_ENTRIES = 200
_CLAWHUB_SKILL_MD_MAX_BYTES = 2 * 1024 * 1024
_DOWNLOAD_LINK_RE = re.compile(
    r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>.*?</a>",
    re.IGNORECASE | re.DOTALL,
)
_GITHUB_COMMITTED_DATE_RE = re.compile(r'"committedDate":"([^"]+)"')
_TAG_RE = re.compile(r"<[^>]+>")
_META_STAT_RE = re.compile(
    r'<span class="meta-stat-value">([^<]+)</span>\s*'
    r'<span class="meta-stat-label">([^<]+)</span>',
    re.IGNORECASE,
)
_SKILL_IMPORT_SCENARIOS = [
    {
        "name": "邮箱与消息分诊",
        "queries": ["gmail", "email", "slack", "teams", "notion", "hubspot", "salesforce"],
    },
    {
        "name": "日报周报",
        "queries": ["report", "news", "monitor", "spreadsheet", "browser", "web", "search"],
    },
    {
        "name": "工单分派",
        "queries": ["jira", "linear", "zendesk", "github", "pagerduty", "ticket"],
    },
    {
        "name": "运营巡检",
        "queries": ["browser", "monitor", "spreadsheet", "salesforce", "hubspot", "database", "alert"],
    },
    {
        "name": "行政日程",
        "queries": ["calendar", "meeting", "gmail", "notion", "pdf", "document"],
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class SkillEntry:
    """Persisted local skill metadata."""

    id: str = ""
    source: str = ""
    external_id: str = ""
    name: str = ""
    description: str = ""
    version: str = ""
    author: str = ""
    license: str = ""
    source_url: str = ""
    safety_status: str = ""
    markdown: str = ""
    tags: list[str] = field(default_factory=list)
    imported_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "external_id": self.external_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "license": self.license,
            "source_url": self.source_url,
            "safety_status": self.safety_status,
            "tags": list(self.tags),
            "imported_at": self.imported_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SkillEntry:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


class SkillCatalogStore:
    """Persist local skill metadata to ``workspace/openhire/skills.json``."""

    def __init__(self, workspace: Path) -> None:
        self._dir = workspace / "openhire"
        self._file = self._dir / "skills.json"

    def load(self) -> dict[str, Any]:
        if not self._file.exists():
            return {"skills": {}}
        try:
            return json.loads(self._file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load skill catalog store: {}", exc)
            return {"skills": {}}

    def save(self, data: dict[str, Any]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        tmp = self._file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._file)

    @property
    def preview_file(self) -> Path:
        return self._dir / "skill_import_preview.json"


class SkillCatalogService:
    """Manage persisted local skill metadata."""

    def __init__(self, store: SkillCatalogStore) -> None:
        self._store = store
        self._cache: dict[str, SkillEntry] | None = None

    def _load(self) -> dict[str, SkillEntry]:
        if self._cache is None:
            data = self._store.load()
            self._cache = {
                key: SkillEntry.from_dict(value)
                for key, value in data.get("skills", {}).items()
                if isinstance(value, Mapping)
            }
        return self._cache

    def _save(self) -> None:
        entries = self._load()
        self._store.save({"skills": {key: value.to_dict() for key, value in entries.items()}})

    def list(self) -> list[SkillEntry]:
        entries = self._load()
        system_skill = SkillEntry.from_dict(required_employee_skill_record())
        return [system_skill, *[entry for key, entry in entries.items() if key != system_skill.id]]

    def get_by_ids(self, skill_ids: list[str]) -> list[SkillEntry]:
        entries = self._load()
        result: list[SkillEntry] = []
        for skill_id in skill_ids:
            if skill_id == REQUIRED_EMPLOYEE_SKILL_ID:
                result.append(SkillEntry.from_dict(required_employee_skill_record()))
                continue
            if skill_id in entries:
                result.append(entries[skill_id])
        return result

    def remove(self, skill_id: str) -> bool:
        entries = self._load()
        normalized_id = str(skill_id or "").strip()
        if normalized_id == REQUIRED_EMPLOYEE_SKILL_ID:
            raise RequiredSkillDeleteError("The required employee skill cannot be deleted.")
        if normalized_id not in entries:
            return False
        del entries[normalized_id]
        self._save()
        return True

    def get_content(self, skill_id: str) -> dict[str, Any] | None:
        normalized_id = str(skill_id or "").strip()
        if normalized_id == REQUIRED_EMPLOYEE_SKILL_ID:
            entry = SkillEntry.from_dict(required_employee_skill_record())
            return {
                "skill": entry.to_public_dict(),
                "markdown": load_required_employee_skill_markdown(),
                "editable": True,
                "content_source": "system-file",
                "can_sync_employees": True,
            }

        entry = self._load().get(normalized_id)
        if entry is None:
            return None
        markdown = entry.markdown or self._synthesize_markdown(entry)
        return {
            "skill": entry.to_public_dict(),
            "markdown": markdown,
            "editable": True,
            "content_source": "stored" if entry.markdown else "generated",
            "can_sync_employees": False,
        }

    def update_content(self, skill_id: str, markdown: str) -> dict[str, Any] | None:
        normalized_id = str(skill_id or "").strip()
        if normalized_id == REQUIRED_EMPLOYEE_SKILL_ID:
            save_required_employee_skill_markdown(markdown)
            return self.get_content(normalized_id)

        entries = self._load()
        entry = entries.get(normalized_id)
        if entry is None:
            return None

        frontmatter = _load_skill_frontmatter(markdown)
        entry.name = _frontmatter_text(frontmatter, "name")
        entry.description = _frontmatter_text(frontmatter, "description")
        entry.version = _frontmatter_text(frontmatter, "version") or entry.version
        entry.author = _frontmatter_text(frontmatter, "author") or entry.author
        entry.license = _frontmatter_text(frontmatter, "license")
        entry.markdown = str(markdown)
        entry.imported_at = _now()
        self._save()
        return self.get_content(normalized_id)

    async def generate_clawhub_import_preview(
        self,
        provider: ClawHubSkillProvider,
        *,
        min_count: int = 20,
        max_count: int = 50,
    ) -> dict[str, Any]:
        max_count = max(1, int(max_count))
        min_count = max(1, min(int(min_count), max_count))
        by_key: dict[str, dict[str, Any]] = {}

        for scenario in _SKILL_IMPORT_SCENARIOS:
            scenario_name = str(scenario["name"])
            for query in scenario["queries"]:
                for record in await provider.search(str(query), limit=8):
                    key = self._candidate_key(record)
                    if not key:
                        continue
                    candidate = by_key.get(key)
                    if candidate is None:
                        candidate = {
                            "record": dict(record),
                            "name": record.get("name", ""),
                            "source_url": record.get("source_url", ""),
                            "scenarios": [scenario_name],
                            "queries": [str(query)],
                            "tags": [f"scenario:{scenario_name}", f"query:{query}"],
                        }
                        by_key[key] = candidate
                    else:
                        self._add_candidate_tag(candidate, f"scenario:{scenario_name}")
                        self._add_candidate_tag(candidate, f"query:{query}")
                        candidate.setdefault("scenarios", [])
                        if scenario_name not in candidate["scenarios"]:
                            candidate["scenarios"].append(scenario_name)

        selected = self._select_preview_candidates(list(by_key.values()), max_count=max_count)
        semaphore = asyncio.Semaphore(5)

        async def enrich(item: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                return await self._build_preview_candidate(
                    provider,
                    item["record"],
                    scenario=item["scenarios"][0],
                    query=item["queries"][0],
                    scenarios=item["scenarios"],
                    queries=item["queries"],
                )

        ordered = list(await asyncio.gather(*(enrich(item) for item in selected)))
        preview = {
            "generated_at": _now(),
            "min_count": min_count,
            "max_count": max_count,
            "count": len(ordered),
            "candidates": ordered,
        }
        self._store.preview_file.parent.mkdir(parents=True, exist_ok=True)
        self._store.preview_file.write_text(json.dumps(preview, indent=2, ensure_ascii=False), encoding="utf-8")
        return preview

    async def list_soulbanner_skill_records(
        self,
        provider: SoulBannerSkillProvider,
    ) -> list[dict[str, Any]]:
        return await self._list_github_role_skill_records(
            provider,
            collections=_SOULBANNER_COLLECTIONS,
            source="soulbanner",
            label="SoulBanner",
            error_cls=SoulBannerProviderError,
            empty_message="SoulBanner search returned no usable skills.",
        )

    async def list_mbti_sbti_skill_records(
        self,
        provider: MbtiSbtiSkillProvider,
    ) -> list[dict[str, Any]]:
        return await self._list_github_role_skill_records(
            provider,
            collections=_MBTI_SBTI_COLLECTIONS,
            source="mbti-sbti",
            label="Mbti/Sbti",
            error_cls=MbtiSbtiProviderError,
            empty_message="Mbti/Sbti search returned no usable skills.",
            use_direct_skill_urls=True,
        )

    async def _list_github_role_skill_records(
        self,
        provider: GitHubSkillDirectoryProvider,
        *,
        collections: tuple[str, ...],
        source: str,
        label: str,
        error_cls: type[RuntimeError],
        empty_message: str,
        use_direct_skill_urls: bool = False,
    ) -> list[dict[str, Any]]:
        semaphore = asyncio.Semaphore(5)
        records: list[dict[str, Any]] = []

        async def load_role_record(collection: str, role_entry: Mapping[str, Any]) -> dict[str, Any] | None:
            if str(role_entry.get("type") or "").strip() != "dir":
                return None
            slug = str(role_entry.get("name") or "").strip()
            role_path = str(role_entry.get("path") or "").strip() or f"{collection}/{slug}"
            if not slug or not role_path:
                return None
            download_url = ""
            if use_direct_skill_urls:
                download_url = self._direct_skill_download_url(provider, role_path)
            if not download_url:
                try:
                    async with semaphore:
                        role_entries = await provider.list_directory(role_path)
                except Exception as exc:
                    logger.warning("Skipping {} role {}: failed to list directory: {}", label, role_path, exc)
                    return None
                download_url = self._find_role_skill_download_url(role_entries)
            if not download_url:
                logger.warning("Skipping {} role {}: SKILL.md download_url missing", label, role_path)
                return None

            try:
                async with semaphore:
                    markdown = await provider.fetch_text(download_url)
                updated_at = ""
                try:
                    async with semaphore:
                        updated_at = await provider.fetch_last_modified_at(f"{role_path}/SKILL.md")
                except Exception as exc:
                    logger.warning("Skipping {} role {} modified date: {}", label, role_path, exc)
                normalized = self._normalize_record(
                    {
                        "source": source,
                        "external_id": f"{collection}/{slug}",
                        "name": "",
                        "description": "",
                        "source_url": download_url,
                        "updated_at": updated_at,
                        "markdown": markdown,
                        "tags": [f"collection:{collection}"],
                    }
                )
                normalized = self._apply_markdown_metadata(normalized)
                normalized["tags"] = _normalize_tags([*normalized["tags"], f"collection:{collection}"])
                return normalized
            except Exception as exc:
                logger.warning("Skipping {} role {}: failed to load SKILL.md: {}", label, role_path, exc)
                return None

        for collection in collections:
            try:
                collection_entries = await provider.list_directory(collection)
            except Exception as exc:
                logger.warning("Skipping {} collection {}: {}", label, collection, exc)
                continue
            role_records = await asyncio.gather(
                *(load_role_record(collection, entry) for entry in collection_entries),
            )
            records.extend(record for record in role_records if record)

        if not records:
            raise error_cls(empty_message)
        return records

    @staticmethod
    def _direct_skill_download_url(provider: GitHubSkillDirectoryProvider, role_path: str) -> str:
        skill_file_url = getattr(provider, "skill_file_url", None)
        if not callable(skill_file_url):
            return ""
        return str(skill_file_url(role_path) or "").strip()

    @staticmethod
    def _candidate_key(record: Mapping[str, Any]) -> str:
        return str(record.get("source_url") or record.get("external_id") or "").strip()

    async def _build_preview_candidate(
        self,
        provider: ClawHubSkillProvider,
        record: Mapping[str, Any],
        *,
        scenario: str,
        query: str,
        scenarios: list[str] | None = None,
        queries: list[str] | None = None,
    ) -> dict[str, Any]:
        skill = dict(record)
        source_url = str(skill.get("source_url") or "").strip()
        details: dict[str, Any] = {}
        markdown_status = "unknown"
        markdown_error = ""
        try:
            details = await provider.fetch_package_details(source_url)
        except Exception as exc:
            details = {"risk": "unknown", "error": str(exc)}
        try:
            markdown = await provider.fetch_skill_markdown(source_url)
            _load_skill_frontmatter(markdown)
            markdown_status = "ok"
        except Exception as exc:
            markdown_status = "error"
            markdown_error = str(exc)

        downloads = details.get("downloads")
        stars = details.get("stars")
        risk = str(details.get("risk") or "unknown")
        tags = self._candidate_tags(skill, scenario=scenario, query=query, risk=risk, downloads=downloads, stars=stars)
        for extra_scenario in scenarios or []:
            if extra_scenario != scenario:
                tags.append(f"scenario:{extra_scenario}")
        for extra_query in queries or []:
            if extra_query != query:
                tags.append(f"query:{extra_query}")
        tags = _normalize_tags(tags)
        skill["tags"] = tags
        return {
            "name": skill.get("name", ""),
            "owner": skill.get("author", ""),
            "source_url": source_url,
            "scenario": scenario,
            "scenarios": [scenario],
            "reason": f"Matched query '{query}' for {scenario}.",
            "stars": stars,
            "downloads": downloads,
            "risk": risk,
            "markdown_status": markdown_status,
            "markdown_error": markdown_error,
            "download_url": details.get("download_url", ""),
            "updated_at": skill.get("updated_at", ""),
            "score": skill.get("score", 0),
            "tags": tags,
            "skill": skill,
        }

    def _candidate_tags(
        self,
        skill: Mapping[str, Any],
        *,
        scenario: str,
        query: str,
        risk: str,
        downloads: Any,
        stars: Any,
    ) -> list[str]:
        tags = [
            f"scenario:{scenario}",
            f"query:{query}",
            f"tool:{skill.get('external_id') or skill.get('name') or 'unknown'}",
            f"risk:{risk or 'unknown'}",
        ]
        if isinstance(downloads, int) and downloads >= 1000:
            tags.append("popular:high-downloads")
        elif isinstance(stars, int) and stars >= 10:
            tags.append("popular:high-stars")
        else:
            tags.append("popularity:unknown")
        return _normalize_tags(tags)

    @staticmethod
    def _add_candidate_tag(candidate: dict[str, Any], tag: str) -> None:
        tags = candidate.setdefault("tags", [])
        if tag not in tags:
            tags.append(tag)
        skill = candidate.setdefault("skill", {})
        skill_tags = skill.setdefault("tags", [])
        if tag not in skill_tags:
            skill_tags.append(tag)

    def _select_preview_candidates(self, candidates: list[dict[str, Any]], *, max_count: int) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        selected_keys: set[str] = set()
        for scenario in _SKILL_IMPORT_SCENARIOS:
            scenario_name = str(scenario["name"])
            scenario_items = [
                item for item in candidates
                if f"scenario:{scenario_name}" in item.get("tags", [])
            ]
            for item in sorted(scenario_items, key=self._candidate_sort_key):
                key = str(item.get("source_url") or item.get("name") or "")
                if key in selected_keys:
                    continue
                selected.append(item)
                selected_keys.add(key)
                break

        for item in sorted(candidates, key=self._candidate_sort_key):
            if len(selected) >= max_count:
                break
            key = str(item.get("source_url") or item.get("name") or "")
            if key in selected_keys:
                continue
            selected.append(item)
            selected_keys.add(key)
        return selected[:max_count]

    @staticmethod
    def _candidate_sort_key(item: Mapping[str, Any]) -> tuple[int, int, int, str]:
        downloads = item.get("downloads") if isinstance(item.get("downloads"), int) else 0
        stars = item.get("stars") if isinstance(item.get("stars"), int) else 0
        score = item.get("score") if isinstance(item.get("score"), int) else 0
        return (-downloads, -stars, -score, str(item.get("name") or ""))

    @staticmethod
    def _find_role_skill_download_url(entries: list[Mapping[str, Any]]) -> str:
        for entry in entries:
            if str(entry.get("type") or "").strip() != "file":
                continue
            if str(entry.get("name") or "").strip().lower() != "skill.md":
                continue
            return str(entry.get("download_url") or "").strip()
        return ""

    def preview_local_skill(self, filename: str, content: bytes) -> dict[str, str]:
        normalized_filename = str(filename or "").strip()
        if normalized_filename.lower() not in _LOCAL_SKILL_FILENAMES:
            raise LocalSkillImportError("Uploaded file must be named SKILL.md or skill.md.")

        try:
            markdown = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise LocalSkillImportError("Uploaded SKILL.md must be valid UTF-8.") from exc

        try:
            return self._preview_skill_markdown(markdown, source="local")
        except SkillPreviewParseError as exc:
            raise LocalSkillImportError(str(exc)) from exc

    async def preview_web_skill(self, url: str, *, max_bytes: int) -> dict[str, str]:
        normalized_url = self._validate_web_skill_url(url)
        try:
            async with httpx.AsyncClient(
                timeout=_DEFAULT_REMOTE_SKILL_TIMEOUT,
                follow_redirects=True,
            ) as client:
                response = await client.get(normalized_url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise WebSkillImportError(str(exc)) from exc

        resolved_ok, resolved_error = validate_resolved_url(str(response.url))
        if not resolved_ok:
            raise WebSkillImportError(resolved_error)

        if len(response.content) > max(0, int(max_bytes)):
            raise WebSkillImportError(
                f"Remote SKILL.md exceeds {max_bytes // (1024 * 1024)}MB limit."
            )
        try:
            markdown = response.content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise WebSkillImportError("Fetched SKILL.md must be valid UTF-8.") from exc

        try:
            return self._preview_skill_markdown(
                markdown,
                source="web",
                source_url=normalized_url,
            )
        except SkillPreviewParseError as exc:
            raise WebSkillImportError(str(exc)) from exc

    def upsert_many(self, records: list[Mapping[str, Any]]) -> list[SkillEntry]:
        entries = self._load()
        by_identity = {
            self._identity_key(entry.source, entry.external_id, entry.source_url): entry
            for entry in entries.values()
        }
        upserted: list[SkillEntry] = []
        seen_input: set[tuple[str, str]] = set()

        for record in records:
            normalized = self._normalize_record(record)
            if normalized["markdown"]:
                normalized = self._apply_markdown_metadata(normalized)
            identity = self._identity_key(
                normalized["source"],
                normalized["external_id"],
                normalized["source_url"],
            )
            if identity in seen_input:
                continue
            seen_input.add(identity)

            requested_id = normalized["id"]
            existing = entries.get(requested_id) if requested_id else None
            if existing is None:
                existing = by_identity.get(identity)
            if existing is None:
                skill_id = requested_id or str(uuid.uuid4())[:8]
                while skill_id in entries:
                    skill_id = str(uuid.uuid4())[:8]
                existing = SkillEntry(id=skill_id)
                entries[existing.id] = existing

            existing.source = normalized["source"]
            existing.external_id = normalized["external_id"]
            existing.name = normalized["name"]
            existing.description = normalized["description"]
            existing.version = normalized["version"]
            existing.author = normalized["author"]
            existing.license = normalized["license"]
            existing.source_url = normalized["source_url"]
            existing.safety_status = normalized["safety_status"]
            existing.markdown = normalized["markdown"]
            existing.tags = normalized["tags"]
            existing.imported_at = _now()
            by_identity[identity] = existing
            upserted.append(existing)

        self._save()
        return upserted

    @staticmethod
    def _identity_key(source: str, external_id: str, source_url: str) -> tuple[str, str]:
        if source == "web":
            return source, source_url or external_id
        return source, external_id or source_url

    @staticmethod
    def _normalize_record(record: Mapping[str, Any]) -> dict[str, Any]:
        def text(value: Any) -> str:
            return str(value or "").strip()

        return {
            "id": text(record.get("id")),
            "source": text(record.get("source")),
            "external_id": text(record.get("external_id")),
            "name": text(record.get("name")),
            "description": text(record.get("description")),
            "version": text(record.get("version")),
            "author": text(record.get("author")),
            "license": text(record.get("license")),
            "source_url": text(record.get("source_url")),
            "updated_at": text(record.get("updated_at")),
            "safety_status": text(record.get("safety_status")),
            "markdown": str(record.get("markdown") or ""),
            "tags": _normalize_tags(record.get("tags")),
        }

    def _apply_markdown_metadata(self, normalized: dict[str, Any]) -> dict[str, Any]:
        frontmatter = _load_skill_frontmatter(normalized["markdown"])
        updated = dict(normalized)
        updated["name"] = updated["name"] or _frontmatter_text(frontmatter, "name")
        updated["description"] = _frontmatter_text(frontmatter, "description")
        updated["license"] = _frontmatter_text(frontmatter, "license") or updated["license"]
        updated["version"] = _frontmatter_text(frontmatter, "version") or updated["version"]
        updated["author"] = _frontmatter_text(frontmatter, "author") or updated["author"]
        return updated

    def _preview_skill_markdown(
        self,
        markdown: str,
        *,
        source: str,
        source_url: str = "",
    ) -> dict[str, Any]:
        frontmatter = _load_skill_frontmatter(markdown)
        name = _frontmatter_text(frontmatter, "name")
        return self._normalize_record(
            {
                "source": source,
                "external_id": name,
                "name": name,
                "description": _frontmatter_text(frontmatter, "description"),
                "version": "",
                "author": "",
                "license": _frontmatter_text(frontmatter, "license"),
                "source_url": source_url if source == "web" else _frontmatter_text(frontmatter, "homepage"),
                "safety_status": "",
                "markdown": markdown,
                "tags": [],
            }
        )

    @staticmethod
    def _frontmatter_block_value(value: str) -> str:
        lines = str(value or "").splitlines() or [""]
        return ">\n" + "\n".join(f"  {line}" for line in lines)

    def _synthesize_markdown(self, entry: SkillEntry) -> str:
        name = entry.name or entry.external_id or entry.id or "skill"
        description = entry.description or "No description available."
        frontmatter = [
            "---",
            f"name: {name}",
            f"description: {self._frontmatter_block_value(description)}",
        ]
        if entry.source_url:
            frontmatter.append(f"homepage: {entry.source_url}")
        if entry.version:
            frontmatter.append(f"version: {entry.version}")
        if entry.author:
            frontmatter.append(f"author: {entry.author}")
        if entry.license:
            frontmatter.append(f"license: {entry.license}")
        frontmatter.append("---")
        return "\n".join(frontmatter) + f"\n\n# {name}\n\n{description}\n"

    @staticmethod
    def _validate_web_skill_url(url: str) -> str:
        normalized_url = str(url or "").strip()
        parsed = urlparse(normalized_url)
        if parsed.scheme not in {"http", "https"}:
            raise WebSkillUrlError(f"Only http/https allowed, got '{parsed.scheme or 'none'}'")
        if not parsed.netloc:
            raise WebSkillUrlError("Missing domain")
        if not parsed.path.lower().endswith(_SKILL_MD_PATH_SUFFIX):
            raise WebSkillUrlError("Web skill URL must point directly to SKILL.md or skill.md.")
        is_valid_target, validation_error = validate_url_target(normalized_url)
        if not is_valid_target:
            raise WebSkillUrlError(validation_error)
        return normalized_url


class LocalSkillImportError(ValueError):
    """Raised when an uploaded local SKILL.md cannot be normalized."""


class RequiredSkillDeleteError(ValueError):
    """Raised when a caller tries to remove a required system skill."""


class WebSkillUrlError(ValueError):
    """Raised when a remote SKILL.md URL is invalid or unsafe."""


class WebSkillImportError(RuntimeError):
    """Raised when a remote SKILL.md cannot be fetched or parsed."""


class SkillPreviewParseError(ValueError):
    """Raised when SKILL.md frontmatter cannot be parsed into a preview record."""


def _extract_frontmatter(content: str) -> str | None:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[1:index])
    return None


def ensure_skill_frontmatter(markdown: str, metadata: Mapping[str, Any]) -> str:
    """Prepend a synthesized YAML frontmatter block when the SKILL.md is missing one.

    Used when importing packaged skills whose SKILL.md only contains body markdown.
    The provided ``metadata`` mapping is trusted as the source of truth for the
    frontmatter fields (``name`` and ``description`` are required; the rest are optional).
    """

    body = markdown or ""
    if _extract_frontmatter(body) is not None:
        return body

    def _text(key: str) -> str:
        return str(metadata.get(key) or "").strip()

    name = _text("name") or _text("external_id") or "skill"
    description = _text("description") or "No description available."
    lines = [
        "---",
        f"name: {name}",
        "description: >",
    ]
    for description_line in description.splitlines() or [""]:
        lines.append(f"  {description_line}")
    for key in ("homepage", "source_url"):
        value = _text(key)
        if value:
            lines.append(f"homepage: {value}")
            break
    for key in ("version", "author", "license"):
        value = _text(key)
        if value:
            lines.append(f"{key}: {value}")
    lines.append("---")
    prefix = "\n".join(lines)
    separator = "\n\n" if body.strip() else "\n"
    return f"{prefix}{separator}{body}" if body else f"{prefix}\n"


def _parse_simple_frontmatter(frontmatter_text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    current_key: str | None = None
    multiline_mode: str | None = None
    for line in frontmatter_text.splitlines():
        if multiline_mode and line[:1].isspace():
            stripped = line.strip()
            if multiline_mode == ">":
                if stripped:
                    parsed[current_key] = (
                        f"{parsed[current_key]} {stripped}".strip()
                        if parsed[current_key]
                        else stripped
                    )
                elif parsed[current_key]:
                    parsed[current_key] = f"{parsed[current_key]}\n"
            else:
                parsed[current_key] = (
                    f"{parsed[current_key]}\n{stripped}" if parsed[current_key] else stripped
                )
            continue

        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line[:1].isspace():
            continue
        if ":" not in stripped:
            raise SkillPreviewParseError("Unsupported YAML syntax in SKILL.md frontmatter.")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise SkillPreviewParseError("Unsupported YAML syntax in SKILL.md frontmatter.")
        if value in {"|", ">"}:
            parsed[key] = ""
            current_key = key
            multiline_mode = value
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        parsed[key] = value
        current_key = key
        multiline_mode = None
    return parsed


def _load_skill_frontmatter(markdown: str) -> dict[str, str]:
    frontmatter_text = _extract_frontmatter(markdown)
    if frontmatter_text is None:
        raise SkillPreviewParseError("Invalid frontmatter format in SKILL.md.")
    frontmatter = _parse_simple_frontmatter(frontmatter_text)
    if not _frontmatter_text(frontmatter, "name"):
        raise SkillPreviewParseError("Missing 'name' in SKILL.md frontmatter.")
    if not _frontmatter_text(frontmatter, "description"):
        raise SkillPreviewParseError("Missing 'description' in SKILL.md frontmatter.")
    return frontmatter


def _frontmatter_text(frontmatter: Mapping[str, Any], key: str) -> str:
    value = frontmatter.get(key)
    return str(value or "").strip()


def _normalize_tags(value: Any) -> list[str]:
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item or "").strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


class ClawHubProviderError(RuntimeError):
    """Raised when the upstream ClawHub search request fails."""


class SoulBannerProviderError(RuntimeError):
    """Raised when the SoulBanner upstream request fails."""


class MbtiSbtiProviderError(RuntimeError):
    """Raised when the Mbti/Sbti upstream request fails."""


class ClawHubSkillProvider(Protocol):
    """Remote skill metadata provider."""

    async def search(self, query: str, *, limit: int = 10) -> list[dict[str, str]]:
        """Search remote skills and return normalized metadata."""

    async def fetch_skill_markdown(self, source_url: str) -> str:
        """Fetch a complete SKILL.md from a ClawHub package page."""

    async def fetch_package_details(self, source_url: str) -> dict[str, Any]:
        """Fetch ClawHub package details such as downloads, stars, risk, and download URL."""


class GitHubSkillDirectoryProvider(Protocol):
    """Remote GitHub skill source provider backed by directory listings."""

    async def list_directory(self, path: str) -> list[dict[str, Any]]:
        """List repo directory entries for a given path."""

    async def fetch_text(self, url: str) -> str:
        """Fetch a UTF-8 text file such as a raw SKILL.md."""

    async def fetch_last_modified_at(self, path: str) -> str:
        """Fetch the latest commit timestamp for a repo file path."""


class SoulBannerSkillProvider(GitHubSkillDirectoryProvider, Protocol):
    """Remote SoulBanner skill source provider."""


class MbtiSbtiSkillProvider(GitHubSkillDirectoryProvider, Protocol):
    """Remote Mbti/Sbti skill source provider."""

    def skill_file_url(self, path: str) -> str:
        """Return the raw SKILL.md URL for a role directory path."""


class HttpClawHubSkillProvider:
    """HTTP implementation backed by the public ClawHub package search API."""

    def __init__(
        self,
        base_url: str = "https://clawhub.ai",
        *,
        timeout: float = 10.0,
        max_attempts: int = 3,
        initial_retry_delay: float = 0.4,
        max_retry_delay: float = 2.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = max(0.1, float(timeout))
        self._max_attempts = max(1, int(max_attempts))
        self._initial_retry_delay = max(0.1, float(initial_retry_delay))
        self._max_retry_delay = max(self._initial_retry_delay, float(max_retry_delay))

    async def search(self, query: str, *, limit: int = 10) -> list[dict[str, str]]:
        url = f"{self._base_url}/api/v1/packages/search"
        params = {
            "family": "skill",
            "q": query,
            "limit": limit,
        }
        last_error: httpx.HTTPError | None = None
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for attempt in range(1, self._max_attempts + 1):
                try:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    break
                except httpx.HTTPError as exc:
                    last_error = exc
                    if not self._is_retryable_error(exc) or attempt >= self._max_attempts:
                        raise ClawHubProviderError(self._format_provider_error(exc, attempt)) from exc
                    delay = self._retry_delay_for(exc, attempt)
                    logger.warning(
                        "ClawHub search failed (attempt {}/{} for {!r}): {}. Retrying in {}s",
                        attempt,
                        self._max_attempts,
                        query,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)
            else:
                if last_error is not None:
                    raise ClawHubProviderError(
                        self._format_provider_error(last_error, self._max_attempts)
                    ) from last_error
                raise ClawHubProviderError("ClawHub search failed without an upstream response.")

        payload = response.json()
        results = payload.get("results", []) if isinstance(payload, Mapping) else []
        return [
            self._normalize_search_result(item.get("package", {}))
            for item in results
            if isinstance(item, Mapping)
        ]

    async def fetch_skill_markdown(self, source_url: str) -> str:
        details = await self.fetch_package_details(source_url)
        download_url = str(details.get("download_url") or "").strip()
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
            ) as client:
                download_response = await client.get(download_url)
                download_response.raise_for_status()
                self._validate_resolved_remote_url(str(download_response.url))
        except httpx.HTTPError as exc:
            raise ClawHubProviderError(str(exc)) from exc

        if len(download_response.content) > _CLAWHUB_ARCHIVE_MAX_BYTES:
            raise ClawHubProviderError("ClawHub archive exceeds the download size limit.")

        # ClawHub packages are not required to ship YAML frontmatter; callers
        # that need structured metadata should synthesize it from their own
        # context (e.g. case records) before persisting the skill.
        return self._skill_markdown_from_archive(download_response.content)

    async def fetch_package_details(self, source_url: str) -> dict[str, Any]:
        detail_url = self._validate_remote_url(source_url)
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
            ) as client:
                detail_response = await client.get(detail_url)
                detail_response.raise_for_status()
                self._validate_resolved_remote_url(str(detail_response.url))
        except httpx.HTTPError as exc:
            raise ClawHubProviderError(str(exc)) from exc
        return self._extract_package_details(detail_response.text, base_url=str(detail_response.url))

    def _extract_package_details(self, html: str, *, base_url: str) -> dict[str, Any]:
        stats: dict[str, int] = {}
        for value, label in _META_STAT_RE.findall(html):
            normalized_label = unescape(label).strip().casefold()
            parsed_value = self._parse_compact_number(unescape(value).strip())
            if "download" in normalized_label:
                stats["downloads"] = parsed_value
            elif "star" in normalized_label:
                stats["stars"] = parsed_value
        risk = "suspicious" if (
            "skill flagged" in html.casefold()
            or ">suspicious<" in html.casefold()
            or "suspicious patterns detected" in html.casefold()
        ) else "unknown"
        return {
            "downloads": stats.get("downloads"),
            "stars": stats.get("stars"),
            "risk": risk,
            "download_url": self._extract_download_url(html, base_url=base_url),
        }

    @staticmethod
    def _parse_compact_number(value: str) -> int:
        text = value.strip().lower().replace(",", "")
        multiplier = 1
        if text.endswith("k"):
            multiplier = 1_000
            text = text[:-1]
        elif text.endswith("m"):
            multiplier = 1_000_000
            text = text[:-1]
        try:
            return int(float(text) * multiplier)
        except ValueError:
            return 0

    def _extract_download_url(self, html: str, *, base_url: str) -> str:
        for match in _DOWNLOAD_LINK_RE.finditer(html):
            if "download" not in match.group(0).casefold():
                continue
            download_url = urljoin(base_url, unescape(match.group(1)))
            return self._validate_remote_url(download_url)
        raise ClawHubProviderError("ClawHub package page did not contain a Download link.")

    def _skill_markdown_from_archive(self, archive_bytes: bytes) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
                entries = archive.infolist()
                if len(entries) > _CLAWHUB_ARCHIVE_MAX_ENTRIES:
                    raise ClawHubProviderError("ClawHub archive exceeded the entry limit.")
                skill_info = self._find_skill_md_entry(entries)
                if skill_info is None:
                    raise ClawHubProviderError("ClawHub archive did not contain SKILL.md.")
                if skill_info.file_size > _CLAWHUB_SKILL_MD_MAX_BYTES:
                    raise ClawHubProviderError("ClawHub SKILL.md exceeds the file size limit.")
                data = archive.read(skill_info)
        except ClawHubProviderError:
            raise
        except (zipfile.BadZipFile, OSError) as exc:
            raise ClawHubProviderError("ClawHub archive could not be read as a ZIP archive.") from exc
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ClawHubProviderError("ClawHub SKILL.md must be valid UTF-8.") from exc

    @staticmethod
    def _find_skill_md_entry(entries: list[zipfile.ZipInfo]) -> zipfile.ZipInfo | None:
        exact = next((entry for entry in entries if entry.filename.lower() == "skill.md"), None)
        if exact is not None:
            return exact
        return next(
            (
                entry
                for entry in entries
                if not entry.is_dir() and Path(entry.filename).name.lower() == "skill.md"
            ),
            None,
        )

    @staticmethod
    def _validate_remote_url(url: str) -> str:
        normalized = str(url or "").strip()
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"}:
            raise ClawHubProviderError(f"Only http/https allowed, got '{parsed.scheme or 'none'}'")
        if not parsed.netloc:
            raise ClawHubProviderError("Missing domain")
        is_valid, error = validate_url_target(normalized)
        if not is_valid:
            raise ClawHubProviderError(error)
        return normalized

    @staticmethod
    def _validate_resolved_remote_url(url: str) -> None:
        is_valid, error = validate_resolved_url(url)
        if not is_valid:
            raise ClawHubProviderError(error)

    def _is_retryable_error(self, exc: httpx.HTTPError) -> bool:
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            return status == 429 or status >= 500
        return isinstance(exc, httpx.RequestError)

    def _retry_delay_for(self, exc: httpx.HTTPError, attempt: int) -> float:
        if isinstance(exc, httpx.HTTPStatusError):
            retry_after = self._retry_after_seconds(exc.response.headers)
            if retry_after is not None:
                return min(self._max_retry_delay, max(self._initial_retry_delay, retry_after))
        return min(self._max_retry_delay, self._initial_retry_delay * (2 ** (attempt - 1)))

    def _format_provider_error(self, exc: httpx.HTTPError, attempt: int) -> str:
        if attempt <= 1:
            return str(exc)
        return f"ClawHub search failed after {attempt} attempts: {exc}"

    @staticmethod
    def _retry_after_seconds(headers: Mapping[str, Any] | None) -> float | None:
        if not headers:
            return None
        raw = headers.get("retry-after")
        if raw is None:
            return None
        text = str(raw).strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def _normalize_search_result(self, package: Mapping[str, Any]) -> dict[str, str]:
        external_id = self._text(package.get("name"))
        owner_handle = self._text(package.get("ownerHandle"))
        return {
            "source": "clawhub",
            "external_id": external_id,
            "name": self._text(package.get("displayName")) or external_id,
            "description": self._text(package.get("summary")),
            "version": self._text(package.get("latestVersion")),
            "author": owner_handle,
            "license": "",
            "source_url": f"{self._base_url}/{owner_handle}/{external_id}",
            "safety_status": self._text(package.get("verificationTier")),
        }

    @staticmethod
    def _text(value: Any) -> str:
        return str(value or "").strip()


class HttpSoulBannerSkillProvider:
    """HTTP implementation backed by a GitHub repository with skill directories."""

    def __init__(
        self,
        *,
        owner: str = "pzy2000",
        repo: str = "SoulBanner",
        branch: str = "main",
        api_base_url: str = "https://api.github.com",
        timeout: float = _DEFAULT_REMOTE_SKILL_TIMEOUT,
        label: str = "SoulBanner",
        error_cls: type[RuntimeError] = SoulBannerProviderError,
        max_attempts: int = 3,
        initial_retry_delay: float = 0.4,
        max_retry_delay: float = 2.0,
        last_modified_ttl_seconds: float = 600.0,
    ) -> None:
        self._owner = owner
        self._repo = repo
        self._branch = branch
        self._api_base_url = api_base_url.rstrip("/")
        self._timeout = max(0.1, float(timeout))
        self._label = label
        self._error_cls = error_cls
        self._max_attempts = max(1, int(max_attempts))
        self._initial_retry_delay = max(0.1, float(initial_retry_delay))
        self._max_retry_delay = max(self._initial_retry_delay, float(max_retry_delay))
        self._last_modified_ttl_seconds = max(1.0, float(last_modified_ttl_seconds))
        self._last_modified_cache: dict[str, tuple[float, str]] = {}

    async def list_directory(self, path: str) -> list[dict[str, Any]]:
        normalized_path = str(path or "").strip().strip("/")
        if not normalized_path:
            raise self._provider_error(f"{self._label} path is required.")
        url = self._validate_remote_url(
            f"{self._api_base_url}/repos/{self._owner}/{self._repo}/contents/{normalized_path}"
        )
        try:
            response = await self._get_with_retries(url, params={"ref": self._branch})
            payload = response.json()
            if not isinstance(payload, list):
                raise self._provider_error(f"{self._label} contents response must be an array.")
            return [item for item in payload if isinstance(item, Mapping)]
        except RuntimeError as exc:
            logger.warning(
                "{} contents API lookup failed for {}: {}. Falling back to tree page.",
                self._label,
                normalized_path,
                exc,
            )
            return await self._fetch_directory_via_tree_page(normalized_path)

    async def fetch_text(self, url: str) -> str:
        normalized_url = self._validate_remote_url(url)
        response = await self._get_with_retries(normalized_url)
        try:
            return response.content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise self._provider_error(f"{self._label} SKILL.md must be valid UTF-8.") from exc

    def skill_file_url(self, path: str) -> str:
        normalized_path = str(path or "").strip().strip("/")
        if not normalized_path:
            return ""
        raw_branch = quote(self._branch, safe="")
        raw_path = quote(f"{normalized_path}/SKILL.md", safe="/")
        return self._validate_remote_url(
            f"https://raw.githubusercontent.com/{self._owner}/{self._repo}/{raw_branch}/{raw_path}"
        )

    async def _fetch_directory_via_tree_page(self, normalized_path: str) -> list[dict[str, Any]]:
        quoted_path = quote(normalized_path, safe="/")
        page_url = self._validate_remote_url(
            f"https://github.com/{self._owner}/{self._repo}/tree/{quote(self._branch, safe='')}/{quoted_path}"
        )
        response = await self._get_with_retries(page_url)
        page = response.text
        marker = '"items":'
        start = page.find(marker)
        if start < 0:
            raise self._provider_error(f"{self._label} tree page missing items payload for {normalized_path}.")
        decoder = json.JSONDecoder()
        try:
            items, _ = decoder.raw_decode(page[start + len(marker):])
        except json.JSONDecodeError as exc:
            raise self._provider_error(f"{self._label} tree page items payload is invalid for {normalized_path}.") from exc
        if not isinstance(items, list):
            raise self._provider_error(f"{self._label} tree page items payload must be an array.")
        normalized_items: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, Mapping):
                continue
            item_path = self._text(item.get("path"))
            content_type = self._text(item.get("contentType"))
            name = self._text(item.get("name")) or Path(item_path).name
            entry_type = "dir" if content_type == "directory" else "file" if content_type == "file" else ""
            if not entry_type or not name or not item_path:
                continue
            normalized_items.append(
                {
                    "type": entry_type,
                    "name": name,
                    "path": item_path,
                    "download_url": (
                        self.skill_file_url(item_path[:-len("/SKILL.md")])
                        if entry_type == "file" and item_path.endswith("/SKILL.md")
                        else ""
                    ),
                }
            )
        return normalized_items

    async def fetch_last_modified_at(self, path: str) -> str:
        normalized_path = str(path or "").strip().strip("/")
        if not normalized_path:
            raise self._provider_error(f"{self._label} path is required.")
        cache_key = f"{self._owner}/{self._repo}/{self._branch}/{normalized_path}"
        cached = self._last_modified_cache.get(cache_key)
        now = monotonic()
        if cached and (now - cached[0]) < self._last_modified_ttl_seconds:
            return cached[1]
        try:
            modified_at = await self._fetch_last_modified_at_via_api(normalized_path)
        except RuntimeError as exc:
            logger.warning(
                "{} commit API lookup failed for {}: {}. Falling back to commit page.",
                self._label,
                normalized_path,
                exc,
            )
            modified_at = await self._fetch_last_modified_at_via_commit_page(normalized_path)
        self._last_modified_cache[cache_key] = (now, modified_at)
        return modified_at

    async def _fetch_last_modified_at_via_api(self, normalized_path: str) -> str:
        url = self._validate_remote_url(f"{self._api_base_url}/repos/{self._owner}/{self._repo}/commits")
        response = await self._get_with_retries(
            url,
            params={
                "sha": self._branch,
                "path": normalized_path,
                "per_page": 1,
            },
        )
        payload = response.json()
        if not isinstance(payload, list) or not payload:
            raise self._provider_error(f"{self._label} commit response missing entries for {normalized_path}.")
        first = payload[0]
        if not isinstance(first, Mapping):
            raise self._provider_error(f"{self._label} commit response must contain objects.")
        commit = first.get("commit")
        if not isinstance(commit, Mapping):
            raise self._provider_error(f"{self._label} commit payload missing commit object.")
        committer = commit.get("committer")
        author = commit.get("author")
        modified_at = ""
        if isinstance(committer, Mapping):
            modified_at = self._text(committer.get("date"))
        if not modified_at and isinstance(author, Mapping):
            modified_at = self._text(author.get("date"))
        if not modified_at:
            raise self._provider_error(f"{self._label} commit payload missing author date for {normalized_path}.")
        return modified_at

    async def _fetch_last_modified_at_via_commit_page(self, normalized_path: str) -> str:
        quoted_path = quote(normalized_path, safe="/")
        page_url = self._validate_remote_url(
            f"https://github.com/{self._owner}/{self._repo}/commits/{quote(self._branch, safe='')}/{quoted_path}"
        )
        response = await self._get_with_retries(page_url)
        page = response.text
        match = _GITHUB_COMMITTED_DATE_RE.search(page)
        if not match:
            raise self._provider_error(f"{self._label} commit page missing committedDate for {normalized_path}.")
        modified_at = self._text(match.group(1))
        if not modified_at:
            raise self._provider_error(f"{self._label} commit page returned empty committedDate for {normalized_path}.")
        return modified_at

    async def _get_with_retries(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> httpx.Response:
        last_error: httpx.HTTPError | None = None
        async with httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=True,
        ) as client:
            for attempt in range(1, self._max_attempts + 1):
                try:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    self._validate_resolved_remote_url(str(response.url))
                    return response
                except httpx.HTTPError as exc:
                    last_error = exc
                    if not self._is_retryable_error(exc) or attempt >= self._max_attempts:
                        raise self._provider_error(self._format_http_error(exc, attempt)) from exc
                    delay = self._retry_delay_for(attempt)
                    logger.warning(
                        "{} request failed (attempt {}/{}): {}. Retrying in {}s",
                        self._label,
                        attempt,
                        self._max_attempts,
                        self._http_error_text(exc),
                        delay,
                    )
                    await asyncio.sleep(delay)
        if last_error is not None:
            raise self._provider_error(self._format_http_error(last_error, self._max_attempts)) from last_error
        raise self._provider_error(f"{self._label} request failed without an upstream response.")

    def _validate_remote_url(self, url: str) -> str:
        normalized = str(url or "").strip()
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"}:
            raise self._provider_error(f"Only http/https allowed, got '{parsed.scheme or 'none'}'")
        if not parsed.netloc:
            raise self._provider_error("Missing domain")
        is_valid, error = validate_url_target(normalized)
        if not is_valid:
            raise self._provider_error(error)
        return normalized

    def _validate_resolved_remote_url(self, url: str) -> None:
        is_valid, error = validate_resolved_url(url)
        if not is_valid:
            raise self._provider_error(error)

    def _provider_error(self, message: str) -> RuntimeError:
        return self._error_cls(message)

    @staticmethod
    def _text(value: Any) -> str:
        return str(value or "").strip()

    @staticmethod
    def _is_retryable_error(exc: httpx.HTTPError) -> bool:
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            return status == 429 or status >= 500
        return isinstance(exc, httpx.RequestError)

    def _retry_delay_for(self, attempt: int) -> float:
        return min(self._max_retry_delay, self._initial_retry_delay * (2 ** (attempt - 1)))

    def _format_http_error(self, exc: httpx.HTTPError, attempt: int) -> str:
        text = self._http_error_text(exc)
        if attempt <= 1:
            return text
        return f"{self._label} request failed after {attempt} attempts: {text}"

    @staticmethod
    def _http_error_text(exc: httpx.HTTPError) -> str:
        text = str(exc).strip()
        return text or exc.__class__.__name__


class HttpMbtiSbtiSkillProvider(HttpSoulBannerSkillProvider):
    """HTTP implementation backed by the Sbti-Mbti GitHub repository."""

    def __init__(
        self,
        *,
        owner: str = "pzy2000",
        repo: str = "Sbti-Mbti",
        branch: str = "main",
        api_base_url: str = "https://api.github.com",
        timeout: float = _DEFAULT_REMOTE_SKILL_TIMEOUT,
    ) -> None:
        super().__init__(
            owner=owner,
            repo=repo,
            branch=branch,
            api_base_url=api_base_url,
            timeout=timeout,
            label="Mbti/Sbti",
            error_cls=MbtiSbtiProviderError,
        )
