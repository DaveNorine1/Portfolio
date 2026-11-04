"""chat interface. start a local model first, then run: python src/app.py"""
import os
import gradio as gr
from agent import ask, build_agent, get_model, summarize
from knowledge import build_store, get_embeddings

model = get_model()
agent = build_agent(model, build_store(get_embeddings(os.getenv("EMBEDDINGS", "minilm"))))


def respond(message, history):
    return ask(agent, message, thread="ui")["answer"]


with gr.Blocks(title="Larkfield support agent") as demo:
    gr.ChatInterface(respond, examples=["How much is the C2 refill plan?", "Did ticket volume change between 2025-03-15 and 2025-07-15?", "My toddler has a rash from the water"])
    button = gr.Button("Summarize this conversation")
    summary = gr.Markdown()
    button.click(lambda: summarize(agent, model, thread="ui"), outputs=summary)

if __name__ == "__main__":
    demo.launch()
