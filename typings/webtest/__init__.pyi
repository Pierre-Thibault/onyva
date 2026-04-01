from typing import Any

from webtest.response import TestResponse

class TestApp:
    def __init__(self, app: Any) -> None: ...
    def get(
        self,
        url: str,
        params: Any | None = None,
        headers: Any | None = None,
        extra_environ: Any | None = None,
        status: int | None = None,
        expect_errors: bool = False,
        xhr: bool = False,
    ) -> TestResponse: ...
    def post(
        self,
        url: str,
        params: Any | None = None,
        headers: Any | None = None,
        extra_environ: Any | None = None,
        status: int | None = None,
        expect_errors: bool = False,
        xhr: bool = False,
    ) -> TestResponse: ...
