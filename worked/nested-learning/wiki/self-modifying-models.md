---
title: Self-Modifying Models
aliases: ["Self-Referential Learning", "Self-Modifying Networks"]
created: "2026-04-07T04:00:00Z"
updated: "2026-04-07T04:00:00Z"
sources:
  - raw/arxiv_2512_24695.md
  - raw/research-notes.md
  - raw/arxiviq_substack_com_p_nested-learning-the-illusion-of-deep.md
  - raw/continual-learning-background.md
categories:
  - research
  - ideas
tags:
  - self-modification
  - meta-learning
  - schmidhuber
  - learning-to-learn
confidence: medium
word_count: 395
backlink_count: 6
status: active
---

# Self-Modifying Models

> Models that learn their own update algorithms, enabling them to adapt their learning process in response to data, a capability central to the [[Nested Learning]] paradigm.

## Overview

Self-modifying models are systems that can optimize their own learning procedures rather than relying on fixed, externally specified update rules. In the context of [[Nested Learning]], this means a model that learns not just a task mapping but also how to update itself -- learning to learn. The [[Hope Architecture]] is the primary example: it is described as a "self-referential learning module" that modifies its own update rules at test time.

The concept has deep historical roots. Jurgen Schmidhuber pioneered self-referential learning in the 1990s, proposing neural networks that could modify their own weights. The [[Nested Learning]] framework formalizes and generalizes this idea by treating the optimizer (the update rule) as another level of associative memory that can itself be learned. When the optimizer is a neural network (as in [[Deep Momentum Gradient Descent]]), the model genuinely learns how to learn.

Self-modification connects to several related fields: meta-learning (learning to learn), Neural Architecture Search (models modify their own structure), and the work of Vitaly Vanchurin et al. on evolution as multilevel learning. [[Dynamic Nested Hierarchies]] takes self-modification further by allowing models to autonomously adjust not just update rules but the entire nesting structure -- the number of levels, their topology, and their update frequencies.

## Key Concepts

- **Self-referential learning**: A model that can write its own update rules (Schmidhuber, 1990s)
- **Learning to learn**: The outer optimization loop learns how the inner loop should update
- **Test-time adaptation**: Self-modifying models can adapt during inference, not just training
- **Unbounded in-context learning**: Self-modification enables in-context learning at arbitrary depth
- **Meta-learning connection**: NL's self-modification generalizes the meta-learning framework

## Connections

- [[Nested Learning]] -- provides the theoretical framework for self-modification
- [[Hope Architecture]] -- the self-referential learning module implementing self-modification
- [[Deep Momentum Gradient Descent]] -- makes the optimizer learnable, a form of self-modification
- [[Dynamic Nested Hierarchies]] -- extends self-modification to the nesting structure itself
- [[Open Questions in Nested Learning]] -- computational overhead of self-modification is an open question

## Sources

- `raw/arxiv_2512_24695.md` -- self-modifying learning module as core contribution
- `raw/research-notes.md` -- connections to Schmidhuber and meta-learning
- `raw/arxiviq_substack_com_p_nested-learning-the-illusion-of-deep.md` -- Hope as self-modifying Titans
- `raw/continual-learning-background.md` -- Schmidhuber's pioneering role