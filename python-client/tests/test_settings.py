import os
from pathlib import Path

from giskard.settings import Settings


def test_default_obj_equals_static_built():
    assert Settings(disable_analytics=os.getenv("GSK_DISABLE_ANALYTICS", "false")) == Settings.build_from_env()


def test_override_env():
    os.environ["GSK_DISABLE_ANALYTICS"] = "true"
    os.environ["GSK_WS_PORT"] = "4444"
    os.environ["GSK_HOST"] = "toto"

    settings = Settings.build_from_env()
    assert settings.disable_analytics
    assert settings.ws_port == 4444
    assert settings.host == "toto"


def test_expand_path():
    os.environ["ENV1"] = "~/toto/../${ENV2}"
    os.environ["ENV2"] = "${ENV3}/${ENV4}"
    os.environ["ENV3"] = "tutu"
    os.environ["ENV4"] = "tata"

    settings = Settings(home="${ENV1}")
    print(settings.home_dir.as_posix())
    assert settings.home_dir.as_posix() == (Path("~").expanduser().resolve() / "tutu/tata").as_posix()
