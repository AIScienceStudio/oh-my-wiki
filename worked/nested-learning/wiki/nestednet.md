---
title: NestedNet
aliases: ["Nested Sparse Network", "NestedNet: Learning Nested Sparse Structures"]
created: "2026-04-07T04:00:00Z"
updated: "2026-04-07T04:00:00Z"
sources:
  - raw/arxiv_1712_03781.md
categories:
  - research
  - technology
tags:
  - model-compression
  - sparse-networks
  - resource-aware
  - predecessor
confidence: medium
word_count: 273
backlink_count: 1
status: active
---

# NestedNet

> A 2017 deep learning framework using n-in-1 nested sparse structures for resource-aware neural network architectures, distinct from the 2025 [[Nested Learning]] paradigm.

## Overview

NestedNet was proposed by Eunwoo Kim, Chanho Ahn, and Songhwai Oh in 2017 (arXiv:1712.03781). It is an earlier use of "nested" in a neural network context that addresses a different problem than the 2025 [[Nested Learning]] paradigm. While NL focuses on multi-level optimization and continual learning, NestedNet focuses on model compression and resource-aware deployment.

The core idea is an n-in-1 nested structure where a single neural network contains multiple sub-networks at different sparsity ratios. Higher-level (less sparse) networks share parameters with lower-level (more sparse) networks, enabling a single trained model to serve devices with diverse computational resources. This parameter sharing approach enables stable "nested learning" in the original sense -- training multiple sparsity levels simultaneously.

NestedNet supports multiple applications including adaptive deep compression, knowledge distillation, and coarse-to-fine hierarchical classification. The framework uses weight connection learning and channel/layer scheduling strategies for efficient training.

## Key Concepts

- **N-in-1 structure**: Multiple sub-networks with different sparsity ratios coexist in one network
- **Parameter sharing**: Higher-level networks share weights with lower-level ones
- **Resource-aware deployment**: A single model meets diverse hardware constraints
- **Adaptive compression**: Dynamically adjust model complexity based on available resources
- **Distinct from NL**: Uses "nested" to mean parameter-shared sub-networks, not multi-level optimization

## Connections

- [[Nested Learning]] -- the 2025 paradigm that shares the "nested" name but addresses different problems
- [[Catastrophic Forgetting and Continual Learning]] -- NestedNet's multi-task learning is tangentially related

## Sources

- `raw/arxiv_1712_03781.md` -- the original NestedNet paper (Kim et al., 2017)