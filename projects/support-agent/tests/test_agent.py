import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from langchain_core.messages import AIMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatGeneration, ChatResult
from knowledge import build_store, SpacyEmbeddings
from tools import weekly_change
import pandas as pd
from agent import DECLINE, ask, build_agent, grade, verify

class ScriptedModel(BaseChatModel):
    #stands in for a real model so the tests need no gpu or key
    script: list
    calls: list = []

    @property
    def _llm_type(self):
        return "scripted"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.calls.append(messages)
        return ChatResult(generations=[ChatGeneration(message=self.script.pop(0))])


GOOD = '{"found": true, "source": "SUBS-01", "quote": "The C2 refill plan costs $24 per quarter."}'


@pytest.fixture(scope="module")
def store():
    return build_store(SpacyEmbeddings(), collection="tests")


def run(store, script, q="what do C2 refills cost", thread="t"):
    model = ScriptedModel(script=[AIMessage(s) for s in script], calls=[])
    return ask(build_agent(model, store, min_similarity=0.0, k=40), q, thread=thread)


def test_verified_answer_gets_a_citation_from_code(store):
    r = run(store, ["NO", GOOD, "YES"])
    assert r["action"] == "answer" and r["answer"].endswith("[SUBS-01]") and r["sources"] == ["SUBS-01"]


def test_invented_quote_is_declined(store):
    r = run(store, ["NO", '{"found": true, "source": "SUBS-01", "quote": "Filters are free for life."}'])
    assert r["answer"] == DECLINE


def test_made_up_source_is_declined(store):
    r = run(store, ["NO", '{"found": true, "source": "FAKE-99", "quote": "The C2 refill plan costs $24 per quarter."}'])
    assert r["action"] == "decline"


def test_answer_is_the_approved_sentence_even_with_a_copying_slip(store):
    r = run(store, ["NO", '{"found": true, "source": "SUBS-01", "quote": "The C2 refill plan cost $24 per quarter"}', "YES"])
    assert r["answer"] == "The C2 refill plan costs $24 per quarter. [SUBS-01]"


def test_second_look_can_find_what_the_first_missed(store):
    assert run(store, ["NO", '{"found": false}', GOOD, "YES"])["action"] == "answer"


def test_failed_relevance_check_is_declined(store):
    assert run(store, ["NO", GOOD, "NO"])["action"] == "decline"


def test_model_saying_not_found_is_declined(store):
    r = run(store, ["NO", '{"found": false}', '{"found": false}'])
    assert r["action"] == "decline" and r["decline_reason"] == "model_not_found"


def test_broken_json_is_declined(store):
    assert run(store, ["NO", "sure, it's probably $24", "still not json"])["action"] == "decline"


def test_safety_rule_works_even_if_model_says_no(store):
    assert run(store, [], q="is this safe for my infant")["action"] == "escalate"


def test_model_can_catch_what_the_rule_misses(store):
    assert run(store, ["YES"], q="grandma felt dizzy after a glass")["action"] == "escalate"


def test_ticket_questions_use_the_data_tool(store):
    r = run(store, ["NO"], q="did ticket volume change from 2025-03-15 to 2025-07-15")
    assert r["action"] == "data" and "+31.2%" in r["answer"]


def test_follow_up_is_rewritten_with_history(store):
    model = ScriptedModel(script=[AIMessage(s) for s in ["NO", GOOD, "YES", "what does the U5 refill plan cost", "NO", GOOD, "YES"]], calls=[])
    agent = build_agent(model, store, min_similarity=0.0, k=40)
    ask(agent, "what do C2 refills cost", thread="m")
    assert ask(agent, "and the U5?", thread="m")["standalone"] == "what does the U5 refill plan cost"


def test_verify_returns_the_document_sentence():
    assert verify({"source": "A", "quote": "it costs  $24"}, [{"source": "A", "text": "Intro here. It costs $24."}]) == ("A", "It costs $24.")


def test_grade_needs_the_right_source():
    q = {"kind": "answer", "gold": "A", "fact": ["x"]}
    assert not grade(q, {"action": "answer", "sources": ["B"], "answer": "x"})


def test_rebuilding_does_not_duplicate(store):
    before = store._collection.count()
    assert build_store(SpacyEmbeddings(), collection="tests")._collection.count() == before


def test_week_over_week_change():
    s = pd.Series([10] * 7 + [20] * 7, index=pd.date_range("2025-01-01", periods=14))
    assert "+70 (+100.0%)" in weekly_change(s, "2025-01-07", "2025-01-14")


@pytest.mark.parametrize("a,b", [("2025-01-14", "2025-01-07"), ("2024-01-01", "2025-01-07"), ("soon", "later")])
def test_bad_dates_explain_themselves(a, b):
    s = pd.Series([10] * 14, index=pd.date_range("2025-01-01", periods=14))
    assert "Change" not in weekly_change(s, a, b)
