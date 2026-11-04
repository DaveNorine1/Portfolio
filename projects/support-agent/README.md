# Support agent with LangChain, LangGraph, and Chroma

A conversational agent for a made-up water filter company. It answers only with approved sentences and citations, declines what the documents don't cover, sends health and safety questions to a person, pulls ticket trends from a data tool, follows up on earlier questions, and summarizes the conversation.

Code controls what the customer reads. Safety routing runs first, the model only picks a sentence, and code confirms that sentence is in the document before showing it.

## Results

Tested on Llama 3.1 (8B) through Ollama on a GPU, with `all-MiniLM-L6-v2` embeddings. Details are in `results/`.

| Test | Result |
|---|---|
| Answerable questions answered correctly | 16 of 20 |
| Unanswerable questions declined | 5 of 8 |
| Safety questions sent to a person | 12 of 12 |
| Right document ranked first, embeddings vs. BM25 | 85% vs. 70% |

It's ready for a supervised pilot, not for customers on its own. On 3 of the 8 unanswerable questions it quoted a real sentence that didn't answer the question, and it declined 3 answerable ones.

## Run it

```
pip install -r requirements.txt langchain-huggingface sentence-transformers
python -m spacy download en_core_web_md
python -m pytest
```

Start a local model in Ollama or LM Studio, set `LLM_BASE_URL` and `LLM_MODEL`, then run `python src/run_test.py` for the graded test or `python src/app.py` to chat. Set `LLM_PROVIDER=bedrock` to use AWS credentials from your normal config. Keys never go in code.
