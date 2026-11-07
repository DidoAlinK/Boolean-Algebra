"""Tests for the body size limit, the rate limiter and the /api/simplify endpoint."""
import threading

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app import config
from app.limits import BodyLimitMiddleware, RateLimiter, RateLimitMiddleware, client_address
from app.main import app, _simplify_slots


# -- RateLimiter (no web server needed: the clock is a variable we move by hand) ------------------
class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_allows_the_limit_then_refuses_with_the_wait_time():
    clock = FakeClock()
    limiter = RateLimiter([("/api/", 3, 60)], clock)
    assert [limiter.check("1.1.1.1", "/api/x") for _ in range(3)] == [0, 0, 0]
    assert limiter.check("1.1.1.1", "/api/x") == 60        # the first request expires in 60 s
    clock.now += 25
    assert limiter.check("1.1.1.1", "/api/x") == 35        # 60 - 25


def test_window_slides():
    clock = FakeClock()
    limiter = RateLimiter([("/api/", 2, 60)], clock)
    limiter.check("a", "/api/x")
    clock.now += 30
    limiter.check("a", "/api/x")
    assert limiter.check("a", "/api/x") > 0
    clock.now += 31                                         # the first request (t=0) is now 61 s old
    assert limiter.check("a", "/api/x") == 0


def test_clients_and_rules_are_counted_separately():
    limiter = RateLimiter([("/api/simplify", 1, 60), ("/api/", 5, 60)], FakeClock())
    assert limiter.check("a", "/api/simplify") == 0
    assert limiter.check("a", "/api/simplify") > 0          # a is out of simplify requests
    assert limiter.check("b", "/api/simplify") == 0         # b is not
    assert limiter.check("a", "/api/analyze") == 0          # and a still has the general budget


def test_paths_without_a_rule_are_not_limited():
    limiter = RateLimiter([("/api/", 1, 60)], FakeClock())
    for _ in range(10):
        assert limiter.check("a", "/index.html") == 0


def test_old_clients_are_forgotten_so_memory_stays_bounded(monkeypatch):
    import app.limits as limits
    monkeypatch.setattr(limits, "MAX_TRACKED_CLIENTS", 5)
    clock = FakeClock()
    limiter = RateLimiter([("/api/", 1, 60)], clock)
    for n in range(6):
        limiter.check(f"client{n}", "/api/x")
    clock.now += 120
    limiter.check("newcomer", "/api/x")
    assert len(limiter.hits) == 1


def test_proxy_header_is_only_trusted_when_asked():
    scope = {"headers": [(b"x-forwarded-for", b"6.6.6.6, 9.9.9.9")], "client": ("10.0.0.1", 5000)}
    assert client_address(scope, trust_proxy=False) == "10.0.0.1"
    assert client_address(scope, trust_proxy=True) == "9.9.9.9"      # the LAST entry, written by our proxy


# -- the middlewares on a tiny app ----------------------------------------------------------------
def tiny_app(max_bytes=100, limit=2):
    tiny = FastAPI()

    @tiny.post("/api/echo")
    async def echo(request: Request):
        return {"size": len(await request.body())}

    tiny.add_middleware(BodyLimitMiddleware, max_bytes=max_bytes)
    tiny.add_middleware(RateLimitMiddleware, limiter=RateLimiter([("/api/", limit, 60)]))
    return TestClient(tiny)


def test_small_bodies_pass_through_intact():
    assert tiny_app().post("/api/echo", content=b"x" * 100).json() == {"size": 100}


def test_declared_oversize_body_is_refused_with_413():
    response = tiny_app().post("/api/echo", content=b"x" * 101)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "payload_too_large"


def test_streamed_oversize_body_is_refused_without_a_content_length():
    def chunks():
        for _ in range(5):
            yield b"x" * 30                                 # 150 bytes in total, sent in pieces

    response = tiny_app().post("/api/echo", content=chunks())
    assert response.status_code == 413


def test_rate_limit_returns_429_with_retry_after():
    client = tiny_app(limit=2)
    assert client.post("/api/echo", content=b"{}").status_code == 200
    assert client.post("/api/echo", content=b"{}").status_code == 200
    response = client.post("/api/echo", content=b"{}")
    assert response.status_code == 429
    body = response.json()["error"]
    assert body["code"] == "rate_limited" and body["retry_after"] >= 1
    assert int(response.headers["retry-after"]) == body["retry_after"]


def test_oversize_requests_also_count_against_the_rate_limit():
    client = tiny_app(max_bytes=10, limit=1)
    assert client.post("/api/echo", content=b"x" * 50).status_code == 413
    assert client.post("/api/echo", content=b"x" * 50).status_code == 429


# -- the real app ----------------------------------------------------------------------------------
client = TestClient(app)


def test_simplify_endpoint_returns_named_steps():
    response = client.post("/api/simplify", json={"expression": "xy + x'z + yz"})
    assert response.status_code == 200
    data = response.json()
    assert data["result"] == "xy + x'z" and data["verified"] is True
    assert data["steps"][0]["rule"] == "T6a" and data["steps"][0]["rule_name"] == "Consensus"


def test_simplify_rules_endpoint_lists_the_sheet():
    ids = [rule["id"] for rule in client.get("/api/simplify/rules").json()]
    for expected in ("P1a", "P5b", "T3a", "T4b", "T5a", "T6b", "INV"):
        assert expected in ids


def test_simplify_parse_error_has_a_position():
    response = client.post("/api/simplify", json={"expression": "(a + b"})
    assert response.status_code == 422
    assert response.json()["error"] == {"code": "parse_error", "message": "missing ')'", "position": 7}


def test_simplify_accepts_long_expressions_that_analyze_refuses():
    expression = " + ".join(["ab"] * 150)                  # about 750 characters
    assert client.post("/api/analyze", json={"expression": expression}).status_code == 422
    assert client.post("/api/simplify", json={"expression": expression}).status_code == 200


def test_simplify_rejects_expressions_over_the_length_limit():
    response = client.post("/api/simplify", json={"expression": "a" * (config.MAX_SIMPLIFY_LENGTH + 1)})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_simplify_unknown_preset_is_400():
    response = client.post("/api/simplify", json={"expression": "a", "preset": "nope"})
    assert response.status_code == 400 and response.json()["error"]["code"] == "unknown_preset"


def test_real_app_refuses_a_huge_body():
    response = client.post("/api/analyze", content=b'{"expression": "' + b"a" * (config.MAX_BODY_BYTES + 10) + b'"}',
                           headers={"content-type": "application/json"})
    assert response.status_code == 413


def test_real_app_rate_limits_simplify():
    limit = next(count for prefix, count, _ in config.RATE_LIMITS if prefix == "/api/simplify")
    codes = [client.post("/api/simplify", json={"expression": "a"}).status_code for _ in range(limit + 1)]
    assert codes[:limit] == [200] * limit and codes[limit] == 429


def test_busy_server_answers_503_instead_of_queueing():
    taken = 0
    try:
        while _simplify_slots.acquire(blocking=False):      # occupy every slot
            taken += 1
        response = client.post("/api/simplify", json={"expression": "a + a"})
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "busy"
    finally:
        for _ in range(taken):
            _simplify_slots.release()
    assert client.post("/api/simplify", json={"expression": "a + a"}).status_code == 200


def test_error_responses_still_carry_cors_headers():
    # Otherwise a browser would show "network error" instead of the real message.
    response = client.post("/api/analyze", content=b"x" * (config.MAX_BODY_BYTES + 1),
                           headers={"origin": "http://localhost:5173", "content-type": "application/json"})
    assert response.status_code == 413
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
