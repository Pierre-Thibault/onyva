from typing import Any, Callable

class Bottle:
    def __init__(self) -> None: ...
    def route(
        self,
        path: str | None = None,
        method: str = "GET",
        callback: Callable[..., Any] | None = None,
        name: str | None = None,
        apply: Any | None = None,
        skip: Any | None = None,
        **config: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...
    def run(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        debug: bool = False,
        **kwargs: Any,
    ) -> None: ...

def route(
    path: str | None = None,
    method: str = "GET",
    callback: Callable[..., Any] | None = None,
    name: str | None = None,
    apply: Any | None = None,
    skip: Any | None = None,
    **config: Any,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...
def run(
    host: str = "127.0.0.1",
    port: int = 8080,
    debug: bool = False,
    **kwargs: Any,
) -> None: ...
def static_file(
    filename: str,
    root: str,
    mimetype: str | None = None,
    download: bool | str = False,
    charset: str = "UTF-8",
) -> Any: ...
