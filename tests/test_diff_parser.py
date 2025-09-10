import pytest

from src.parsers.diff_parser import DiffParser


@pytest.fixture
def parser():
    return DiffParser()


def test_parse_diff(parser):
    diff_data = """diff --git a/file1.py b/file1.py
index 83db48f..f735c8b 100644
--- a/file1.py
+++ b/file1.py
@@ -1,4 +1,4 @@
 def hello_world():
-    print("Hello, world!")
+    print("Hello, universe!")
 """
    expected_output = {
        "file": "file1.py",
        "changes": [{"line": 2, "old": '    print("Hello, world!")', "new": '    print("Hello, universe!")'}],
    }
    result = parser.parse(diff_data)
    assert result == expected_output


def test_empty_diff(parser):
    diff_data = ""
    result = parser.parse(diff_data)
    assert result == {}


def test_invalid_diff_format(parser):
    diff_data = "invalid diff format"
    with pytest.raises(ValueError):
        parser.parse(diff_data)
