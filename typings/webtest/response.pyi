class TestResponse:
    status: str
    status_int: int
    text: str
    body: bytes
    headers: dict[str, str]
    json: dict[str, object]
