from pathlib import Path

from openhire.workforce.outbound_bridge import (
    OUTBOUND_PREFIX,
    clean_docker_agent_output,
    parse_docker_outbound_output,
)


def test_parse_single_outbound_message_removes_protocol_line(tmp_path: Path) -> None:
    parsed = parse_docker_outbound_output(
        f"before\n{OUTBOUND_PREFIX} {{\"content\":\"hello\"}}\nafter",
        workspace=tmp_path,
    )

    assert parsed.cleaned_output == "before\nafter"
    assert len(parsed.messages) == 1
    assert parsed.messages[0].content == "hello"
    assert parsed.messages[0].media == []
    assert parsed.errors == []


def test_parse_multiple_outbound_messages(tmp_path: Path) -> None:
    parsed = parse_docker_outbound_output(
        "\n".join([
            f"{OUTBOUND_PREFIX} {{\"content\":\"one\"}}",
            "normal output",
            f"{OUTBOUND_PREFIX} {{\"content\":\"two\"}}",
        ]),
        workspace=tmp_path,
    )

    assert parsed.cleaned_output == "normal output"
    assert [item.content for item in parsed.messages] == ["one", "two"]


def test_invalid_json_is_reported_and_not_sent(tmp_path: Path) -> None:
    parsed = parse_docker_outbound_output(
        f"{OUTBOUND_PREFIX} {{not-json",
        workspace=tmp_path,
    )

    assert parsed.cleaned_output == ""
    assert parsed.messages == []
    assert parsed.errors
    assert "invalid JSON" in parsed.errors[0]


def test_empty_content_is_rejected(tmp_path: Path) -> None:
    parsed = parse_docker_outbound_output(
        f"{OUTBOUND_PREFIX} {{\"content\":\"   \"}}",
        workspace=tmp_path,
    )

    assert parsed.messages == []
    assert parsed.errors == ["outbound message 1 content is required"]


def test_channel_and_chat_id_are_rejected(tmp_path: Path) -> None:
    parsed = parse_docker_outbound_output(
        f"{OUTBOUND_PREFIX} {{\"content\":\"hello\",\"channel\":\"feishu\",\"chat_id\":\"oc_other\"}}",
        workspace=tmp_path,
    )

    assert parsed.messages == []
    assert parsed.errors == ["outbound message 1 must not specify channel or chat_id"]


def test_media_paths_are_mapped_to_workspace(tmp_path: Path) -> None:
    parsed = parse_docker_outbound_output(
        f"{OUTBOUND_PREFIX} {{\"content\":\"see files\",\"media\":[\"tmp/a.pdf\",\"/workspace/images/b.png\"]}}",
        workspace=tmp_path,
    )

    assert parsed.errors == []
    assert parsed.messages[0].media == [
        str(tmp_path / "tmp" / "a.pdf"),
        str(tmp_path / "images" / "b.png"),
    ]


def test_workspace_escape_media_path_is_rejected(tmp_path: Path) -> None:
    parsed = parse_docker_outbound_output(
        f"{OUTBOUND_PREFIX} {{\"content\":\"bad\",\"media\":[\"../secret.txt\"]}}",
        workspace=tmp_path,
    )

    assert parsed.messages == []
    assert parsed.errors
    assert "escapes workspace" in parsed.errors[0]


def test_clean_output_removes_nanobot_banner() -> None:
    assert clean_docker_agent_output("🐈 nanobot\nhello") == "hello"


def test_clean_output_extracts_content_from_json_only_line() -> None:
    assert clean_docker_agent_output('{"content":"群聊内容"}') == "群聊内容"


def test_split_protocol_output_leaves_json_for_fallback(tmp_path: Path) -> None:
    parsed = parse_docker_outbound_output(
        f"🐈 nanobot\n{OUTBOUND_PREFIX}\n{{\"content\":\"拆行内容\"}}",
        workspace=tmp_path,
    )

    assert parsed.messages == []
    assert parsed.errors
    assert clean_docker_agent_output(parsed.cleaned_output) == "拆行内容"
