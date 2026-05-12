#!/usr/bin/env python3
"""
Docs PR Review Bot
==================
Validates DITA documentation files changed in a pull request against:
  - DITA structural rules (element nesting, required attributes, required elements)
  - IBM Style Guide rules (plain language, word choice, voice, tense)
  - General grammar and style rules

Posts a structured review comment on the GitHub PR with all findings.

Environment variables required:
  GITHUB_TOKEN       - GitHub Actions token
  PR_NUMBER          - Pull request number
  REPO               - Repository in "owner/repo" format
  CHANGED_FILES_PATH - Path to file listing changed DITA files (one per line)
  BOT_CONFIG_PATH    - (optional) Path to JSON config overrides
"""

import os
import re
import sys
import json
import textwrap
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import urllib.request
import urllib.error


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    """A single validation finding."""
    file: str
    line: int
    level: str          # "error" | "warning" | "suggestion"
    category: str       # "dita-structure" | "ibm-style" | "grammar"
    rule_id: str        # short identifier, e.g. "DITA001"
    message: str
    suggestion: str = ""
    confidence: str = "medium"  # "high" | "medium" | "low"

    @property
    def severity_icon(self) -> str:
        return {"error": "🔴", "warning": "🟡", "suggestion": "🔵"}.get(self.level, "⚪")


@dataclass
class PlanStep:
    """A single planner step for the agent loop."""
    file: str
    checks: List[str]
    risk: int


# ---------------------------------------------------------------------------
# DITA structural validation
# ---------------------------------------------------------------------------

# DITA topic types and their expected body elements
TOPIC_TYPE_BODIES = {
    "concept":   "conbody",
    "task":      "taskbody",
    "reference": "refbody",
    "topic":     "body",
}

# Elements that MUST carry an id attribute
REQUIRE_ID = {"concept", "task", "reference", "topic", "section", "fig", "table"}

# Elements that must NOT be empty (must have text or child elements)
MUST_NOT_BE_EMPTY = {"cmd", "title", "shortdesc", "p", "li", "dt", "dd"}

# Known inline DITA elements (used to detect block elements in inline context)
INLINE_ELEMENTS = {
    "ph", "b", "i", "u", "tt", "codeph", "varname", "filepath", "uicontrol",
    "menucascade", "userinput", "systemoutput", "msgph", "term", "xref",
    "cite", "q", "tm", "image",
}

# Block elements that should NOT appear inside inline elements
BLOCK_IN_INLINE_FORBIDDEN = {"p", "ul", "ol", "sl", "dl", "table", "fig", "note", "section"}


def _line_number_for_element(source: str, tag_name: str, occurrence: int = 1) -> int:
    """Best-effort: find approximate line number for a tag occurrence in source text."""
    pattern = re.compile(rf"<{re.escape(tag_name)}[\s/>]", re.IGNORECASE)
    count = 0
    for i, line in enumerate(source.splitlines(), start=1):
        if pattern.search(line):
            count += 1
            if count >= occurrence:
                return i
    return 1


def _element_line(source_lines: List[str], tag: str) -> int:
    """Return 1-based line number of first occurrence of opening tag in source."""
    pattern = re.compile(rf"<{re.escape(tag)}[\s/>]", re.IGNORECASE)
    for i, line in enumerate(source_lines, start=1):
        if pattern.search(line):
            return i
    return 1


def validate_dita(filepath: str) -> List[Finding]:
    """
    Parse and validate a DITA file against structural rules.
    Returns a list of Finding objects.
    """
    findings: List[Finding] = []
    path = Path(filepath)

    if not path.exists():
        return findings

    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings

    source_lines = source.splitlines()

    # Strip DOCTYPE and processing instructions so ET can parse cleanly
    cleaned = re.sub(r"<\?[^?]+\?>", "", source)
    cleaned = re.sub(r"<!DOCTYPE[^>]*>", "", cleaned)
    cleaned = re.sub(r"<!--.*?-->", "", cleaned, flags=re.DOTALL)

    try:
        root = ET.fromstring(cleaned)
    except ET.ParseError as exc:
        line_no = exc.position[0] if exc.position else 1
        findings.append(Finding(
            file=filepath, line=line_no, level="error",
            category="dita-structure", rule_id="DITA000",
            message=f"XML parse error: {exc}",
            suggestion="Fix the XML syntax error before committing.",
        ))
        return findings

    root_tag = root.tag.lower()

    # -----------------------------------------------------------------------
    # DITA001 — Topic must have an id attribute
    # -----------------------------------------------------------------------
    if root_tag in TOPIC_TYPE_BODIES and not root.get("id"):
        findings.append(Finding(
            file=filepath, line=1, level="error",
            category="dita-structure", rule_id="DITA001",
            message=f"Root <{root_tag}> element is missing required `id` attribute.",
            suggestion=f'Add id="your-topic-id" to the <{root_tag}> element.',
        ))

    # -----------------------------------------------------------------------
    # DITA002 — Topic must have a <title>
    # -----------------------------------------------------------------------
    title_el = root.find("title")
    if root_tag in TOPIC_TYPE_BODIES and title_el is None:
        findings.append(Finding(
            file=filepath, line=1, level="error",
            category="dita-structure", rule_id="DITA002",
            message=f"Topic <{root_tag}> is missing a <title> element.",
            suggestion="Add a <title> element as the first child of the root topic.",
        ))
    elif title_el is not None:
        title_text = "".join(title_el.itertext()).strip()
        if not title_text:
            ln = _element_line(source_lines, "title")
            findings.append(Finding(
                file=filepath, line=ln, level="error",
                category="dita-structure", rule_id="DITA002",
                message="<title> element is empty.",
                suggestion="Provide a descriptive title for the topic.",
            ))

    # -----------------------------------------------------------------------
    # DITA003 — Topic should have a <shortdesc>
    # -----------------------------------------------------------------------
    shortdesc_el = root.find("shortdesc")
    if root_tag in TOPIC_TYPE_BODIES and shortdesc_el is None:
        findings.append(Finding(
            file=filepath, line=1, level="warning",
            category="dita-structure", rule_id="DITA003",
            message=f"Topic <{root_tag}> is missing a <shortdesc> element.",
            suggestion="Add a short description (1–2 sentences) after <title> to improve search and navigation.",
        ))
    elif shortdesc_el is not None:
        sd_text = "".join(shortdesc_el.itertext()).strip()
        if len(sd_text.split()) > 50:
            ln = _element_line(source_lines, "shortdesc")
            findings.append(Finding(
                file=filepath, line=ln, level="warning",
                category="dita-structure", rule_id="DITA003",
                message=f"<shortdesc> is too long ({len(sd_text.split())} words). Keep it under 50 words.",
                suggestion="Trim the short description to a single concise sentence.",
            ))

    # -----------------------------------------------------------------------
    # DITA004 — Body element must match topic type
    # -----------------------------------------------------------------------
    expected_body = TOPIC_TYPE_BODIES.get(root_tag)
    if expected_body:
        body_el = root.find(expected_body)
        if body_el is None:
            findings.append(Finding(
                file=filepath, line=1, level="error",
                category="dita-structure", rule_id="DITA004",
                message=f"<{root_tag}> topic is missing its required body element <{expected_body}>.",
                suggestion=f"Add a <{expected_body}> element to contain the topic content.",
            ))

    # -----------------------------------------------------------------------
    # DITA005 — <step> must contain <cmd>
    # -----------------------------------------------------------------------
    for step in root.iter("step"):
        cmd = step.find("cmd")
        if cmd is None:
            ln = _element_line(source_lines, "step")
            findings.append(Finding(
                file=filepath, line=ln, level="error",
                category="dita-structure", rule_id="DITA005",
                message="<step> element is missing a required <cmd> element.",
                suggestion="Every <step> must begin with a <cmd> that describes the action.",
            ))
        else:
            cmd_text = "".join(cmd.itertext()).strip()
            if not cmd_text:
                ln = _element_line(source_lines, "cmd")
                findings.append(Finding(
                    file=filepath, line=ln, level="error",
                    category="dita-structure", rule_id="DITA005",
                    message="<cmd> element is empty.",
                    suggestion="Provide a clear, imperative instruction in the <cmd> element.",
                ))

    # -----------------------------------------------------------------------
    # DITA006 — <image> must have alt attribute
    # -----------------------------------------------------------------------
    for idx, img in enumerate(root.iter("image"), start=1):
        if not img.get("alt") and img.find("alt") is None:
            ln = _element_line(source_lines, "image")
            findings.append(Finding(
                file=filepath, line=ln, level="error",
                category="dita-structure", rule_id="DITA006",
                message=f"<image> element #{idx} is missing an `alt` attribute (accessibility).",
                suggestion='Add alt="Descriptive text" to every <image> element.',
            ))

    # -----------------------------------------------------------------------
    # DITA007 — <xref> and <link> must have href
    # -----------------------------------------------------------------------
    for tag in ("xref", "link"):
        for el in root.iter(tag):
            if not el.get("href"):
                ln = _element_line(source_lines, tag)
                findings.append(Finding(
                    file=filepath, line=ln, level="error",
                    category="dita-structure", rule_id="DITA007",
                    message=f"<{tag}> element is missing required `href` attribute.",
                    suggestion=f'Add href="target.dita" or href="http://..." to the <{tag}> element.',
                ))

    # -----------------------------------------------------------------------
    # DITA008 — <section> should have an id and/or a <title>
    # -----------------------------------------------------------------------
    for idx, section in enumerate(root.iter("section"), start=1):
        has_id = bool(section.get("id"))
        has_title = section.find("title") is not None
        if not has_id:
            ln = _element_line(source_lines, "section")
            findings.append(Finding(
                file=filepath, line=ln, level="warning",
                category="dita-structure", rule_id="DITA008",
                message=f"<section> #{idx} is missing an `id` attribute.",
                suggestion='Add id="section-id" so the section can be referenced via conref/xref.',
            ))
        if not has_title:
            ln = _element_line(source_lines, "section")
            findings.append(Finding(
                file=filepath, line=ln, level="warning",
                category="dita-structure", rule_id="DITA008",
                message=f"<section> #{idx} is missing a <title> element.",
                suggestion="Add a <title> to each <section> to aid navigation and accessibility.",
            ))

    # -----------------------------------------------------------------------
    # DITA009 — Task topics should use <steps>, not bare <ol>/<ul> for procedures
    # -----------------------------------------------------------------------
    if root_tag == "task":
        taskbody = root.find("taskbody")
        if taskbody is not None:
            for ol in taskbody.findall("ol"):
                ln = _element_line(source_lines, "ol")
                findings.append(Finding(
                    file=filepath, line=ln, level="warning",
                    category="dita-structure", rule_id="DITA009",
                    message="Task topic uses <ol> directly in <taskbody>; prefer <steps>/<step> elements.",
                    suggestion="Replace <ol><li> with <steps><step><cmd> for proper task structure.",
                ))

    # -----------------------------------------------------------------------
    # DITA010 — <note> type should be specified
    # -----------------------------------------------------------------------
    for note in root.iter("note"):
        if not note.get("type"):
            ln = _element_line(source_lines, "note")
            findings.append(Finding(
                file=filepath, line=ln, level="suggestion",
                category="dita-structure", rule_id="DITA010",
                message='<note> element is missing a `type` attribute.',
                suggestion='Add type="note", type="tip", type="important", type="caution", or type="warning".',
            ))

    # -----------------------------------------------------------------------
    # DITA011 — <table> should have a <title>
    # -----------------------------------------------------------------------
    for idx, tbl in enumerate(root.iter("table"), start=1):
        if tbl.find("title") is None:
            ln = _element_line(source_lines, "table")
            findings.append(Finding(
                file=filepath, line=ln, level="warning",
                category="dita-structure", rule_id="DITA011",
                message=f"<table> #{idx} is missing a <title>.",
                suggestion="Add a <title> element as the first child of <table>.",
            ))

    # -----------------------------------------------------------------------
    # DITA012 — <fig> should have a <title>
    # -----------------------------------------------------------------------
    for idx, fig in enumerate(root.iter("fig"), start=1):
        if fig.find("title") is None:
            ln = _element_line(source_lines, "fig")
            findings.append(Finding(
                file=filepath, line=ln, level="warning",
                category="dita-structure", rule_id="DITA012",
                message=f"<fig> #{idx} is missing a <title>.",
                suggestion="Add a <title> to each <fig> element for accessibility and navigation.",
            ))

    # -----------------------------------------------------------------------
    # DITA013 — xml:lang should be present on root topic
    # -----------------------------------------------------------------------
    if root_tag in TOPIC_TYPE_BODIES:
        lang = root.get("{http://www.w3.org/XML/1998/namespace}lang") or root.get("xml:lang")
        # Also check raw attribute name since ET may parse it differently
        if not lang:
            raw_attrs = " ".join(root.attrib.keys())
            if "lang" not in raw_attrs.lower():
                findings.append(Finding(
                    file=filepath, line=1, level="suggestion",
                    category="dita-structure", rule_id="DITA013",
                    message='Root topic element is missing `xml:lang` attribute.',
                    suggestion='Add xml:lang="en-us" to the root topic element.',
                ))

    # Deduplicate findings with the same rule, line, and message
    seen_keys: set = set()
    deduped: List[Finding] = []
    for f in findings:
        key = (f.rule_id, f.line, f.message)
        if key not in seen_keys:
            seen_keys.add(key)
            deduped.append(f)
    return deduped


# ---------------------------------------------------------------------------
# IBM Style Guide validation
# ---------------------------------------------------------------------------

# Each rule: (rule_id, level, pattern, message, suggestion)
# Patterns run against plain text extracted from DITA elements.

IBM_STYLE_RULES: List[Tuple[str, str, re.Pattern, str, str]] = []


def _add_rule(rule_id: str, level: str, pattern: str, message: str, suggestion: str,
              flags: int = re.IGNORECASE):
    IBM_STYLE_RULES.append((rule_id, level, re.compile(pattern, flags), message, suggestion))


# ---- Banned / discouraged words -----------------------------------------
_add_rule("IBM001", "warning",
    r"\b(easy|easily|simple|simply|straightforward|trivial|obviously|of course|"
    r"just|merely|basic|basically|clearly)\b",
    "Avoid minimizing language: '{match}' may frustrate users who find the task difficult.",
    "Remove the word or rephrase without implying the task is effortless.")

_add_rule("IBM002", "warning",
    r"\bplease\b",
    "Avoid 'please' in technical documentation.",
    "Remove 'please'. Technical instructions should be direct.")

_add_rule("IBM003", "warning",
    r"\butilize\b",
    "Avoid 'utilize'; prefer 'use'.",
    "Replace 'utilize' with 'use'.")

_add_rule("IBM004", "warning",
    r"\bin order to\b",
    "Avoid 'in order to'; prefer 'to'.",
    "Replace 'in order to' with 'to'.")

_add_rule("IBM005", "warning",
    r"\betc\.\b",
    "Avoid 'etc.' — it is vague.",
    "List all items explicitly or use 'such as' with representative examples.")

_add_rule("IBM006", "warning",
    r"\bclick on\b",
    "Use 'click' not 'click on'.",
    "Replace 'click on' with 'click'.")

_add_rule("IBM007", "warning",
    r"\b(above|below)\b(?=.{0,40}(section|table|figure|list|step|topic|page))",
    "Avoid 'above'/'below' as spatial references; use cross-references instead.",
    "Replace with an explicit xref or 'the following' / 'the previous'.")

_add_rule("IBM008", "suggestion",
    r"\b(we|our|us)\b",
    "Avoid first-person plural ('we', 'our', 'us') in technical documentation.",
    "Rewrite using second person ('you', 'your') or passive construction.")

_add_rule("IBM009", "warning",
    r"\ballow(s)? (you|users?) to\b",
    "Avoid 'allows you to'; prefer active, task-focused phrasing.",
    "Rewrite as 'You can ...' or use an imperative sentence.")

_add_rule("IBM010", "suggestion",
    r"\b(n't|can't|won't|don't|doesn't|isn't|aren't|wasn't|weren't|"
    r"haven't|hasn't|hadn't|wouldn't|shouldn't|couldn't|mustn't)\b",
    "Avoid contractions in formal technical documentation.",
    "Expand the contraction (e.g., 'can't' → 'cannot', 'don't' → 'do not').")

_add_rule("IBM011", "suggestion",
    r"\bwill\s+(?:be\s+)?(?:need|have|use|create|delete|update|configure|install|run)\b",
    "Avoid future tense where possible; use present tense for instructions.",
    "Change 'will need' → 'need', 'will use' → 'use', etc.")

_add_rule("IBM012", "warning",
    r"\b(prior to|subsequent to|at this point in time|at the present time|"
    r"due to the fact that|in the event that|for the purpose of)\b",
    "Replace verbose phrase '{match}' with a simpler alternative.",
    "Use: 'before', 'after', 'now', 'currently', 'because', 'if', 'to'.")

_add_rule("IBM013", "warning",
    r"\b(perform a|perform an|make a|make an|give a|give an|have a|have an|"
    r"provide a|provide an)\s+\w+",
    "Avoid nominalizations: '{match}'. Prefer a direct verb.",
    "For example: 'perform a search' → 'search', 'make a change' → 'change'.")

_add_rule("IBM014", "suggestion",
    r"\b(and/or)\b",
    "Avoid 'and/or'. Be explicit about whether you mean 'and', 'or', or both.",
    "Rewrite to remove ambiguity.")

_add_rule("IBM015", "warning",
    r"\b(press\s+the\s+enter\s+key|press\s+the\s+return\s+key)\b",
    "Use 'press Enter' not 'press the Enter key'.",
    "Replace with 'press Enter' or 'press Return'.")

_add_rule("IBM016", "suggestion",
    r"\bdesire[sd]?\b",
    "Avoid 'desired'; prefer 'required', 'wanted', or 'appropriate'.",
    "Replace 'desired' with a more precise word.")

_add_rule("IBM017", "warning",
    r"\b(it is (important|necessary|essential|critical) (to|that)|"
    r"note that|be (sure|certain|aware) that)\b",
    "Avoid throat-clearing phrases like '{match}'.",
    "State the requirement directly. Use a <note> element for important asides.")

_add_rule("IBM018", "suggestion",
    r"\b(very|quite|rather|somewhat|fairly|pretty|really)\s+\w+",
    "Avoid vague intensifiers like '{match}'.",
    "Remove the intensifier or use a more precise adjective.")

_add_rule("IBM019", "warning",
    r"\b(he|she|him|her|his|hers|he/she|him/her|his/her)\b",
    "Avoid gendered pronouns. Use 'they/them/their' or rewrite as second person.",
    "Replace with 'they', 'them', or 'their', or rewrite using 'you'.")

_add_rule("IBM020", "suggestion",
    r"\bmust not\b.{0,60}\bsupported\b|\bnot supported\b",
    "Consider using a <note type=\"important\"> or <note type=\"restriction\"> for unsupported feature notices.",
    "Wrap in a <note type=\"restriction\"> element for better semantic markup.")


def _extract_text_lines(filepath: str) -> List[Tuple[int, str]]:
    """
    Extract (line_number, text_content) pairs from DITA source,
    stripping XML tags and attribute values so style rules run on plain text only.
    Handles tags that span multiple lines to avoid false positives from attribute
    values (e.g. conref paths containing '..').
    Returns one entry per source line that contains non-whitespace prose text.
    """
    path = Path(filepath)
    if not path.exists():
        return []

    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    # 1. Remove XML comments (may span lines)
    cleaned = re.sub(r"<!--.*?-->", "", source, flags=re.DOTALL)
    # 2. Remove processing instructions
    cleaned = re.sub(r"<\?[^?]*\?>", "", cleaned)
    # 3. Remove XML tags that may span multiple lines (including all attributes)
    cleaned = re.sub(r"<[^>]*>", " ", cleaned, flags=re.DOTALL)
    # 4. Collapse runs of whitespace within a line to a single space
    #    (keep newlines so we can map back to line numbers)

    # Rebuild per-line mapping: the cleaned text preserves newlines, so
    # splitting by newline keeps line numbers in sync with the original source.
    results: List[Tuple[int, str]] = []
    for i, line in enumerate(cleaned.splitlines(), start=1):
        text = re.sub(r"\s+", " ", line).strip()
        if text and len(text) > 3:
            results.append((i, text))

    return results


def check_ibm_style(filepath: str) -> List[Finding]:
    """Run IBM style guide rules against plain text content of a DITA file."""
    findings: List[Finding] = []
    text_lines = _extract_text_lines(filepath)
    seen: set = set()  # deduplicate identical rule+line combinations

    for line_no, text in text_lines:
        for rule_id, level, pattern, message, suggestion in IBM_STYLE_RULES:
            for match in pattern.finditer(text):
                dedup_key = (filepath, line_no, rule_id, match.group(0).lower())
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                matched_text = match.group(0)
                msg = message.replace("{match}", f"`{matched_text}`")
                findings.append(Finding(
                    file=filepath,
                    line=line_no,
                    level=level,
                    category="ibm-style",
                    rule_id=rule_id,
                    message=msg,
                    suggestion=suggestion,
                ))

    return findings


# ---------------------------------------------------------------------------
# General grammar / style checks (language-level, not IBM-specific)
# ---------------------------------------------------------------------------

GRAMMAR_RULES: List[Tuple[str, str, re.Pattern, str, str]] = []


def _add_grammar(rule_id: str, level: str, pattern: str, message: str, suggestion: str,
                 flags: int = re.IGNORECASE):
    GRAMMAR_RULES.append((rule_id, level, re.compile(pattern, flags), message, suggestion))


_add_grammar("GRM001", "warning",
    r"\b(\w+)\s+\1\b",
    "Duplicate word: '{match}'.",
    "Remove the repeated word.")

_add_grammar("GRM002", "suggestion",
    r"\b(a)\s+([aeiou]\w+)",
    "Possible article error: '{match}'. Use 'an' before vowel sounds.",
    "Change 'a' to 'an' if the following word begins with a vowel sound.",
    re.IGNORECASE)

_add_grammar("GRM003", "warning",
    r"\.{2,}(?!\.)",
    "Ellipsis or extra periods found.",
    "Use a single period to end a sentence, or use the proper ellipsis character (…) intentionally.")

_add_grammar("GRM004", "suggestion",
    r"\b(is|are|was|were|be|been|being)\s+\w+ed\b(?!\s+by\b)",
    "Possible passive voice construction detected.",
    "Rewrite in active voice where possible (IBM Style Guide preference).")

_add_grammar("GRM005", "warning",
    r"\s{2,}",
    "Multiple consecutive spaces found.",
    "Replace multiple spaces with a single space.")

_add_grammar("GRM006", "suggestion",
    r"\b(setup|startup|login|logout|dropdown|checkbox|toolbox|"
    r"filename|webpage|website|email)\b",
    "Check compound word '{match}' — IBM style may require a different form.",
    "IBM style: 'set up' (v), 'setup' (n/adj); 'log in' (v), 'login' (n/adj); "
    "'drop-down' (adj), 'check box', 'web page'.")


def check_grammar(filepath: str) -> List[Finding]:
    """Run grammar rules against plain text content of a DITA file."""
    findings: List[Finding] = []
    text_lines = _extract_text_lines(filepath)
    seen: set = set()

    for line_no, text in text_lines:
        for rule_id, level, pattern, message, suggestion in GRAMMAR_RULES:
            for match in pattern.finditer(text):
                dedup_key = (filepath, line_no, rule_id, match.start())
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)
                matched_text = match.group(0)
                msg = message.replace("{match}", f"`{matched_text}`")
                findings.append(Finding(
                    file=filepath,
                    line=line_no,
                    level=level,
                    category="grammar",
                    rule_id=rule_id,
                    message=msg,
                    suggestion=suggestion,
                ))

    return findings


# ---------------------------------------------------------------------------
# PR comment formatter
# ---------------------------------------------------------------------------

def _count_by_level(findings: List[Finding]) -> dict:
    counts = {"error": 0, "warning": 0, "suggestion": 0}
    for f in findings:
        counts[f.level] = counts.get(f.level, 0) + 1
    return counts


def _status_badge(counts: dict) -> str:
    if counts["error"] > 0:
        return "🔴 **Issues Found — Action Required**"
    if counts["warning"] > 0:
        return "🟡 **Warnings Found — Review Recommended**"
    if counts["suggestion"] > 0:
        return "🔵 **Suggestions Only — Optional Improvements**"
    return "✅ **All Checks Passed**"


def build_pr_comment(all_findings: List[Finding], changed_files: List[str]) -> str:
    """Build the full Markdown body for the PR review comment."""

    counts = _count_by_level(all_findings)
    files_with_issues = sorted({f.file for f in all_findings})
    total_files = len(changed_files)

    lines = [
        "## 📚 Docs PR Review Bot",
        "",
        _status_badge(counts),
        "",
        f"Validated **{total_files}** changed DITA file(s). "
        f"Found **{counts['error']} error(s)**, "
        f"**{counts['warning']} warning(s)**, "
        f"**{counts['suggestion']} suggestion(s)**.",
        "",
    ]

    if not all_findings:
        lines += [
            "No issues detected. Great job keeping the docs clean! ✨",
            "",
        ]
        lines.append(_build_legend())
        return "\n".join(lines)

    # Summary table
    lines += [
        "### Summary",
        "",
        "| Category | Errors | Warnings | Suggestions |",
        "|---|---|---|---|",
    ]
    for cat, label in [
        ("dita-structure", "DITA Structure"),
        ("ibm-style", "IBM Style Guide"),
        ("grammar", "Grammar & Style"),
    ]:
        cat_findings = [f for f in all_findings if f.category == cat]
        cat_counts = _count_by_level(cat_findings)
        lines.append(
            f"| {label} | {cat_counts['error']} | {cat_counts['warning']} | {cat_counts['suggestion']} |"
        )
    lines.append("")

    # Per-file findings
    lines.append("### Findings by File")
    lines.append("")

    for filepath in files_with_issues:
        file_findings = [f for f in all_findings if f.file == filepath]
        file_counts = _count_by_level(file_findings)
        status = "🔴" if file_counts["error"] else ("🟡" if file_counts["warning"] else "🔵")
        short_path = filepath.replace("\\", "/")

        lines += [
            f"<details>",
            f"<summary>{status} <code>{short_path}</code> — "
            f"{file_counts['error']} error(s), {file_counts['warning']} warning(s), "
            f"{file_counts['suggestion']} suggestion(s)</summary>",
            "",
            "| Line | Level | Rule | Category | Message |",
            "|---|---|---|---|---|",
        ]

        for finding in sorted(file_findings, key=lambda x: (x.line, x.rule_id)):
            level_icon = finding.severity_icon
            suggestion_cell = (
                f"<br><sub>💡 {finding.suggestion}</sub>" if finding.suggestion else ""
            )
            lines.append(
                f"| {finding.line} | {level_icon} {finding.level} | `{finding.rule_id}` | "
                f"{finding.category} | {finding.message}{suggestion_cell} |"
            )

        lines += ["", "</details>", ""]

    lines.append(_build_legend())
    lines += [
        "",
        "---",
        "<sub>Generated by the Docs PR Review Bot · "
        "[Rule reference](.github/docs-bot-config.json)</sub>",
    ]

    return "\n".join(lines)


def _build_legend() -> str:
    return textwrap.dedent("""\
        <details>
        <summary>Legend & Rule Reference</summary>

        | Icon | Level | Meaning |
        |---|---|---|
        | 🔴 | Error | Must be fixed — violates DITA spec or critical IBM style rule |
        | 🟡 | Warning | Should be fixed — IBM Style Guide recommendation |
        | 🔵 | Suggestion | Optional improvement — grammar or minor style hint |

        **DITA Structure Rules**
        | Rule | Description |
        |---|---|
        | DITA000 | XML parse error |
        | DITA001 | Root topic missing `id` attribute |
        | DITA002 | Missing or empty `<title>` |
        | DITA003 | Missing or over-long `<shortdesc>` |
        | DITA004 | Body element mismatch (conbody/taskbody/refbody) |
        | DITA005 | `<step>` missing `<cmd>` |
        | DITA006 | `<image>` missing `alt` attribute |
        | DITA007 | `<xref>` or `<link>` missing `href` |
        | DITA008 | `<section>` missing `id` or `<title>` |
        | DITA009 | Task uses `<ol>` instead of `<steps>` |
        | DITA010 | `<note>` missing `type` attribute |
        | DITA011 | `<table>` missing `<title>` |
        | DITA012 | `<fig>` missing `<title>` |
        | DITA013 | Root topic missing `xml:lang` |

        **IBM Style Guide Rules**
        | Rule | Description |
        |---|---|
        | IBM001 | Minimizing language (easy, simply, just, …) |
        | IBM002 | Use of "please" |
        | IBM003 | "utilize" → "use" |
        | IBM004 | "in order to" → "to" |
        | IBM005 | Vague "etc." |
        | IBM006 | "click on" → "click" |
        | IBM007 | Spatial references (above/below) |
        | IBM008 | First-person plural (we/our/us) |
        | IBM009 | "allows you to" phrasing |
        | IBM010 | Contractions |
        | IBM011 | Future tense |
        | IBM012 | Verbose phrases |
        | IBM013 | Nominalizations |
        | IBM014 | "and/or" ambiguity |
        | IBM015 | "press the Enter key" → "press Enter" |
        | IBM016 | "desired" → specific word |
        | IBM017 | Throat-clearing phrases |
        | IBM018 | Vague intensifiers |
        | IBM019 | Gendered pronouns |
        | IBM020 | Unsupported feature notices |

        **Grammar Rules**
        | Rule | Description |
        |---|---|
        | GRM001 | Duplicate words |
        | GRM002 | Article "a" before vowel sounds |
        | GRM003 | Extra periods or ellipsis |
        | GRM004 | Passive voice |
        | GRM005 | Multiple spaces |
        | GRM006 | Compound word style check |

        </details>""")


# ---------------------------------------------------------------------------
# Agentic planner / critic / state helpers
# ---------------------------------------------------------------------------

STATE_MARKER_PREFIX = "<!-- DOCS_BOT_STATE:"
STATE_MARKER_SUFFIX = " -->"


def _finding_fingerprint(finding: Finding) -> str:
    return "|".join([
        finding.file,
        str(finding.line),
        finding.rule_id,
        finding.level,
        finding.message,
    ])


def _file_risk_score(filepath: str) -> int:
    """Simple risk heuristic used by planner to prioritize files."""
    score = 0
    lower = filepath.lower()
    if lower.endswith(".dita"):
        score += 3
    if lower.endswith(".ditamap"):
        score += 1
    if "/task" in lower or "_task" in lower or lower.startswith("t_"):
        score += 2
    if "install" in lower or "upgrade" in lower or "security" in lower:
        score += 2
    return score


def build_plan(changed_files: List[str], state: Dict[str, Any], config: Dict[str, Any]) -> List[PlanStep]:
    """Planner: build an ordered list of file+check actions."""
    previous_sha = state.get("last_sha", "")
    current_sha = os.environ.get("GITHUB_SHA", "")
    incremental = bool(previous_sha and current_sha and previous_sha == current_sha)

    plan: List[PlanStep] = []
    for filepath in changed_files:
        checks: List[str] = ["dita"]
        if filepath.endswith(".dita"):
            checks += ["ibm-style", "grammar"]

        # If run is incremental with same SHA, avoid re-running low confidence checks.
        if incremental:
            checks = [c for c in checks if c in ("dita", "ibm-style")]

        plan.append(PlanStep(
            file=filepath,
            checks=checks,
            risk=_file_risk_score(filepath),
        ))

    return sorted(plan, key=lambda s: s.risk, reverse=True)


def _assign_confidence(finding: Finding) -> Finding:
    """Critic: assign confidence level based on category and severity."""
    if finding.category == "dita-structure":
        finding.confidence = "high" if finding.level == "error" else "medium"
    elif finding.category == "ibm-style":
        finding.confidence = "medium" if finding.level in ("error", "warning") else "low"
    else:
        finding.confidence = "low"
    return finding


def _dedupe_and_rank_findings(findings: List[Finding]) -> List[Finding]:
    """Critic: normalize, dedupe, and rank findings for output."""
    seen: Set[str] = set()
    deduped: List[Finding] = []
    for item in findings:
        item = _assign_confidence(item)
        fp = _finding_fingerprint(item)
        if fp in seen:
            continue
        seen.add(fp)
        deduped.append(item)

    level_weight = {"error": 0, "warning": 1, "suggestion": 2}
    conf_weight = {"high": 0, "medium": 1, "low": 2}
    return sorted(
        deduped,
        key=lambda f: (
            level_weight.get(f.level, 3),
            conf_weight.get(f.confidence, 3),
            f.file,
            f.line,
            f.rule_id,
        ),
    )


def _extract_state_from_comment(comment_body: str) -> Dict[str, Any]:
    """Parse persisted state from hidden HTML marker in bot comment body."""
    if not comment_body:
        return {}
    pattern = re.escape(STATE_MARKER_PREFIX) + r"(.*?)" + re.escape(STATE_MARKER_SUFFIX)
    match = re.search(pattern, comment_body, flags=re.DOTALL)
    if not match:
        return {}
    payload = match.group(1).strip()
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return {}


def _append_state_marker(comment_body: str, state: Dict[str, Any]) -> str:
    marker = f"{STATE_MARKER_PREFIX}{json.dumps(state, separators=(',', ':'))}{STATE_MARKER_SUFFIX}"
    return f"{comment_body}\n\n{marker}"


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------

def _github_request(method: str, url: str, token: str, body: Optional[dict] = None) -> dict:
    """Make an authenticated GitHub API request."""
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "docs-pr-review-bot/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"GitHub API error {exc.code}: {error_body}", file=sys.stderr)
        raise


def find_existing_bot_comment(token: str, repo: str, pr_number: int) -> Optional[Tuple[int, str]]:
    """Return (comment_id, body) for the existing bot comment on the PR, or None."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments?per_page=100"
    try:
        comments = _github_request("GET", url, token)
    except urllib.error.HTTPError:
        return None

    for comment in comments:
        body = comment.get("body", "")
        if "📚 Docs PR Review Bot" in body:
            return comment["id"], body
    return None


def post_or_update_comment(token: str, repo: str, pr_number: int, body: str) -> int:
    """Post a new comment or update the existing bot comment on the PR and return comment id."""
    existing = find_existing_bot_comment(token, repo, pr_number)

    if existing:
        existing_id = existing[0]
        url = f"https://api.github.com/repos/{repo}/issues/comments/{existing_id}"
        _github_request("PATCH", url, token, {"body": body})
        print(f"Updated existing bot comment #{existing_id}.")
        return existing_id
    else:
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        response = _github_request("POST", url, token, {"body": body})
        print("Posted new bot comment on PR.")
        return int(response.get("id", 0))


def set_pr_review_status(
    token: str, repo: str, pr_number: int, findings: List[Finding]
) -> None:
    """
    Submit a formal PR review (APPROVE / REQUEST_CHANGES / COMMENT).
    Only requests changes when there are errors.
    """
    counts = _count_by_level(findings)
    blocking_errors = [f for f in findings if f.level == "error" and f.confidence == "high"]

    if blocking_errors:
        event = "REQUEST_CHANGES"
        review_body = (
            f"🔴 **{len(blocking_errors)} high-confidence blocking error(s) found** in the documentation. "
            "Please resolve them before merging. See the bot comment above for details."
        )
    elif counts["warning"] > 0:
        event = "COMMENT"
        review_body = (
            f"🟡 **{counts['warning']} warning(s) found** in the documentation. "
            "Review the bot comment for suggestions."
        )
    else:
        event = "APPROVE"
        review_body = "✅ All docs validation checks passed!"

    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
    try:
        _github_request("POST", url, token, {"body": review_body, "event": event})
        print(f"Submitted PR review: {event}")
    except urllib.error.HTTPError as exc:
        # Reviews can fail if the bot is the PR author — not fatal
        print(f"Could not submit PR review (non-fatal): {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Configuration loader
# ---------------------------------------------------------------------------

def load_config(config_path: Optional[str]) -> dict:
    """Load optional bot configuration from JSON file."""
    defaults = {
        "disabled_rules": [],
        "max_findings_per_file": 50,
        "max_steps": 8,
        "max_state_fingerprints": 3000,
        "post_review": True,
    }
    if not config_path:
        return defaults
    path = Path(config_path)
    if not path.exists():
        return defaults
    try:
        user_config = json.loads(path.read_text(encoding="utf-8"))
        defaults.update(user_config)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Warning: could not load config {config_path}: {exc}", file=sys.stderr)
    return defaults


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    token = os.environ.get("GITHUB_TOKEN", "")
    pr_number_str = os.environ.get("PR_NUMBER", "")
    repo = os.environ.get("REPO", "")
    changed_files_path = os.environ.get("CHANGED_FILES_PATH", "changed_files.txt")
    config_path = os.environ.get("BOT_CONFIG_PATH")

    if not token or not pr_number_str or not repo:
        print("ERROR: GITHUB_TOKEN, PR_NUMBER, and REPO must be set.", file=sys.stderr)
        sys.exit(1)

    try:
        pr_number = int(pr_number_str)
    except ValueError:
        print(f"ERROR: PR_NUMBER must be an integer, got '{pr_number_str}'", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    disabled_rules = set(config.get("disabled_rules", []))
    max_per_file = int(config.get("max_findings_per_file", 50))
    max_steps = int(config.get("max_steps", 8))
    max_state_fingerprints = int(config.get("max_state_fingerprints", 3000))

    # Read changed files list
    changed_files_file = Path(changed_files_path)
    if not changed_files_file.exists():
        print(f"ERROR: Changed files list not found: {changed_files_path}", file=sys.stderr)
        sys.exit(1)

    changed_files = [
        line.strip()
        for line in changed_files_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and (line.strip().endswith(".dita") or line.strip().endswith(".ditamap"))
    ]

    if not changed_files:
        print("No DITA files to validate.")
        return

    print(f"Planning validation for {len(changed_files)} file(s)…")

    existing_comment = find_existing_bot_comment(token, repo, pr_number)
    previous_state: Dict[str, Any] = {}
    existing_comment_id: Optional[int] = None
    if existing_comment:
        existing_comment_id = existing_comment[0]
        previous_state = _extract_state_from_comment(existing_comment[1])

    plan = build_plan(changed_files, previous_state, config)
    print(f"Planner created {len(plan)} step(s).")

    all_findings: List[Finding] = []
    processed_files: List[str] = []
    seen_fingerprints: Set[str] = set(previous_state.get("finding_fingerprints", []))

    steps_executed = 0
    idle_steps = 0
    for step in plan:
        if steps_executed >= max_steps:
            print(f"Reached max_steps={max_steps}; stopping execution loop.")
            break

        steps_executed += 1
        processed_files.append(step.file)
        file_findings: List[Finding] = []

        if "dita" in step.checks:
            file_findings.extend(validate_dita(step.file))
        if "ibm-style" in step.checks:
            file_findings.extend(check_ibm_style(step.file))
        if "grammar" in step.checks:
            file_findings.extend(check_grammar(step.file))

        if disabled_rules:
            file_findings = [f for f in file_findings if f.rule_id not in disabled_rules]

        file_findings = _dedupe_and_rank_findings(file_findings)

        if len(file_findings) > max_per_file:
            print(
                f"  {step.file}: {len(file_findings)} findings — capping at {max_per_file}",
                file=sys.stderr,
            )
            file_findings = file_findings[:max_per_file]

        new_findings: List[Finding] = []
        for finding in file_findings:
            fp = _finding_fingerprint(finding)
            if fp in seen_fingerprints:
                continue
            seen_fingerprints.add(fp)
            new_findings.append(finding)

        counts = _count_by_level(new_findings)
        print(
            f"  step {steps_executed}: {step.file} (risk={step.risk}) -> "
            f"{counts['error']} new errors, {counts['warning']} new warnings, "
            f"{counts['suggestion']} new suggestions"
        )

        if not new_findings:
            idle_steps += 1
        else:
            idle_steps = 0
            all_findings.extend(new_findings)

        # Stop early if planner keeps producing no new information.
        if idle_steps >= 2:
            print("No new findings in 2 consecutive steps; stopping early.")
            break

    all_findings = _dedupe_and_rank_findings(all_findings)

    # Build and post/update PR comment with persisted state marker.
    comment_body = build_pr_comment(all_findings, changed_files)
    new_state: Dict[str, Any] = {
        "last_sha": os.environ.get("GITHUB_SHA", ""),
        "files_analyzed": processed_files,
        "finding_fingerprints": list(seen_fingerprints)[-max_state_fingerprints:],
        "steps_executed": steps_executed,
    }
    final_comment_body = _append_state_marker(comment_body, new_state)
    comment_id = post_or_update_comment(token, repo, pr_number, final_comment_body)

    if existing_comment_id is not None and existing_comment_id != comment_id:
        print(f"Bot comment moved from {existing_comment_id} to {comment_id}.")

    if config.get("post_review", True):
        set_pr_review_status(token, repo, pr_number, all_findings)

    # CI blocking is based only on high-confidence errors.
    blocking_errors = [f for f in all_findings if f.level == "error" and f.confidence == "high"]
    if blocking_errors:
        print(
            f"\n❌ Validation failed: {len(blocking_errors)} high-confidence blocking error(s) found.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\n✅ Validation complete.")


if __name__ == "__main__":
    main()
