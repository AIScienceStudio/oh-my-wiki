---
title: Titans Architecture
aliases: ["Titans"]
created: "2026-04-07T04:00:00Z"
updated: "2026-04-07T04:00:00Z"
sources:
  - raw/arxiviq_substack_com_p_nested-learning-the-illusion-of-deep.md
  - raw/www_marktechpost_com_2025_11_08_nested-learning-a-new-machine-learning-approach-.md
  - raw/itcanthink_substack_com_p_paper-notes-nested-learning.md
categories:
  - research
  - technology
tags:
  - architecture
  - long-term-memory
  - sequence-model
  - predecessor
confidence: medium
word_count: 359
backlink_count: 4
status: active
---

# Titans Architecture

> A long-term memory architecture introducing a neural memory module that learns to memorize surprising events at test time, serving as the direct predecessor to the [[Hope Architecture]].

## Overview

Titans is a sequence model architecture developed by [[Ali Behrouz]] and collaborators at Google Research, prior to the [[Nested Learning]] paper. Its key innovation is a dedicated Long-Term Memory Module -- a neural memory that learns to update itself during test time by memorizing "surprising" events (inputs with high prediction error). This module helps attention attend to tokens far beyond the standard context window.

Titans operates with two levels of parameter update: the standard model weights (slow, updated during training) and the long-term memory module (fast, updated at inference). This two-level structure yields what the [[Nested Learning]] framework would later formalize as first-order in-context learning.

The [[Hope Architecture]] is described as a direct evolution of Titans. While Titans introduced the concept of a single specialized neural memory module, [[Nested Learning]] provides the theoretical framework explaining why such systems work and generalizes them. Hope extends Titans by adding self-modification capability and replacing the single long-term memory with a full [[Continuum Memory System]] operating at multiple frequencies. The Titans team promised to release code on GitHub but had not yet done so as of the NL paper's publication.

## Key Concepts

- **Neural Long-Term Memory Module**: Learns to memorize surprising events during inference
- **Test-time learning**: Memory updates at inference, not just training
- **Two-level updates**: Training weights (slow) + memory module (fast)
- **First-order in-context learning**: The two-level structure enables basic in-context learning
- **Attention augmentation**: Memory module helps attention reach tokens beyond the context window

## Connections

- [[Hope Architecture]] -- the successor that extends Titans with self-modification and CMS
- [[Nested Learning]] -- the theoretical framework that explains and generalizes Titans
- [[Continuum Memory System]] -- replaces Titans' single memory module with multi-frequency memory
- [[Ali Behrouz]] -- lead researcher on both Titans and NL

## Sources

- `raw/arxiviq_substack_com_p_nested-learning-the-illusion-of-deep.md` -- describes Hope as a direct evolution of Titans
- `raw/www_marktechpost_com_2025_11_08_nested-learning-a-new-machine-learning-approach-.md` -- Hope built as a variant of Titans
- `raw/itcanthink_substack_com_p_paper-notes-nested-learning.md` -- mentions Titans as predecessor