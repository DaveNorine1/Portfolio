"""compares sentence embeddings to the bm25 baseline on retrieval alone."""
import json
import sys
from pathlib import Path
import numpy as np
from baseline import BM25Retriever
from knowledge import build_store, get_embeddings, search

HERE = Path(__file__).resolve().parent.parent
docs = json.loads((HERE / "data/knowledge_base.json").read_text())
ids = [d["id"] for d in docs]
rows = [r for r in json.loads((HERE / "data/retrieval_questions.json").read_text()) if r["kind"] == "answer"]


def scores(ranks):
    ranks = np.array(ranks)
    return {"hit_at_1": float((ranks == 1).mean()), "hit_at_3": float((ranks <= 3).mean()), "mrr": float((1 / ranks).mean())}


def main(name="minilm"):
    store = build_store(get_embeddings(name), collection=f"eval_{name}")
    vector = []
    for r in rows:
        order = list(dict.fromkeys(d.metadata["source"] for d, _ in search(store, r["q"], k=len(ids) * 2)))
        vector.append(order.index(r["gold"]) + 1 if r["gold"] in order else len(ids))
    b = BM25Retriever(docs)
    keyword = [[ids[i] for i in np.argsort(-b.score(r["q"]))].index(r["gold"]) + 1 for r in rows]
    print(json.dumps({"questions": len(rows), "bm25": scores(keyword), "vector": scores(vector)}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "minilm")
