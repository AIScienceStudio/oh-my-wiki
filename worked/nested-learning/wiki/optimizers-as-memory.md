---
title: Optimizers as Memory
aliases: ["Optimizers as Associative Memory", "Deep Optimizers"]
created: "2026-04-07T04:00:00Z"
updated: "2026-04-07T04:00:00Z"
sources:
  - raw/arxiv_2512_24695.md
  - raw/arxiviq_substack_com_p_nested-learning-the-illusion-of-deep.md
  - raw/itcanthink_substack_com_p_paper-notes-nested-learning.md
  - raw/www_marktechpost_com_2025_11_08_nested-learning-a-new-machine-learning-approach-.md
  - raw/research-notes.md
categories:
  - research
  - ideas
tags:
  - optimizers
  - associative-memory
  - adam
  - sgd
  - gradient-descent
confidence: high
word_count: 433
backlink_count: 5
status: active
---

# Optimizers as Memory

> The insight that standard gradient-based optimizers like Adam and SGD with Momentum are associative memory modules that compress gradient information, not merely update rules.

## Overview

Perhaps the most surprising contribution of the [[Nested Learning]] paradigm is the reinterpretation of standard optimization algorithms. [[Ali Behrouz]] et al. demonstrate that gradient descent with momentum is not a simple update rule but a two-level nested optimization process. The momentum term itself is an associative memory module that learns to compress the history of gradients.

Formally, standard momentum can be written as a linear associative memory over past gradients trained with a dot product similarity objective. This internal objective produces a Hebbian-like update rule that does not model dependencies between data samples. The [[Nested Learning]] authors replaced this similarity objective with an L2 regression loss over gradient features, which yields an update rule that better manages limited memory capacity and better memorizes gradient sequences.

This reframing has profound implications: it means that the distinction between "model" and "optimizer" is artificial. Both are associative memory systems operating at different levels of the optimization hierarchy. The optimizer just happens to be a simpler, linear memory operating on gradient context rather than data context. This insight directly motivates [[Deep Momentum Gradient Descent]], which replaces the linear memory with an MLP to create a genuinely deep optimizer.

## Key Concepts

- **Momentum as associative memory**: The momentum term m(t+1) in SGD can be seen as solving its own inner optimization problem
- **Adam as memory**: Adam's first and second moment estimates are memory modules compressing gradient statistics
- **Linear vs. deep memory**: Standard optimizers use linear (shallow) memory; NL proposes replacing this with neural (deep) memory
- **Hebbian-like updates**: The dot-product similarity in standard momentum produces Hebbian update rules
- **Architecture-optimizer unification**: Both model layers and optimizers are the same fundamental concept -- associative memory at different levels

## Connections

- [[Nested Learning]] -- the paradigm that produced this insight
- [[Deep Momentum Gradient Descent]] -- the practical application: replacing linear optimizer memory with neural memory
- [[Hope Architecture]] -- uses deep optimizers internally
- [[Self-Modifying Models]] -- optimizer-as-memory enables models that learn their own update rules
- [[Continuum Memory System]] -- applies the same associative memory principle at the architecture level

## Sources

- `raw/arxiv_2512_24695.md` -- formal proof that optimizers are associative memory modules
- `raw/arxiviq_substack_com_p_nested-learning-the-illusion-of-deep.md` -- explanation of deep optimizers and DMGD
- `raw/itcanthink_substack_com_p_paper-notes-nested-learning.md` -- Chris Paxton's accessible framing of this insight
- `raw/www_marktechpost_com_2025_11_08_nested-learning-a-new-machine-learning-approach-.md` -- technical details on L2 regression objective
- `raw/research-notes.md` -- notes on this as the key insight of NL