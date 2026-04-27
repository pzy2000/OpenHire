from openhire.config.schema import DreamConfig


def test_dream_config_defaults_to_five_minute_interval() -> None:
    cfg = DreamConfig()

    assert cfg.interval_m == 5
    assert cfg.interval_h is None
    assert cfg.cron is None


def test_dream_config_builds_every_schedule_from_minute_interval() -> None:
    cfg = DreamConfig(interval_m=7)

    schedule = cfg.build_schedule("UTC")

    assert schedule.kind == "every"
    assert schedule.every_ms == 7 * 60_000
    assert schedule.expr is None
    assert cfg.describe_schedule() == "every 7m"


def test_dream_config_honors_legacy_interval_hours() -> None:
    cfg = DreamConfig.model_validate({"intervalH": 3})

    schedule = cfg.build_schedule("UTC")

    assert cfg.interval_h == 3
    assert schedule.kind == "every"
    assert schedule.every_ms == 3 * 3_600_000
    assert cfg.describe_schedule() == "every 3h (legacy)"


def test_dream_config_honors_legacy_cron_override() -> None:
    cfg = DreamConfig.model_validate({"cron": "0 */4 * * *"})

    schedule = cfg.build_schedule("UTC")

    assert schedule.kind == "cron"
    assert schedule.expr == "0 */4 * * *"
    assert schedule.tz == "UTC"
    assert cfg.describe_schedule() == "cron 0 */4 * * * (legacy)"


def test_dream_config_dump_uses_interval_m_and_hides_legacy_overrides() -> None:
    cfg = DreamConfig.model_validate({"intervalM": 5, "intervalH": 2, "cron": "0 */4 * * *"})

    dumped = cfg.model_dump(by_alias=True)

    assert dumped["intervalM"] == 5
    assert "intervalH" not in dumped
    assert "cron" not in dumped


def test_dream_config_uses_model_override_name_and_accepts_legacy_model() -> None:
    cfg = DreamConfig.model_validate({"model": "openrouter/sonnet"})

    dumped = cfg.model_dump(by_alias=True)

    assert cfg.model_override == "openrouter/sonnet"
    assert dumped["modelOverride"] == "openrouter/sonnet"
    assert "model" not in dumped
