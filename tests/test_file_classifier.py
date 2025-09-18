from src.parsers.file_classifier import FileClassifier


def test_get_file_extension_variants():
    fc = FileClassifier()
    assert fc.get_file_extension("a.py") == ".py"
    assert fc.get_file_extension("A.PY") == ".py"
    assert fc.get_file_extension("folder/name.module.ts") == ".ts"
    assert fc.get_file_extension("no_ext") == ""
    assert fc.get_file_extension(".gitignore") == ""


def test_classify_file_known_types():
    fc = FileClassifier()
    assert fc.classify_file("app.py") == "python"
    assert fc.classify_file("readme.MD") == "markdown"
    assert fc.classify_file("script.js") == "javascript"
    assert fc.classify_file("index.html") == "html"
    assert fc.classify_file("styles.css") == "css"
    assert fc.classify_file("schema.json") == "json"
    assert fc.classify_file("layout.xml") == "xml"


def test_classify_file_unknown():
    fc = FileClassifier()
    assert fc.classify_file("Dockerfile") == "other"
    assert fc.classify_file("archive.zip") == "other"


def test_classify_files_grouping():
    fc = FileClassifier()
    files = [
        "app.py",
        "README.md",
        "script.js",
        "notes.txt",
        "index.html",
        "unknown.bin",
    ]
    grouped = fc.classify_files(files)
    assert grouped["python"] == ["app.py"]
    assert grouped["markdown"] == ["README.md"]
    assert grouped["javascript"] == ["script.js"]
    assert grouped["text"] == ["notes.txt"]
    assert grouped["html"] == ["index.html"]
    assert grouped["other"] == ["unknown.bin"]
