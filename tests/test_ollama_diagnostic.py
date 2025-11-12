import json
from types import SimpleNamespace

import pytest

from app import ollama_diagnostic as diag


class DummyResponse(SimpleNamespace):
    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    monkeypatch.delenv("HTTP_PROXY", raising=False)
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    monkeypatch.delenv("ALL_PROXY", raising=False)
    monkeypatch.delenv("NO_PROXY", raising=False)


def test_check_env_configuration_handles_invalid_url():
    result = diag.check_env_configuration("localhost", "test")
    assert result.status == "warning"
    assert "Niepoprawny adres" in result.details


def test_check_proxy_settings_detects_proxy(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.local:8080")
    result = diag.check_proxy_settings()
    assert result.status == "warning"
    assert "proxy" in result.details.lower()


def test_check_dns_resolution_success(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "")
    monkeypatch.setenv("HTTPS_PROXY", "")
    result = diag.check_dns_resolution("localhost")
    assert result.status == "ok"


def test_check_dns_resolution_failure(monkeypatch):
    def raise_error(_):
        raise diag.socket.gaierror("boom")

    monkeypatch.setattr(diag.socket, "gethostbyname", raise_error)
    result = diag.check_dns_resolution("bad-host")
    assert result.status == "error"
    assert "bad-host" in result.details


def test_check_socket_connectivity_ok(monkeypatch):
    class DummySocket:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(diag.socket, "create_connection", lambda *args, **kwargs: DummySocket())
    result = diag.check_socket_connectivity("host", 1234)
    assert result.status == "ok"


def test_check_socket_connectivity_timeout(monkeypatch):
    def raise_timeout(*_, **__):
        raise diag.socket.timeout()

    monkeypatch.setattr(diag.socket, "create_connection", raise_timeout)
    result = diag.check_socket_connectivity("host", 1234)
    assert result.status == "error"
    assert "limit czasu" in result.details


def test_check_http_endpoint_ok(monkeypatch):
    payload = {"models": [{"name": "m1"}, {"name": "m2"}]}

    def fake_get(url, timeout):
        return DummyResponse(status_code=200, payload=payload)

    monkeypatch.setattr(diag.requests, "get", fake_get)
    result = diag.check_http_endpoint("http://host:11434", "m1")
    assert result.status == "ok"


def test_check_http_endpoint_missing_model(monkeypatch):
    payload = {"models": [{"name": "other"}]}

    def fake_get(url, timeout):
        return DummyResponse(status_code=200, payload=payload)

    monkeypatch.setattr(diag.requests, "get", fake_get)
    result = diag.check_http_endpoint("http://host:11434", "missing")
    assert result.status == "warning"
    assert "missing" in result.details


def test_check_http_endpoint_bad_json(monkeypatch):
    def fake_get(url, timeout):
        return DummyResponse(status_code=200, payload=ValueError("boom"))

    monkeypatch.setattr(diag.requests, "get", fake_get)
    result = diag.check_http_endpoint("http://host:11434", "m1")
    assert result.status == "warning"
    assert "JSON" in result.details


def test_check_firewall_indicators_no_tools(monkeypatch):
    monkeypatch.setattr(diag.shutil, "which", lambda _: None)
    result = diag.check_firewall_indicators("host", 11434)
    assert result.status == "ok"


def test_check_firewall_indicators_detects_ufw(monkeypatch):
    monkeypatch.setattr(diag.shutil, "which", lambda cmd: "/usr/sbin/ufw" if cmd == "ufw" else None)

    def fake_run(command, capture_output, text, timeout, check):
        return SimpleNamespace(stdout="Status: active", stderr="")

    monkeypatch.setattr(diag, "_run_command", fake_run)
    result = diag.check_firewall_indicators("host", 11434)
    assert result.status == "warning"
    assert "ufw" in result.details.lower()


def test_run_diagnostics_aggregates_results(monkeypatch):
    monkeypatch.setattr(diag, "check_env_configuration", lambda base_url, model: diag.DiagnosticResult("environment", "ok", "env ok"))
    monkeypatch.setattr(diag, "check_proxy_settings", lambda: diag.DiagnosticResult("proxy", "ok", "proxy ok"))
    monkeypatch.setattr(diag, "check_dns_resolution", lambda host: diag.DiagnosticResult("dns", "ok", "dns ok"))
    monkeypatch.setattr(diag, "check_socket_connectivity", lambda host, port: diag.DiagnosticResult("tcp", "ok", "tcp ok"))
    monkeypatch.setattr(diag, "check_http_endpoint", lambda base_url, model: diag.DiagnosticResult("http", "ok", "http ok"))
    monkeypatch.setattr(diag, "check_firewall_indicators", lambda host, port: diag.DiagnosticResult("firewall", "ok", "fw ok"))

    results = diag.run_diagnostics("http://host:11434", "model")
    assert len(results) == 6
    assert {r.status for r in results} == {"ok"}


def test_main_json_output(monkeypatch, capsys):
    monkeypatch.setattr(
        diag,
        "run_diagnostics",
        lambda base_url, model: [diag.DiagnosticResult("environment", "ok", "env ok")],
    )
    exit_code = diag.main(["--json"])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    payload = json.loads(output)
    assert payload[0]["name"]
    assert payload[0]["status"] == "ok"

