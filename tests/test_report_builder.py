from src.report.report_builder import ReportBuilder


def test_generate_report():
    report_builder = ReportBuilder()
    sample_data = {
        "title": "Sample Merge Request",
        "author": "Test Author",
        "changes": [{"file": "test_file.py", "status": "modified"}, {"file": "new_file.py", "status": "added"}],
    }
    expected_report = (
        "# Sample Merge Request\n## 👤 Автор: Test Author\n\n### Changes:\n"
        "- test_file.py: modified\n- new_file.py: added\n"
    )
    report = report_builder.generate_report(sample_data)
    assert report == expected_report


def test_empty_report():
    report_builder = ReportBuilder()
    sample_data = {}
    expected_report = "# No Title\n## 👤 Автор: Unknown\n\n### Changes:\nNo changes detected.\n"
    report = report_builder.generate_report(sample_data)
    assert report == expected_report
