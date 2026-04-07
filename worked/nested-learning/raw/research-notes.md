---
type: note
title: "Research Notes on Nested Learning"
captured_at: 2026-04-07T00:00:00Z
contributor: "me"
---

# Research Notes on Nested Learning

## Why This Matters

Nested Learning (NL) by Ali Behrouz et al. is potentially a paradigm shift in how we think about deep learning. Instead of viewing a neural network as a single optimization problem (minimize loss over parameters), NL views it as a hierarchy of nested optimization problems, each with its own context flow.

## Key Insight: Optimizers as Memory

The most surprising claim: standard optimizers like Adam and SGD with Momentum are actually associative memory modules. They compress gradients the same way attention compresses context. This reframes the entire training process.

## Hope Architecture

Hope is the practical application — a self-modifying recurrent model that:
- Learns its own update algorithm
- Has a Continuum Memory System (CMS) that generalizes short/long-term memory
- Can do continual learning without catastrophic forgetting
- Scales to longer contexts than transformers

## Questions to Investigate

1. How does Hope compare to Mamba and other state-space models?
2. What's the computational overhead of nested optimization?
3. Can NL be applied to existing transformer architectures retroactively?
4. What are the practical limits of the continuum memory system?

## Connections to Other Work

- Relates to meta-learning (learning to learn)
- Connects to Neural Architecture Search (the model modifies its own structure)
- Reminiscent of Schmidhuber's self-referential learning from the 1990s
- The bilevel optimization view connects to hyperparameter optimization
