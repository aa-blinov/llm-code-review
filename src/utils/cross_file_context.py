"""Cross-file context utilities for LLM code review.

Based on SOTA research (AACR-Bench, LAURA, Hydra-Reviewer):
- ~15% of real code issues require repository-level (cross-file) context
- Providing related module context significantly improves review quality
- Key insight: reviewee needs to know about contracts with imported/importing modules
"""

from __future__ import annotations

import ast
from typing import Any


def _extract_python_imports(source_code: str) -> list[str]:
    """Extract all module paths from Python import statements using AST."""
    imports: list[str] = []
    try:
        tree = ast.parse(source_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
    except SyntaxError:
        pass
    return imports


def _module_to_possible_paths(module: str) -> list[str]:
    """Convert a dotted module name to candidate file paths."""
    base = module.replace(".", "/")
    return [base + ".py", base + "/__init__.py"]


def _build_module_variants(file_path: str) -> list[str]:
    """Build possible Python module names for a given file path.

    E.g. 'src/utils/helpers.py' → ['src.utils.helpers', 'utils.helpers', 'helpers']
    """
    if not file_path.endswith(".py"):
        return []
    parts = file_path.replace(".py", "").replace("/", ".")
    # Strip __init__ suffix
    if parts.endswith(".__init__"):
        parts = parts[: -len(".__init__")]
    segments = parts.split(".")
    variants = []
    for i in range(len(segments)):
        variants.append(".".join(segments[i:]))
    return variants


def find_related_changes(
    file_path: str,
    new_content: str,
    all_changes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Find PR changes that are related to *file_path* via Python imports.

    Returns:
        (dependencies, dependents)
        - dependencies: other changed files that *this* file imports
        - dependents:   other changed files that import *this* file
    """
    other_changes = [c for c in all_changes if c.get("file_path") != file_path]

    dependencies: list[dict[str, Any]] = []
    dependents: list[dict[str, Any]] = []

    # --- Files this file imports -----------------------------------------
    if file_path.endswith(".py") and new_content:
        imports = _extract_python_imports(new_content)
        seen: set[str] = set()
        for imp in imports:
            for possible_path in _module_to_possible_paths(imp):
                for other in other_changes:
                    other_fp = other.get("file_path", "")
                    if other_fp and (
                        other_fp == possible_path or other_fp.endswith("/" + possible_path)
                    ):
                        if other_fp not in seen:
                            dependencies.append(other)
                            seen.add(other_fp)
                        break

    # --- Files that import this file  ------------------------------------
    this_variants = set(_build_module_variants(file_path))
    if this_variants:
        seen_dep: set[str] = set()
        for other in other_changes:
            other_fp = other.get("file_path", "")
            if not other_fp.endswith(".py"):
                continue
            other_content = other.get("new_content", "")
            if not other_content:
                continue
            other_imports = set(_extract_python_imports(other_content))
            if other_imports & this_variants and other_fp not in seen_dep:
                dependents.append(other)
                seen_dep.add(other_fp)

    return dependencies, dependents


def build_pr_map(
    enhanced_changes: list[dict[str, Any]],
    pr_title: str = "",
    pr_description: str = "",
) -> str:
    """Build a concise overview map of all files changed in the PR.

    This gives the LLM a "bird's-eye view" of the whole PR so it can
    reason about architectural consistency and missing pieces.
    """
    if not enhanced_changes:
        return ""

    lines: list[str] = []
    if pr_title:
        lines.append(f"### Контекст PR: {pr_title}")
    else:
        lines.append("### Контекст PR")

    if pr_description and pr_description.strip():
        desc = pr_description.strip()
        if len(desc) > 300:
            desc = desc[:300] + "..."
        lines.append(f"**Описание**: {desc}")
        lines.append("")

    lines.append(f"**Изменено файлов**: {len(enhanced_changes)}")
    lines.append("")
    lines.append("| Файл | Изменение |")
    lines.append("|------|-----------|")
    for c in enhanced_changes:
        fp = c.get("file_path", "?")
        if c.get("new_file"):
            ct = "новый"
        elif c.get("deleted_file"):
            ct = "удалён"
        else:
            ct = "изменён"
        lines.append(f"| `{fp}` | {ct} |")

    return "\n".join(lines)


def build_cross_file_section(
    dependencies: list[dict[str, Any]],
    dependents: list[dict[str, Any]],
    max_diff_chars: int = 1500,
) -> str:
    """Build a human-readable cross-file context section for the review prompt.

    Args:
        dependencies:  changed files that the file under review imports.
        dependents:    changed files that import the file under review.
        max_diff_chars: max characters per diff snippet to avoid token overload.
    """
    if not dependencies and not dependents:
        return ""

    parts: list[str] = ["### Связанные изменения в PR"]

    if dependencies:
        parts.append(
            "\n**Зависимости** (файлы, которые импортирует этот модуль, также изменены в PR):"
        )
        for dep in dependencies:
            fp = dep.get("file_path", "?")
            diff = dep.get("diff", "")
            parts.append(f"\n`{fp}`")
            if diff:
                snippet = diff[:max_diff_chars]
                if len(diff) > max_diff_chars:
                    snippet += "\n... (сокращено)"
                parts.append(f"```diff\n{snippet}\n```")
            else:
                parts.append("*(нет diff — новый файл или удалён)*")

    if dependents:
        parts.append(
            "\n**Зависимые модули** (файлы, которые импортируют этот модуль, также изменены в PR):"
        )
        for dep in dependents:
            fp = dep.get("file_path", "?")
            diff = dep.get("diff", "")
            parts.append(f"\n`{fp}`")
            if diff:
                snippet = diff[:max_diff_chars]
                if len(diff) > max_diff_chars:
                    snippet += "\n... (сокращено)"
                parts.append(f"```diff\n{snippet}\n```")
            else:
                parts.append("*(нет diff)*")

    return "\n".join(parts)
