---
title: Deep Momentum Gradient Descent
aliases: ["DMGD", "Deep Optimizers"]
created: "2026-04-07T04:00:00Z"
updated: "2026-04-07T04:00:00Z"
sources:
  - raw/arxiviq_substack_com_p_nested-learning-the-illusion-of-deep.md
  - raw/www_marktechpost_com_2025_11_08_nested-learning-a-new-machine-learning-approach-.md
  - raw/arxiv_2512_24695.md
categories:
  - research
  - technology
tags:
  - optimizer
  - gradient-descent
  - deep-memory
  - muon
confidence: high
word_count: 350
backlink_count: 3
status: active
---

# Deep Momentum Gradient Descent

> An optimizer design that replaces the linear momentum memory in standard gradient descent with a multi-layer perceptron, making the optimizer itself a deep learning model.

## Overview

Deep Momentum Gradient Descent (DMGD) is a concrete application of the [[Optimizers as Memory]] insight from the [[Nested Learning]] paradigm. Once standard momentum is recognized as a linear associative memory that compresses gradient history, the natural next step is to replace it with a more powerful, non-linear memory -- specifically, an MLP.

In standard SGD with Momentum, the momentum term uses a dot product similarity objective to produce a Hebbian-like update rule. DMGD replaces this with an L2 regression loss over gradient features and generalizes the momentum memory from a linear map to an MLP. The result is an optimizer capable of learning complex, non-linear dynamics of the loss landscape. The momentum state is produced by a neural memory and can pass through non-linear functions such as Newton-Schulz orthogonalization.

A notable result is that DMGD recovers the Muon optimizer as a special case, providing theoretical grounding for an optimizer that was previously motivated heuristically. This demonstrates the unifying power of the [[Nested Learning]] framework -- existing innovations in optimization can be understood as specific instances of deep associative memory over gradients.

## Key Concepts

- **MLP replaces linear momentum**: The optimizer's memory becomes a deep neural network
- **L2 regression objective**: Replaces dot product similarity for better gradient memorization
- **Muon as special case**: The Muon optimizer is recovered within the DMGD framework
- **Newton-Schulz orthogonalization**: A non-linear post-processing step applicable to the neural momentum
- **Optimizer as deep model**: The training procedure itself becomes a learnable deep network

## Connections

- [[Optimizers as Memory]] -- the theoretical insight DMGD implements
- [[Nested Learning]] -- the paradigm motivating deep optimizers
- [[Hope Architecture]] -- uses DMGD-style deep optimizers internally
- [[Self-Modifying Models]] -- DMGD enables the optimizer to be part of the learned system

## Sources

- `raw/arxiviq_substack_com_p_nested-learning-the-illusion-of-deep.md` -- detailed explanation of DMGD
- `raw/www_marktechpost_com_2025_11_08_nested-learning-a-new-machine-learning-approach-.md` -- Muon recovery result and technical details
- `raw/arxiv_2512_24695.md` -- original formulation