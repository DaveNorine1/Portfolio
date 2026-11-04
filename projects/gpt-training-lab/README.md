# GPT training and GPU benchmark

A decoder-only Transformer written from scratch in PyTorch, with the instrumentation to treat training as a GPU benchmark: causal attention, mixed precision, gradient accumulation, checkpointing, CUDA event timing, step-latency distributions, tokens per second, memory, and power.

**Status:** the code is complete and a full benchmark run is still to come. Results will be added here once that run is finished.

## Run it

Needs an NVIDIA GPU and a CUDA build of PyTorch.

```
pip install torch pandas matplotlib jupyter
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 notebooks/gpt_training_benchmark.ipynb
```

Metrics land in `notebooks/gpt_output/`. The default profile picks a model size from available VRAM and trains for 10,000 steps on Tiny Shakespeare.
