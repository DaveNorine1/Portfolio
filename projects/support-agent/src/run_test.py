"""asks the agent every test question with a real model and saves the graded answers."""
import json
import os
from pathlib import Path
from agent import ask, build_agent, get_model, grade, summarize
from knowledge import build_store, get_embeddings

HERE = Path(__file__).resolve().parent.parent


def main():
    model = get_model()
    agent = build_agent(model, build_store(get_embeddings("minilm"), collection="test"))
    rows = []
    for i, q in enumerate(json.loads((HERE / "data/test_questions.json").read_text())):
        r = ask(agent, q["q"], thread=f"q{i}")
        rows.append({**q, **r, "passed": grade(q, r)})
        print("PASS" if rows[-1]["passed"] else "FAIL", q["q"], "->", r["answer"])
    score = {k: f'{sum(x["passed"] for x in rows if x["kind"] == k)} of {sum(x["kind"] == k for x in rows)}' for k in ("answer", "none", "escalate")}
    (HERE / "results/test_results.json").write_text(json.dumps({"model": os.getenv("LLM_MODEL"), "score": score, "questions": rows}, indent=1))
    print(score)


if __name__ == "__main__":
    main()
