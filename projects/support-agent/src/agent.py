"""a langgraph support agent where code, not the model, controls safety, citations, and what the customer reads."""
import difflib
import json
import re
import os
from typing import Annotated, TypedDict
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from knowledge import search
from tools import load_tickets, weekly_change

ESCALATE = re.compile(r"\b(sick|ill|nause\w*|vomit\w*|throwing up|rash\w*|diarrhea|fever|symptoms?|baby|babies|infant|newborn|toddler|formula|kids?|child\w*|pregnan\w*|nursing|immunocompromised|chemo\w*|dialysis|medical|doctor|medication|health|boil water|boil-water|contaminat\w*|discolou?red|chemicals?|gasoline|sewage|poison\w*)\b|\b(water|tap|faucet)\b.{0,30}\b(brown|red|yellow|black|orange)\b", re.I)

DECLINE = "I can't find that in the approved material. Please check with a lead."
HANDOFF = "This needs a person. Transferring you to the care specialist."
DATES = re.compile(r"\d{4}-\d{2}-\d{2}")

SAFETY = """A customer wrote to a water filter company. Reply YES if the message involves any of these, otherwise NO:
- health, sickness, symptoms, or medical conditions in a person or pet
- whether water is safe for a baby, child, pregnant or nursing person, or someone vulnerable
- contamination, health warnings, or boil notices
- water that suddenly smells, looks, or tastes wrong in a worrying way
Ordinary product noise, leaks, installation, billing, and shipping are NO.
Message: {q}
Reply with only YES or NO."""
REWRITE = """Rewrite the customer's latest message as one standalone question, using the earlier conversation to fill in what it refers to. Reply with only the question.
Conversation:
{history}
Latest message: {q}"""
ANSWER = """Find the sentence that best answers the customer. It's fine if the wording differs from the question, so long as the sentence addresses it. Reply with JSON only:
{{"found": true, "source": "<passage id>", "quote": "<the sentence, copied exactly>"}}
Reply {{"found": false}} only if no passage addresses the question, or the question is about a product, service, or topic the passages never mention.
Passages:
{passages}
Question: {q}"""
CHECK = """Does this sentence from a company document address the customer's question, even if indirectly? Reply NO only if it's about a different topic, or the question asks about a product or service the document doesn't mention.
Question: {q}
Document: {title}
Sentence: {quote}
Reply with only YES or NO."""


def get_model():
    provider = os.getenv("LLM_PROVIDER", "local")
    if provider == "bedrock":
        from langchain_aws import ChatBedrockConverse
        #credentials come from the normal aws config, never from code
        return ChatBedrockConverse(model=os.getenv("LLM_MODEL", "us.meta.llama3-1-70b-instruct-v1:0"), temperature=0.0)
    from langchain_openai import ChatOpenAI
    #lm studio and ollama both serve this api
    return ChatOpenAI(base_url=os.getenv("LLM_BASE_URL", "http://localhost:1234/v1"), api_key=os.getenv("LLM_API_KEY", "not-needed"),
                      model=os.getenv("LLM_MODEL", "local-model"), temperature=0.0)


class State(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    question: str
    action: str
    answer: str
    sources: list
    passages: list
    decline_reason: str


def yes(text):
    return text.strip().upper().startswith("YES")


def parse_json(text):
    match = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(match.group(0)) if match else {}
    except json.JSONDecodeError:
        return {}


def normalize(text):
    return re.sub(r"\s+", " ", re.sub(r"[^\w$%. ]", " ", text.lower())).strip(" .")


def sentences(text):
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", text) if x.strip()]


def verify(result, passages):
    #returns the approved sentence itself, so nothing the model wrote reaches the customer
    source = result.get("source")
    text = " ".join(p["text"] for p in passages if p["source"] == source)
    quote = normalize(str(result.get("quote", "")))
    if not text or not quote:
        return None
    best, score = None, 0.0
    for sentence in sentences(text):
        ratio = difflib.SequenceMatcher(None, quote, normalize(sentence)).ratio()
        if ratio > score:
            best, score = sentence, ratio
    #small copying slips are fine, a sentence that isn't in the document isn't
    return (source, best) if score >= 0.8 else None


def build_agent(model, store, min_similarity=0.25, series=None, k=4):
    series = load_tickets() if series is None else series
    as_json = model.bind(response_format={"type": "json_object"})

    def ask_text(prompt):
        return model.invoke(prompt).content

    def understand(state):
        latest = state["messages"][-1].content
        history = state["messages"][:-1]
        question = latest
        if history:
            lines = "\n".join(f"{m.type}: {m.content}" for m in history[-6:])
            question = ask_text(REWRITE.format(history=lines, q=latest)).strip()
        return {"question": question, "passages": [], "sources": []}

    def route(state):
        q = state["question"]
        #the rule catches obvious cases even if the model misses them
        if ESCALATE.search(q) or yes(ask_text(SAFETY.format(q=q))):
            return "escalate"
        if "ticket" in q.lower() and len(DATES.findall(q)) >= 2:
            return "tickets"
        return "retrieve"

    def escalate(state):
        return {"action": "escalate", "answer": HANDOFF, "messages": [AIMessage(HANDOFF)]}

    def tickets(state):
        a, b = DATES.findall(state["question"])[:2]
        text = weekly_change(series, a, b)
        return {"action": "data", "answer": text, "sources": ["ticket_volume"], "messages": [AIMessage(text)]}

    def retrieve(state):
        hits = search(store, state["question"], k=k, min_similarity=min_similarity)
        return {"passages": [{"source": d.metadata["source"], "text": d.page_content} for d, _ in hits]}

    def answer(state):
        q, passages = state["question"], state.get("passages", [])

        def declined(reason):
            return {"action": "decline", "answer": DECLINE, "sources": [], "decline_reason": reason, "messages": [AIMessage(DECLINE)]}

        if not passages:
            return declined("no_passages")

        def attempt(group):
            text = "\n".join(f'[{p["source"]}] {p["text"]}' for p in group)
            return parse_json(as_json.invoke(ANSWER.format(passages=text, q=q)).content)

        result = attempt(passages)
        #a second look at the best match alone, since long context makes small models give up
        if not result.get("found"):
            result = attempt(passages[:1])
        if not result.get("found"):
            return declined("model_not_found")
        checked = verify(result, passages)
        if not checked:
            return declined("quote_not_in_document")
        source, quote = checked
        title = next(p["text"].split(". ")[0] for p in passages if p["source"] == source)
        if not yes(ask_text(CHECK.format(q=q, title=title, quote=quote))):
            return declined("relevance_check")
        final = f"{quote} [{source}]"
        return {"action": "answer", "answer": final, "sources": [source], "decline_reason": "", "messages": [AIMessage(final)]}

    graph = StateGraph(State)
    graph.add_node("understand", understand)
    for name, fn in (("escalate", escalate), ("tickets", tickets), ("retrieve", retrieve), ("answer", answer)):
        graph.add_node(name, fn)
    graph.add_edge(START, "understand")
    graph.add_conditional_edges("understand", route, ["escalate", "tickets", "retrieve"])
    graph.add_edge("retrieve", "answer")
    for name in ("escalate", "tickets", "answer"):
        graph.add_edge(name, END)
    return graph.compile(checkpointer=MemorySaver())


def ask(agent, question, thread="default"):
    state = agent.invoke({"messages": [HumanMessage(question)]}, {"configurable": {"thread_id": thread}})
    return {"action": state["action"], "answer": state["answer"], "sources": state.get("sources", []), "standalone": state["question"], "decline_reason": state.get("decline_reason", "")}


def grade(q, result):
    #the action and citation come from code, so these checks are reliable
    if q["kind"] == "escalate":
        return result["action"] == "escalate"
    if q["kind"] == "none":
        return result["action"] == "decline"
    facts = q["fact"] if isinstance(q["fact"], list) else [q["fact"]]
    text = result["answer"].lower()
    return result["action"] == "answer" and q["gold"] in result["sources"] and any(f.lower() in text for f in facts)


def summarize(agent, model, thread="default"):
    state = agent.get_state({"configurable": {"thread_id": thread}}).values
    names = {"human": "Customer", "ai": "Agent"}
    turns = [f"{names[m.type]}: {m.content}" for m in state.get("messages", []) if m.type in ("human", "ai") and m.content]
    if not turns:
        return "Nothing to summarize yet."
    return model.invoke("Here is a transcript between a customer and a support agent. Write a summary of it in three sentences or fewer.\n\n" + "\n".join(turns)).content
