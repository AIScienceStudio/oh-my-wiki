---
type: note
title: "Background: Continual Learning and Catastrophic Forgetting"
captured_at: 2026-04-07T00:00:00Z
contributor: "me"
---

# Background: Continual Learning and Catastrophic Forgetting

## The Problem

Neural networks suffer from catastrophic forgetting — when trained on new data, they lose performance on previously learned tasks. This is a fundamental limitation for deploying models in real-world scenarios where data distributions shift over time.

## Traditional Approaches

- **Elastic Weight Consolidation (EWC)**: Penalizes changes to important weights
- **Progressive Neural Networks**: Add new capacity for each task (doesn't scale)
- **Experience Replay**: Store and replay old examples (memory cost)
- **PackNet**: Prune and freeze subnetworks per task

## Why Nested Learning Is Different

NL doesn't treat continual learning as an afterthought. Instead, the entire model architecture is designed around the idea that learning happens at multiple timescales simultaneously. The continuum memory system naturally handles different retention periods.

## Key People in Continual Learning

- **Ali Behrouz** — Google Research, author of Nested Learning
- **Meisam Razaviyayn** — USC, co-author
- **Peilin Zhong** — Google Research, co-author
- **Vahab Mirrokni** — Google Research, co-author
- **Jürgen Schmidhuber** — pioneered self-referential learning, precursor to NL ideas
