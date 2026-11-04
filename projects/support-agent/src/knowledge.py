"""vector store over the approved documents. ids are stable, so rebuilding can't create duplicates."""
import json
from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

KB = Path(__file__).resolve().parent.parent / "data/knowledge_base.json"


class SpacyEmbeddings(Embeddings):
    #pretrained word vectors that run anywhere with no download at query time
    def __init__(self, model="en_core_web_md"):
        import spacy
        self.nlp = spacy.load(model, disable=["parser", "ner", "tagger", "lemmatizer", "attribute_ruler"])

    def _embed(self, text):
        doc = self.nlp(text)
        words = [t.vector for t in doc if t.has_vector and not t.is_stop and not t.is_punct]
        if not words:
            return doc.vector.tolist()
        return (sum(words) / len(words)).tolist()

    def embed_documents(self, texts):
        return [self._embed(t) for t in texts]

    def embed_query(self, text):
        return self._embed(text)


def get_embeddings(name="spacy"):
    if name == "minilm":
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", encode_kwargs={"normalize_embeddings": True})
    return SpacyEmbeddings()


def load_documents(path=KB):
    docs = json.loads(Path(path).read_text())
    return [Document(page_content=f'{d["title"]}. {d["text"]}', metadata={"source": d["id"], "title": d["title"]}) for d in docs]


def split_documents(docs, size=400, overlap=60):
    splitter = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap)
    chunks = splitter.split_documents(docs)
    seen = {}
    for c in chunks:
        n = seen[c.metadata["source"]] = seen.get(c.metadata["source"], 0) + 1
        c.metadata["chunk_id"] = f'{c.metadata["source"]}#{n}'
    return chunks


def build_store(embeddings, persist_directory=None, collection="larkfield"):
    store = Chroma(collection_name=collection, embedding_function=embeddings, persist_directory=persist_directory,
                   collection_metadata={"hnsw:space": "cosine"})
    chunks = split_documents(load_documents())
    #explicit ids mean a second run updates rows and never appends copies
    store.add_documents(chunks, ids=[c.metadata["chunk_id"] for c in chunks])
    return store


def search(store, query, k=3, min_similarity=0.0):
    #relevance is cosine similarity; weak matches are dropped rather than passed to the model
    hits = store.similarity_search_with_relevance_scores(query, k=k)
    return [(doc, score) for doc, score in hits if score >= min_similarity]
