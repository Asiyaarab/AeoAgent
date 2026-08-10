"""Tests for app/ai_client.py — Z.ai wrapper, mocked transport."""
import json
from unittest.mock import MagicMock

import pytest
import requests

from app import ai_client
from app.ai_client import call_ai


def _ok_response(content: str) -> MagicMock:
    """Build a MagicMock that quacks like a requests.Response with status 200."""
    resp = MagicMock(spec=requests.Response)
    resp.status_code = 200
    resp.json.return_value = {"choices": [{"message": {"content": content}}]}
    resp.text = json.dumps(resp.json.return_value)
    resp.raise_for_status.return_value = None
    return resp


def test_call_ai_sends_bearer_token(monkeypatch):
    captured = {}

    def fake_post(url, json, headers, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return _ok_response("hello")

    monkeypatch.setattr(ai_client.requests, "post", fake_post)

    out = call_ai("ping")
    assert out == "hello"
    assert captured["headers"]["Authorization"] == "Bearer test-zai-key"
    assert captured["headers"]["Content-Type"] == "application/json"
    assert captured["json"]["model"] == ai_client.Z_AI_MODEL
    assert captured["json"]["messages"][0]["role"] == "system"
    assert captured["json"]["messages"][1]["content"] == "ping"
    assert captured["timeout"] == 60


def test_call_ai_uses_custom_system_prompt(monkeypatch):
    captured = {}

    def fake_post(url, json, headers, timeout):
        captured["json"] = json
        return _ok_response("ok")

    monkeypatch.setattr(ai_client.requests, "post", fake_post)
    call_ai("hi", system="be terse")
    assert captured["json"]["messages"][0]["content"] == "be terse"


def test_call_ai_raises_when_key_missing(monkeypatch):
    monkeypatch.setattr(ai_client, "Z_AI_API_KEY", None)
    with pytest.raises(RuntimeError, match="Z_AI_API_KEY"):
        call_ai("anything")


def test_call_ai_raises_on_non_200(monkeypatch):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = 401
    resp.text = '{"error":"unauthorized"}'
    resp.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")

    monkeypatch.setattr(ai_client.requests, "post", lambda *a, **kw: resp)
    with pytest.raises(requests.HTTPError):
        call_ai("anything")

