"""Unit tests for the pure helpers in advisor_core (no network / no API client needed,
since advisor_core creates no client at import).

Run with pytest (`python -m pytest test_advisor_core.py`) or directly
(`python test_advisor_core.py`) — a tiny runner at the bottom executes every test.
"""

from advisor_core import (
    ROADMAP_OPEN,
    _extract_roadmap,
    _strip_roadmap_block,
    generate_validated_reply,
)

VALID_BLOCK = (
    '<roadmap-json>{"cs_cap": 2, "terms": '
    '[{"term": "Fall 2026", "courses": ["CSC 1001"]}]}</roadmap-json>'
)


def test_extract_valid_block_parses():
    roadmap = _extract_roadmap("Here is your plan.\n\n" + VALID_BLOCK)
    assert roadmap is not None
    assert roadmap["cs_cap"] == 2
    assert roadmap["terms"][0]["term"] == "Fall 2026"


def test_extract_no_block_returns_none():
    assert _extract_roadmap("Just a conversational reply, no plan here.") is None


def test_extract_malformed_json_returns_none():
    bad = '<roadmap-json>{"terms": [oops not valid json}</roadmap-json>'
    assert _extract_roadmap(bad) is None


def test_extract_json_fenced_block_still_parses():
    fenced = (
        "<roadmap-json>```json\n"
        '{"terms": [{"term": "Fall 2026", "courses": ["CSC 1001"]}]}\n'
        "```</roadmap-json>"
    )
    roadmap = _extract_roadmap(fenced)
    assert roadmap is not None
    assert roadmap["terms"][0]["courses"] == ["CSC 1001"]


def test_strip_removes_block():
    text = "Your plan:\n\n" + VALID_BLOCK + "\n\nLet me know!"
    stripped = _strip_roadmap_block(text)
    assert "<roadmap-json>" not in stripped
    assert "</roadmap-json>" not in stripped
    assert "Your plan:" in stripped
    assert "Let me know!" in stripped


def test_strip_collapses_blank_lines():
    # The block removal here leaves 3+ blank lines, which must collapse to one.
    text = "Intro\n\n" + VALID_BLOCK + "\n\nOutro"
    assert _strip_roadmap_block(text) == "Intro\n\nOutro"
    # Also collapses standalone runs of 3+ newlines.
    assert _strip_roadmap_block("A\n\n\n\nB") == "A\n\nB"


def test_strip_handles_truncated_block_without_closing_tag():
    # Model truncated at max_tokens mid-block: opening tag, no closing tag.
    text = 'Here is your plan.\n\n' + ROADMAP_OPEN + '{"cs_cap": 2, "terms": [{"term": "Fall'
    stripped = _strip_roadmap_block(text)
    assert ROADMAP_OPEN not in stripped
    assert stripped == "Here is your plan."


# --- generate_validated_reply with a FAKE client (no real API calls) -------------

class _Block:
    """Mimics an Anthropic text content block (.type == 'text', has .text)."""
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _Response:
    """Mimics an Anthropic Messages response: .content is a list of blocks."""
    def __init__(self, text):
        self.content = [_Block(text)]


class _FakeClient:
    """Returns canned responses in order; records how many times create() was called."""
    def __init__(self, reply_texts):
        self._replies = list(reply_texts)
        self.calls = 0
        self.messages = self  # so client.messages.create(...) works

    def create(self, **kwargs):
        self.calls += 1
        return _Response(self._replies.pop(0))


# Real course data from advising_data so validate_roadmap behaves authentically:
# CSC 1000/1001/1024 are all major courses with no prereqs, offered Fall.
_INVALID = (
    'Here is a plan.\n\n<roadmap-json>{"cs_cap": 2, "terms": '
    '[{"term": "Fall 2026", "courses": ["CSC 1000", "CSC 1001", "CSC 1024"]}]}'
    "</roadmap-json>"  # 3 CS courses with cs_cap 2 -> cap breach
)
_VALID = (
    'Here is the plan.\n\n<roadmap-json>{"cs_cap": 2, "terms": '
    '[{"term": "Fall 2026", "courses": ["CSC 1000", "CSC 1001"]}]}</roadmap-json>'
)


def test_generate_validated_reply_retries_then_returns_clean_plan():
    client = _FakeClient([_INVALID, _VALID])
    reply, remaining = generate_validated_reply(
        client,
        [{"role": "user", "content": "plan my degree"}],
        "system prompt",
        earliest_term="Fall 2026",
    )
    assert client.calls == 2, f"expected one retry (2 calls), got {client.calls}"
    assert remaining == [], f"final plan should validate clean, got {remaining}"
    assert "<roadmap-json>" in reply  # caller strips it; loop returns the raw block


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL  {test.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    raise SystemExit(1 if failed else 0)
