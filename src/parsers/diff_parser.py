import re
from typing import Any


class DiffParser:
    """Parses unified diff text into a simple structure."""

    FILE_HEADER_RE = re.compile(r"^diff --git a/(\S+) b/(\S+)")
    HUNK_HEADER_RE = re.compile(r"^@@ -(?P<old_start>\d+),(?P<old_len>\d+) \+(?P<new_start>\d+),(?P<new_len>\d+) @@")

    def parse(self, diff_text: str) -> dict[str, Any]:
        if not diff_text.strip():
            return {}

        lines = diff_text.splitlines()
        file_match = self.FILE_HEADER_RE.match(lines[0]) if lines else None
        if not file_match:
            raise ValueError("Invalid diff format: missing file header")
        _file_a, file_b = file_match.groups()
        file_name = file_b

        changes = []
        old_line_no = None
        new_line_no = None

        for line in lines:
            hunk = self.HUNK_HEADER_RE.match(line)
            if hunk:
                old_line_no = int(hunk.group("old_start"))
                new_line_no = int(hunk.group("new_start"))
                continue
            if line.startswith(("+++", "---", "diff --git", "index ")):
                continue
            if old_line_no is None or new_line_no is None:
                continue
            if line.startswith("-"):
                removed_content = line[1:]
                changes.append({"line": new_line_no, "old": removed_content, "new": None})
                old_line_no += 1
            elif line.startswith("+"):
                added_content = line[1:]
                if changes and changes[-1]["new"] is None:
                    changes[-1]["new"] = added_content
                else:
                    changes.append({"line": new_line_no, "old": None, "new": added_content})
                new_line_no += 1
            else:
                old_line_no += 1
                new_line_no += 1

        modifications = [c for c in changes if c["old"] is not None and c["new"] is not None]

        return {
            "file": file_name,
            "changes": modifications,
        }

    def parse_multi_file_diff(self, diff_text: str) -> list[dict[str, Any]]:
        """Parse diff text containing multiple files into list of file diffs."""
        if not diff_text.strip():
            return []

        files = []
        current_file_lines = []

        for line in diff_text.splitlines():
            if line.startswith("diff --git"):
                if current_file_lines:
                    try:
                        file_diff = self.parse("\n".join(current_file_lines))
                        if file_diff:
                            files.append(file_diff)
                    except ValueError:
                        pass
                current_file_lines = [line]
            else:
                current_file_lines.append(line)

        # Process last file
        if current_file_lines:
            try:
                file_diff = self.parse("\n".join(current_file_lines))
                if file_diff:
                    files.append(file_diff)
            except ValueError:
                pass

        return files

    def extract_file_chunks(self, diff_text: str) -> list[dict[str, str]]:
        """Extract individual file diffs with their raw content."""
        if not diff_text.strip():
            return []

        chunks = []
        current_chunk = []
        current_file = None

        for line in diff_text.splitlines():
            if line.startswith("diff --git"):
                if current_chunk and current_file:
                    chunks.append({"file": current_file, "diff": "\n".join(current_chunk)})

                match = self.FILE_HEADER_RE.match(line)
                current_file = match.group(2) if match else "unknown"
                current_chunk = [line]
            else:
                current_chunk.append(line)

        if current_chunk and current_file:
            chunks.append({"file": current_file, "diff": "\n".join(current_chunk)})

        return chunks
