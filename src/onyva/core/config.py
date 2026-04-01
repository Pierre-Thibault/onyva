"""Application configuration using dynaconf."""

from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="APP",
    settings_files=["settings.toml"],
    environments=True,
    env_switcher="APP_ENV",
)
