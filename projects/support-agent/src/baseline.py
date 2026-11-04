"""bm25 keyword search with a small glossary, the baseline for comparing retrieval."""
import math
import re
from collections import Counter
import numpy as np

STOP = set("a an the is are was were be do does did i my me we our you your it this that of in on at to for with and or can will should what how when where which who there have has get".split())


#the words customers use versus the words the documents use; a real team maintains this list
GLOSSARY = {"cartridge": "filter", "cartridges": "filter", "refill": "subscription plan", "refills": "subscription plan",
            "delivery": "shipping", "deliveries": "shipment", "hold": "pause", "stop": "cancel", "tap": "faucet",
            "trickling": "slow flow", "weak": "slow flow", "drip": "leak", "dripping": "leak", "pooling": "leak",
            "milky": "cloudy", "charcoal": "carbon", "crushed": "damaged", "smashed": "damaged", "broken": "damaged", "reach": "shipping", "discount": "business", "company": "business", "wear": "last",
            "husband": "authorized contact", "wife": "authorized contact", "spouse": "authorized contact", "someone": "authorized contact",
            "declined": "failed payment", "money": "refund", "set": "install", "swap": "change", "off": "third-party"}


def stem(t):
    #light stemmer so filters and filter match
    for suffix in ("ing", "ed", "es", "s"):
        if t.endswith(suffix) and len(t) - len(suffix) >= 3:
            return t[: -len(suffix)]
    return t


def tokens(text, expand=False):
    words = re.findall(r"[a-z0-9$]+", text.lower())
    if expand:
        words = words + [w for t in words for w in GLOSSARY.get(t, "").split()]
    return [stem(t) for t in words if t not in STOP]


class BM25Retriever:
    name = "BM25"
    def __init__(self, docs, k1=1.4, b=0.75):
        self.docs = [tokens(d["title"] + " " + d["text"]) for d in docs]
        self.len = np.array([len(d) for d in self.docs], float)
        self.avg = self.len.mean()
        self.tf = [Counter(d) for d in self.docs]
        df = Counter(t for d in self.docs for t in set(d))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        self.k1, self.b = k1, b
    def score(self, q):
        out = np.zeros(len(self.docs))
        for t in tokens(q, expand=True):
            if t not in self.idf:
                continue
            for i, tf in enumerate(self.tf):
                f = tf[t]
                if f:
                    out[i] += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
        return out
