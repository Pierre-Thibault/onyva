from typing import Any

class Dynaconf:
    def __init__(
        self,
        envvar_prefix: str = ...,
        settings_files: list[str] = ...,
        environments: bool = ...,
        env_switcher: str = ...,
        **kwargs: Any,
    ) -> None: ...
    def __getattr__(self, name: str) -> Any: ...
