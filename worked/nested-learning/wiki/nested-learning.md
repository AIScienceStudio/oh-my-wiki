---
title: Nested Learning
aliases: ["NL", "Nested Learning paradigm"]
created: "2026-04-07T04:00:00Z"
updated: "2026-04-07T04:00:00Z"
sources:
  - raw/arxiv_2512_24695.md
  - raw/research_google_blog_introducing-nested-learning-a-new-ml-paradigm-for-continual.md
  - raw/arxiviq_substack_com_p_nested-learning-the-illusion-of-deep.md
  - raw/itcanthink_substack_com_p_paper-notes-nested-learning.md
  - raw/www_marktechpost_com_2025_11_08_nested-learning-a-new-machine-learning-approach-.md
  - raw/research-notes.md
categories:
  - research
tags:
  - paradigm
  - optimization
  - continual-learning
  - associative-memory
confidence: high
word_count: 455
backlink_count: 11
status: active
---

# Nested Learning

> A new machine learning paradigm that represents models as nested, multi-level optimization problems, each with its own context flow and update frequency.

## Overview

Nested Learning (NL) was introduced by [[Ali Behrouz]] et al. from Google Research in a paper published at NeurIPS 2025 (arXiv:2512.24695). The central thesis is that any machine learning model, from a simple MLP to a complex Transformer, can be represented as a hierarchy of interconnected optimization problems. Rather than viewing a neural network as a single optimization problem (minimize loss over parameters), NL views it as multiple nested sub-problems, each compressing its own "context flow."

The paradigm bridges the gap between model architecture and optimization algorithm, arguing they are fundamentally the same concept at different levels. Architecture is described as an "illusion" -- both optimizers and neural networks are instances of associative memory. This perspective provides a new dimension for designing models, allowing components with deeper computational depth.

NL imposes ordering by update frequency: fast-updating parameters sit at inner levels, while slow-updating parameters form outer levels. This hierarchy, inspired by multi-timescale processes in the human brain (delta, theta, gamma waves), enables [[Catastrophic Forgetting and Continual Learning|continual learning]] as a first-class design concern. The paradigm yields three core contributions: [[Optimizers as Memory|deep optimizers]], a [[Continuum Memory System]], and the [[Hope Architecture]] as a proof-of-concept implementation.

## Key Concepts

- **Multi-level optimization**: Models decomposed into nested optimization problems at different update frequencies
- **Context flow**: Each component has its own information stream (data samples, gradients, states) from which it learns
- **Architecture as illusion**: Both model layers and optimizers are associative memory modules compressing context
- **Backpropagation as memory**: The training process itself maps data points to local error values, functioning as associative memory
- **Higher-order in-context learning**: More nesting levels unlock progressively higher-order learning capabilities

## Connections

- [[Hope Architecture]] -- the practical proof-of-concept architecture implementing NL principles
- [[Continuum Memory System]] -- NL's generalization of short/long-term memory into a spectrum
- [[Optimizers as Memory]] -- NL's reinterpretation of gradient-based optimizers as associative memory
- [[Dynamic Nested Hierarchies]] -- extension allowing autonomous adjustment of nesting structure
- [[Catastrophic Forgetting and Continual Learning]] -- the core problem NL addresses
- [[Self-Modifying Models]] -- NL enables models that learn their own update algorithms
- [[Titans Architecture]] -- direct predecessor to Hope, provides the foundation NL generalizes
- [[NestedNet]] -- earlier use of "nested" in neural networks (distinct from NL)

## External Links

- [Nested Learning: The Illusion of Deep Learning Architectures (arXiv:2512.24695)](https://arxiv.org/abs/2512.24695) — the foundational paper
- [Google Research Blog: Introducing Nested Learning](https://research.google/blog/introducing-nested-learning-a-new-ml-paradigm-for-continual-learning/) — official announcement
- [NeurIPS 2025 Poster](https://neurips.cc/virtual/2025/poster/116123) — conference page
- [OpenReview](https://openreview.net/forum?id=nbMeRvNb7A) — peer review discussion
- [ArXivIQ Analysis](https://arxiviq.substack.com/p/nested-learning-the-illusion-of-deep) — detailed technical explainer
- [Paper Notes by Chris Paxton](https://itcanthink.substack.com/p/paper-notes-nested-learning) — accessible walkthrough

## Sources

- `raw/arxiv_2512_24695.md` — the foundational NL paper (Behrouz et al., NeurIPS 2025)
- `raw/research_google_blog_introducing-nested-learning-a-new-ml-paradigm-for-continual.md` — official Google Research blog post
- `raw/arxiviq_substack_com_p_nested-learning-the-illusion-of-deep.md` — detailed ArXivIQ analysis
- `raw/itcanthink_substack_com_p_paper-notes-nested-learning.md` — Chris Paxton's accessible explanation
- `raw/www_marktechpost_com_2025_11_08_nested-learning-a-new-machine-learning-approach-.md` — MarkTechPost technical summary
- `raw/research-notes.md` — personal research notes on the paradigm