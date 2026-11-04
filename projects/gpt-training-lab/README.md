# GPT training and GPU benchmark

A decoder-only Transformer written from scratch in PyTorch, with the instrumentation to treat training as a GPU benchmark: causal attention, mixed precision, gradient accumulation, checkpointing, CUDA event timing, step-latency distributions, tokens per second, memory, and power.

## Results

Run on an NVIDIA A100 (80GB) in Google Colab: a 202M-parameter model, 16 layers, BF16 mixed precision, 10,000 optimizer steps on Tiny Shakespeare, in about 76 minutes. Metrics are in `results/`.

| Measure | Result |
|---|---|
| Training throughput | about 113,000 tokens per second |
| Median optimizer step | 435 ms (standard deviation 2.7 ms) |
| Tokens processed | 491.5 million |
| Mean GPU utilization | 98% |
| Peak VRAM | 10.7 GB of 79 GB |
| Best validation loss | 1.58, at step 750 |
| Final loss | training 0.03, validation 4.69 |

The hardware numbers are the point of this run. The model is far too large for this small dataset and overfits almost immediately, so it's a stress test and not a useful text generator. For real generation, I'd stop near step 750, use a smaller model, or train on more data.

## Run it

Needs an NVIDIA GPU and a CUDA build of PyTorch.

```
pip install torch pandas matplotlib jupyter
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 notebooks/gpt_training_benchmark.ipynb
```

Metrics land in `notebooks/gpt_output/`. The default profile picks a model size from available VRAM and trains for 10,000 steps on Tiny Shakespeare.
