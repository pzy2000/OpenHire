from __future__ import annotations

import asyncio
import io
import zipfile
import httpx
import pytest

from openhire.skill_catalog import ClawHubProviderError, HttpClawHubSkillProvider


def _response(payload: dict, *, status_code: int = 200, headers: dict[str, str] | None = None) -> httpx.Response:
    response = httpx.Response(status_code, json=payload, headers=headers)
    response._request = httpx.Request("GET", "https://clawhub.ai/api/v1/packages/search")
    return response


def _text_response(
    text: str,
    *,
    url: str,
    status_code: int = 200,
    content_type: str = "text/html",
) -> httpx.Response:
    return httpx.Response(
        status_code,
        text=text,
        headers={"content-type": content_type},
        request=httpx.Request("GET", url),
    )


def _zip_response(files: dict[str, bytes | str], *, url: str) -> httpx.Response:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            data = content.encode("utf-8") if isinstance(content, str) else content
            archive.writestr(name, data)
    return httpx.Response(
        200,
        content=buffer.getvalue(),
        headers={"content-type": "application/zip"},
        request=httpx.Request("GET", url),
    )


@pytest.mark.asyncio
async def test_clawhub_provider_maps_search_results(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(self, url: str, params: dict[str, object] | None = None):
        assert url == "https://clawhub.ai/api/v1/packages/search"
        assert params == {"family": "skill", "q": "github", "limit": 10}
        return _response(
            {
                "results": [
                    {
                        "package": {
                            "name": "github",
                            "displayName": "Github",
                            "summary": "Use the gh CLI.",
                            "latestVersion": "1.0.0",
                            "ownerHandle": "steipete",
                            "verificationTier": "available",
                        },
                        "score": 370,
                    }
                ]
            }
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    provider = HttpClawHubSkillProvider()
    results = await provider.search("github")

    assert results == [
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
        }
    ]


@pytest.mark.asyncio
async def test_clawhub_provider_uses_fallbacks_for_missing_optional_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(self, url: str, params: dict[str, object] | None = None):
        return _response(
            {
                "results": [
                    {
                        "package": {
                            "name": "nano-gpt-cli",
                            "displayName": "",
                            "summary": None,
                            "latestVersion": None,
                            "ownerHandle": None,
                            "verificationTier": None,
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    provider = HttpClawHubSkillProvider()
    results = await provider.search("nano")

    assert results == [
        {
            "source": "clawhub",
            "external_id": "nano-gpt-cli",
            "name": "nano-gpt-cli",
            "description": "",
            "version": "",
            "author": "",
            "license": "",
            "source_url": "https://clawhub.ai//nano-gpt-cli",
            "safety_status": "",
        }
    ]


@pytest.mark.asyncio
async def test_clawhub_provider_retries_retryable_502_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = {"count": 0}
    sleeps: list[float] = []

    async def fake_get(self, url: str, params: dict[str, object] | None = None):
        attempts["count"] += 1
        if attempts["count"] == 1:
            response = _response({"error": "bad gateway"}, status_code=502)
            raise httpx.HTTPStatusError("502 Bad Gateway", request=response.request, response=response)
        return _response(
            {
                "results": [
                    {
                        "package": {
                            "name": "github",
                            "displayName": "Github",
                            "summary": "Use the gh CLI.",
                            "latestVersion": "1.0.0",
                            "ownerHandle": "steipete",
                            "verificationTier": "available",
                        }
                    }
                ]
            }
        )

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    provider = HttpClawHubSkillProvider()
    results = await provider.search("github")

    assert attempts["count"] == 2
    assert sleeps == [0.4]
    assert results[0]["name"] == "Github"


@pytest.mark.asyncio
async def test_clawhub_provider_does_not_retry_non_retryable_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = {"count": 0}

    async def fake_get(self, url: str, params: dict[str, object] | None = None):
        attempts["count"] += 1
        response = _response({"error": "not found"}, status_code=404)
        raise httpx.HTTPStatusError("404 Not Found", request=response.request, response=response)

    async def fail_sleep(delay: float) -> None:
        raise AssertionError(f"unexpected retry sleep: {delay}")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    monkeypatch.setattr(asyncio, "sleep", fail_sleep)

    provider = HttpClawHubSkillProvider()
    with pytest.raises(ClawHubProviderError, match="404 Not Found"):
        await provider.search("github")

    assert attempts["count"] == 1


@pytest.mark.asyncio
async def test_clawhub_provider_downloads_skill_markdown_from_archive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    skill_md = (
        "---\n"
        "name: pdf\n"
        "description: Full PDF skill.\n"
        "---\n\n"
        "# PDF Processing Guide\n\n"
        "Lots of complete instructions.\n"
    )

    async def fake_get(self, url: str, **kwargs):
        if url == "https://clawhub.ai/awspace/pdf":
            return _text_response(
                '<a href="https://packages.example.test/api/v1/download?slug=pdf">Download</a>',
                url=url,
            )
        if url == "https://packages.example.test/api/v1/download?slug=pdf":
            return _zip_response({"SKILL.md": skill_md, "_meta.json": "{}"}, url=url)
        raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr("openhire.skill_catalog.validate_url_target", lambda url: (True, ""))
    monkeypatch.setattr("openhire.skill_catalog.validate_resolved_url", lambda url: (True, ""))
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    provider = HttpClawHubSkillProvider()

    assert await provider.fetch_skill_markdown("https://clawhub.ai/awspace/pdf") == skill_md


@pytest.mark.asyncio
async def test_clawhub_provider_parses_package_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(self, url: str, **kwargs):
        assert url == "https://clawhub.ai/awspace/pdf"
        return _text_response(
            """
            <div>Skill flagged — suspicious patterns detected</div>
            <span class="meta-stat-value">30.5k</span><span class="meta-stat-label">downloads</span>
            <span class="meta-stat-value">44</span><span class="meta-stat-label">stars</span>
            <a href="https://packages.example.test/api/v1/download?slug=pdf">Download</a>
            """,
            url=url,
        )

    monkeypatch.setattr("openhire.skill_catalog.validate_url_target", lambda url: (True, ""))
    monkeypatch.setattr("openhire.skill_catalog.validate_resolved_url", lambda url: (True, ""))
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    provider = HttpClawHubSkillProvider()
    details = await provider.fetch_package_details("https://clawhub.ai/awspace/pdf")

    assert details == {
        "downloads": 30500,
        "stars": 44,
        "risk": "suspicious",
        "download_url": "https://packages.example.test/api/v1/download?slug=pdf",
    }


@pytest.mark.asyncio
async def test_clawhub_provider_rejects_archive_without_skill_md(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(self, url: str, **kwargs):
        if url == "https://clawhub.ai/awspace/pdf":
            return _text_response(
                '<a href="https://packages.example.test/api/v1/download?slug=pdf">Download</a>',
                url=url,
            )
        if url == "https://packages.example.test/api/v1/download?slug=pdf":
            return _zip_response({"README.md": "# nope"}, url=url)
        raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr("openhire.skill_catalog.validate_url_target", lambda url: (True, ""))
    monkeypatch.setattr("openhire.skill_catalog.validate_resolved_url", lambda url: (True, ""))
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    provider = HttpClawHubSkillProvider()
    with pytest.raises(ClawHubProviderError, match="SKILL.md"):
        await provider.fetch_skill_markdown("https://clawhub.ai/awspace/pdf")


@pytest.mark.asyncio
async def test_clawhub_provider_rejects_invalid_archive_zip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(self, url: str, **kwargs):
        if url == "https://clawhub.ai/awspace/pdf":
            return _text_response(
                '<a href="https://packages.example.test/api/v1/download?slug=pdf">Download</a>',
                url=url,
            )
        if url == "https://packages.example.test/api/v1/download?slug=pdf":
            return httpx.Response(200, content=b"not a zip", request=httpx.Request("GET", url))
        raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr("openhire.skill_catalog.validate_url_target", lambda url: (True, ""))
    monkeypatch.setattr("openhire.skill_catalog.validate_resolved_url", lambda url: (True, ""))
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    provider = HttpClawHubSkillProvider()
    with pytest.raises(ClawHubProviderError, match="archive"):
        await provider.fetch_skill_markdown("https://clawhub.ai/awspace/pdf")
