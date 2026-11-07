"""The private-beta passcode gate: off unless BETA_PASSCODE is set, and airtight when it is."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from core import beta_gate
from core.beta_gate import COOKIE_NAME, MAX_FAILURES, UNLOCK_PATH, safe_next
from main import start_application

PASSCODE = "correct horse"  # test-only value


@pytest.fixture
def make_client(monkeypatch: pytest.MonkeyPatch) -> Callable[..., TestClient]:
    def build(passcode: str | None = PASSCODE) -> TestClient:
        if passcode is None:
            monkeypatch.delenv("BETA_PASSCODE", raising=False)
        else:
            monkeypatch.setenv("BETA_PASSCODE", passcode)
        # https, because the cookie is Secure and would not be sent back over plain http
        return TestClient(start_application(), base_url="https://testserver", follow_redirects=False)

    return build


def unlock(client: TestClient, passcode: str = PASSCODE, next_path: str = "/", forwarded_for: str | None = None):
    headers = {"X-Forwarded-For": forwarded_for} if forwarded_for else {}
    return client.post(UNLOCK_PATH, data={"passcode": passcode, "next": next_path}, headers=headers)


@pytest.mark.parametrize("passcode", [None, ""])
def test_gate_is_off_when_passcode_is_unset_or_empty(make_client, passcode) -> None:
    client = make_client(passcode)
    assert client.get("/").status_code == 200
    assert "x-robots-tag" not in client.get("/").headers
    robots = client.get("/robots.txt").text
    assert "Sitemap:" in robots and "Disallow" not in robots


def test_gate_blocks_pages_and_assets_without_a_cookie(make_client) -> None:
    client = make_client()
    for path in ("/", "/robots-not", "/static/css/notebook/anything.css", "/sitemap.xml"):
        response = client.get(path)
        assert response.status_code == 401, path
        assert 'name="passcode"' in response.text
    assert client.post("/", data={"a": "b"}).status_code == 401


def test_right_passcode_sets_a_hardened_cookie_and_lets_the_visitor_in(make_client) -> None:
    client = make_client()
    response = unlock(client)
    assert response.status_code == 303 and response.headers["location"] == "/"
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f"{COOKIE_NAME}=")
    for attribute in ("HttpOnly", "Secure", "SameSite=lax", f"Max-Age={30 * 24 * 3600}"):
        assert attribute.lower() in cookie.lower()
    assert PASSCODE not in cookie
    assert client.get("/").status_code == 200


def test_wrong_passcode_shows_an_error_and_sets_no_cookie(make_client) -> None:
    client = make_client()
    response = unlock(client, "nope")
    assert response.status_code == 401
    assert "not right" in response.text
    assert "set-cookie" not in response.headers
    assert client.get("/").status_code == 401


def test_repeated_wrong_guesses_lock_the_address_out_even_for_the_right_passcode(make_client) -> None:
    client = make_client()
    for _ in range(MAX_FAILURES):
        assert unlock(client, "nope").status_code == 401
    locked = unlock(client)
    assert locked.status_code == 429 and "set-cookie" not in locked.headers
    # another address is unaffected
    assert unlock(client, forwarded_for="203.0.113.9").status_code == 303


def test_forged_leading_forwarded_for_entries_do_not_dodge_the_limit(make_client) -> None:
    client = make_client()
    for attempt in range(MAX_FAILURES):
        unlock(client, "nope", forwarded_for=f"10.0.0.{attempt}, 198.51.100.7")
    assert unlock(client, forwarded_for="10.9.9.9, 198.51.100.7").status_code == 429


def test_cookie_stops_working_when_the_passcode_changes(make_client) -> None:
    client = make_client()
    cookie = unlock(client).cookies[COOKIE_NAME]
    assert client.get("/").status_code == 200

    rotated = make_client("a different passcode")
    rotated.cookies.set(COOKIE_NAME, cookie)
    assert rotated.get("/").status_code == 401


def test_tampered_malformed_and_expired_cookies_are_refused(make_client, monkeypatch) -> None:
    client = make_client()
    good = unlock(client).cookies[COOKIE_NAME]
    expires, _, signature = good.partition(".")
    for bad in ("", "garbage", f"{int(expires) + 999}.{signature}", f"{expires}.", ".", f"x.{signature}", f"-1.{signature}"):
        fresh = make_client()
        fresh.cookies.set(COOKIE_NAME, bad)
        assert fresh.get("/").status_code == 401, bad

    gate = beta_gate.BetaGate(app=None, passcode=PASSCODE)
    assert gate.cookie_is_valid(gate.make_cookie(now=1_000), now=1_001)
    assert not gate.cookie_is_valid(gate.make_cookie(now=1_000), now=1_000 + 30 * 24 * 3600 + 1)


def test_every_response_is_marked_noindex_and_robots_disallows_everything(make_client) -> None:
    client = make_client()
    assert client.get("/").headers["x-robots-tag"] == "noindex, nofollow"  # gated page
    assert unlock(client, "nope").headers["x-robots-tag"] == "noindex, nofollow"
    assert unlock(client).headers["x-robots-tag"] == "noindex, nofollow"  # redirect
    assert client.get("/").headers["x-robots-tag"] == "noindex, nofollow"  # real page, past the gate
    assert client.get("/static/does-not-exist").headers["x-robots-tag"] == "noindex, nofollow"  # a 404

    anonymous = make_client()
    robots = anonymous.get("/robots.txt")
    assert robots.status_code == 200 and robots.headers["content-type"].startswith("text/plain")
    assert robots.text == "User-agent: *\nDisallow: /\n"
    assert robots.headers["x-robots-tag"] == "noindex, nofollow"


def test_visitor_returns_to_the_page_they_asked_for(make_client) -> None:
    client = make_client()
    page = client.get("/some/page?tab=2")
    assert 'name="next" value="/some/page?tab=2"' in page.text
    assert unlock(client, next_path="/some/page?tab=2").headers["location"] == "/some/page?tab=2"


@pytest.mark.parametrize(
    "target",
    ["https://evil.example", "//evil.example", "/\\evil.example", "evil.example", "javascript:alert(1)", "/ok\r\nSet-Cookie: x=y", ""],
)
def test_no_open_redirect(make_client, target: str) -> None:
    client = make_client()
    assert safe_next(target) == "/"
    assert unlock(client, next_path=target).headers["location"] == "/"


def test_next_is_escaped_in_the_form(make_client) -> None:
    page = make_client().get('/x?"><script>alert(1)</script>')
    assert "<script>alert" not in page.text
