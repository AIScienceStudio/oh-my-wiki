---
title: Catastrophic Forgetting and Continual Learning
aliases: ["Catastrophic Forgetting", "Continual Learning", "Lifelong Learning"]
created: "2026-04-07T04:00:00Z"
updated: "2026-04-07T04:00:00Z"
sources:
  - raw/continual-learning-background.md
  - raw/arxiv_2512_24695.md
  - raw/itcanthink_substack_com_p_paper-notes-nested-learning.md
  - raw/research_google_blog_introducing-nested-learning-a-new-ml-paradigm-for-continual.md
categories:
  - research
tags:
  - catastrophic-forgetting
  - continual-learning
  - memory
  - ewc
  - experience-replay
confidence: high
word_count: 449
backlink_count: 5
status: active
---

# Catastrophic Forgetting and Continual Learning

> The fundamental challenge that neural networks lose performance on previously learned tasks when trained on new data, and the field of research seeking to overcome it.

## Overview

Catastrophic forgetting is one of the most persistent limitations in deep learning. When a neural network trained on task A is subsequently trained on task B, it tends to lose its proficiency on task A. This problem is especially acute for real-world deployment scenarios, such as robotics, where models must learn continuously from shifting data distributions without periodic full retraining.

As Chris Paxton illustrates: imagine a robot trained to pick up cups that is then trained to pick up toys. After training on toys, the robot can no longer properly handle cups. The naive solution -- training on all datasets simultaneously -- does not scale as datasets accumulate. Traditional approaches to combat forgetting include Elastic Weight Consolidation (EWC), which penalizes changes to important weights; Progressive Neural Networks, which add new capacity per task but do not scale; Experience Replay, which stores and replays old examples at a memory cost; and PackNet, which prunes and freezes subnetworks per task.

The [[Nested Learning]] paradigm offers a fundamentally different approach. Rather than treating continual learning as an afterthought (a patch applied to an existing architecture), NL designs the entire model around multi-timescale learning. The [[Continuum Memory System]] naturally handles different retention periods, with slow-updating outer blocks anchoring knowledge and fast-updating inner blocks adapting to new information. The Google Research blog describes current LLMs as suffering from "anterograde amnesia" -- they cannot form new lasting memories after pre-training. The [[Hope Architecture]] is designed to overcome this limitation.

## Key Concepts

- **Catastrophic forgetting (CF)**: Learning new tasks overwrites weights needed for old tasks
- **Elastic Weight Consolidation (EWC)**: Penalizes changes to weights deemed important for previous tasks
- **Progressive Neural Networks**: Adds new network capacity for each new task (does not scale)
- **Experience Replay**: Stores and replays examples from previous tasks (has memory cost)
- **PackNet**: Prunes and freezes subnetworks dedicated to each task
- **Anterograde amnesia analogy**: Current LLMs cannot form new lasting memories, only use pre-trained weights plus context window

## Connections

- [[Nested Learning]] -- proposes a paradigm-level solution to catastrophic forgetting
- [[Continuum Memory System]] -- the NL mechanism for multi-timescale memory retention
- [[Hope Architecture]] -- demonstrates improved continual learning in benchmarks
- [[Dynamic Nested Hierarchies]] -- extends NL to dynamically adapt to distribution shifts

## Sources

- `raw/continual-learning-background.md` -- survey of traditional approaches and how NL differs
- `raw/arxiv_2512_24695.md` -- NL paper's framing of continual learning
- `raw/itcanthink_substack_com_p_paper-notes-nested-learning.md` -- robotics-focused illustration of the forgetting problem
- `raw/research_google_blog_introducing-nested-learning-a-new-ml-paradigm-for-continual.md` -- anterograde amnesia analogy