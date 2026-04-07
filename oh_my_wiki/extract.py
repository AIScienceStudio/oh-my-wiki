"""Extraction schema, validation, and prompt templates.

The actual extraction is done by the host LLM via skill.md orchestration.
This module provides: schema validation, prompt builders, and cache integration.
"""
from __future__ import annotations

import json
from pathlib import Path

from oh_my_wiki.cache import load_cached, save_cached


# ---------------------------------------------------------------------------
# Extraction schema
# ---------------------------------------------------------------------------

EXTRACTION_SCHEMA = {
    "required": ["source_file", "topics", "entities", "summary", "suggested_titles"],
    "optional": ["suggested_categories", "key_claims", "image_description", "source_hash"],
    "topic_fields": ["name", "relevance"],
    "entity_fields": ["name", "type"],
    "entity_types": ["person", "tool", "concept", "organization", "place", "event", "media"],
    "relevance_values": ["primary", "secondary"],
}


def validate_extraction(data: dict) -> list[str]:
    """Validate an extraction dict against the schema.

    Returns a list of error messages (empty = valid).
    """
    errors: list[str] = []
    for field in EXTRACTION_SCHEMA["required"]:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if "topics" in data:
        if not isinstance(data["topics"], list):
            errors.append("'topics' must be a list")
        else:
            for i, topic in enumerate(data["topics"]):
                if not isinstance(topic, dict):
                    errors.append(f"topics[{i}] must be a dict")
                elif "name" not in topic:
                    errors.append(f"topics[{i}] missing 'name'")

    if "entities" in data:
        if not isinstance(data["entities"], list):
            errors.append("'entities' must be a list")
        else:
            for i, entity in enumerate(data["entities"]):
                if not isinstance(entity, dict):
                    errors.append(f"entities[{i}] must be a dict")
                elif "name" not in entity:
                    errors.append(f"entities[{i}] missing 'name'")

    if "suggested_titles" in data:
        if not isinstance(data["suggested_titles"], list):
            errors.append("'suggested_titles' must be a list")

    return errors


# ---------------------------------------------------------------------------
# Extraction cache helpers
# ---------------------------------------------------------------------------

def get_cached_extraction(file_path: str, root: Path = Path(".")) -> dict | None:
    """Get cached extraction for a file, or None."""
    return load_cached(Path(file_path), root)


def save_extraction(file_path: str, extraction: dict, root: Path = Path(".")) -> None:
    """Validate and save extraction to cache."""
    errors = validate_extraction(extraction)
    if errors:
        raise ValueError(f"Invalid extraction for {file_path}: {'; '.join(errors)}")
    save_cached(Path(file_path), extraction, root)


def save_extractions_batch(extractions: list[dict], root: Path = Path(".")) -> int:
    """Save a batch of extractions, keyed by source_file. Returns count saved."""
    saved = 0
    for ext in extractions:
        src = ext.get("source_file", "")
        if src and Path(src).exists():
            try:
                save_extraction(src, ext, root)
                saved += 1
            except (ValueError, OSError):
                continue
    return saved


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT = """\
You are extracting structured information from raw source files for a personal knowledge wiki.

For each file below, produce a JSON object with these fields:

- source_file: the file path (as given)
- topics: [{{"name": "Topic Name", "relevance": "primary"|"secondary"}}]
  - "primary" = the file is mainly about this topic
  - "secondary" = the topic is mentioned but not the focus
- entities: [{{"name": "Entity Name", "type": "person"|"tool"|"concept"|"organization"|"place"|"event"|"media"}}]
  - Extract actual names of people, tools, companies, places, events
- summary: One paragraph (2-4 sentences) summarizing the key information
- suggested_titles: 2-5 article titles this source could contribute to
- suggested_categories: Categories from [people, projects, research, media, personal, technology, places, ideas]
- key_claims: 3-10 specific factual claims, insights, or quotes worth preserving

Be specific. Extract actual names, dates, numbers, and quotes — not vague descriptions.
For images, describe what you see and extract any visible text.

Return a JSON array with one object per file.

Files to process:

{file_contents}
"""

PLANNING_PROMPT = """\
You are planning a wiki compilation. Given extractions from raw source files and the current wiki state, decide which articles to create, update, or skip.

Current wiki has {article_count} articles. Existing article titles and one-line summaries:

{index_summary}

Rules:
1. Prefer UPDATING existing articles over creating duplicates
2. One article per distinct topic — don't merge unrelated topics
3. Create stubs for forward references with no source material
4. Minimum ~100 words of source material to justify a standalone article
5. Flag conflicting information between sources

Extractions to process:

{extractions_json}

Output a JSON object with:
{{
  "articles": [
    {{
      "title": "Article Title",
      "action": "create"|"update"|"stub",
      "sources": ["raw/file.md"],  // for create
      "new_sources": ["raw/file.md"],  // for update
      "categories": ["category"],
      "outline": "Brief outline of what to write",
      "reason": "Why this action"  // for update/stub
    }}
  ],
  "no_action": [
    {{"source": "raw/file.md", "reason": "Why no article needed"}}
  ]
}}
"""

ARTICLE_WRITING_PROMPT = """\
You are writing an article for a personal knowledge wiki. Write in clear, informative prose.

Title: {title}
Categories: {categories}
Outline: {outline}

Source material:
{source_content}

Existing articles you can link to with [[wikilinks]]:
{existing_titles}

Format the article as markdown with YAML frontmatter:

---
title: "{title}"
aliases: []
created: {timestamp}
updated: {timestamp}
sources:
{sources_yaml}
categories:
{categories_yaml}
tags: []
confidence: {confidence}
word_count: 0
backlink_count: 0
status: active
---

# {title}

> One-line summary (blockquote)

## Overview
2-3 paragraphs compiled from sources.

## Key Concepts
(if technical/research — bulleted definitions)

## Connections
- [[Related Article]] — brief description of relationship

## Sources
- `raw/file.md` — brief description

## Notes
(optional: observations, cross-references discovered during compilation)

Write for a knowledgeable reader. Use [[wikilinks]] naturally in the text.
"""

ARTICLE_UPDATE_PROMPT = """\
You are updating an existing wiki article with new information.

Existing article:
{existing_article}

New source material:
{new_source_content}

Reason for update: {reason}

Existing articles you can link to:
{existing_titles}

Instructions:
1. Integrate new information into existing sections (don't just append)
2. Add new Key Concepts if the source introduces them
3. Add new [[wikilinks]] in the Connections section if relevant
4. Update the Sources section with the new source
5. Update the 'updated' timestamp to {timestamp}
6. If information conflicts, add a ## Conflicts section
7. Preserve any existing ## User Notes section unchanged

Output the complete updated article with frontmatter.
"""


def build_extraction_prompt(files: list[tuple[str, str]]) -> str:
    """Build an extraction prompt for a batch of files.

    files: list of (file_path, file_content) tuples.
    """
    parts = []
    for path, content in files:
        parts.append(f"### File: {path}\n\n{content[:8000]}\n")
    return EXTRACTION_PROMPT.format(file_contents="\n---\n\n".join(parts))


def build_planning_prompt(
    extractions: list[dict],
    existing_articles: list[dict],
) -> str:
    """Build a planning prompt."""
    index_lines = []
    for art in existing_articles:
        title = art.get("title", "")
        summary = art.get("summary", "")
        cats = ", ".join(art.get("categories", []))
        index_lines.append(f"- {title} ({cats}) — {summary}")

    return PLANNING_PROMPT.format(
        article_count=len(existing_articles),
        index_summary="\n".join(index_lines) if index_lines else "(empty wiki — first compile)",
        extractions_json=json.dumps(extractions, indent=2),
    )
