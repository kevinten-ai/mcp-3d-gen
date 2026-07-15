import asyncio

from model_gen import server


class FakeResponse:
    status_code = 200
    content = b"model"


class FakeClient:
    def __init__(self, captured, **kwargs):
        captured["client_kwargs"] = kwargs
        captured["constructed"] = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def get(self, url, **kwargs):
        self.captured_url = url
        return FakeResponse()


def test_auto_download_keeps_tls_verification_enabled(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setattr(
        server.httpx,
        "AsyncClient",
        lambda **kwargs: FakeClient(captured, **kwargs),
    )

    result = asyncio.run(
        server._try_download("https://cdn.example/model.glb", str(tmp_path), "tripo")
    )

    assert result is not None
    assert captured["client_kwargs"].get("verify", True) is True


def test_auto_download_rejects_non_http_urls(monkeypatch, tmp_path):
    captured = {"constructed": False}
    monkeypatch.setattr(
        server.httpx,
        "AsyncClient",
        lambda **kwargs: FakeClient(captured, **kwargs),
    )

    result = asyncio.run(
        server._try_download("file:///etc/passwd", str(tmp_path), "tripo")
    )

    assert result is None
    assert captured["constructed"] is False


def test_auto_download_handles_malformed_urls(monkeypatch, tmp_path):
    captured = {"constructed": False}
    monkeypatch.setattr(
        server.httpx,
        "AsyncClient",
        lambda **kwargs: FakeClient(captured, **kwargs),
    )

    result = asyncio.run(server._try_download("http://[", str(tmp_path), "tripo"))

    assert result is None
    assert captured["constructed"] is False


def test_output_format_schema_uses_an_allowlist():
    tools = asyncio.run(server.handle_list_tools())
    by_name = {tool.name: tool for tool in tools}
    expected = ["glb", "fbx", "obj", "usdz", "stl"]

    assert by_name["generate_3d"].inputSchema["properties"]["output_format"]["enum"] == expected
    assert by_name["query_3d_status"].inputSchema["properties"]["output_format"]["enum"] == expected


def test_generate_rejects_unknown_output_format(monkeypatch):
    class Provider:
        called = False

        async def generate(self, *_args, **_kwargs):
            self.called = True
            raise AssertionError("provider should not be called")

    provider = Provider()
    monkeypatch.setattr(server, "_default_provider_name", lambda: "fake")
    monkeypatch.setattr(server, "get_provider", lambda _name: provider)

    result = asyncio.run(
        server.handle_call_tool(
            "generate_3d",
            {"prompt": "cube", "output_format": "../../outside"},
        )
    )

    assert "Unsupported output_format" in result[0].text
    assert provider.called is False


def test_query_rejects_unknown_output_format(monkeypatch):
    class Provider:
        called = False

        async def query(self, *_args, **_kwargs):
            self.called = True
            raise AssertionError("provider should not be called")

    provider = Provider()
    monkeypatch.setattr(server, "get_provider", lambda _name: provider)

    result = asyncio.run(
        server.handle_call_tool(
            "query_3d_status",
            {
                "task_id": "task",
                "provider": "fake",
                "output_format": "../../outside",
            },
        )
    )

    assert "Unsupported output_format" in result[0].text
    assert provider.called is False
