import argparse
import logging
from datetime import UTC, datetime
from pathlib import Path

from src.providers.github_provider import GitHubProvider
from src.providers.gitlab_provider import GitLabProvider
from src.report.report_builder import ReportBuilder
from src.reviewers.gemini_reviewer import GeminiReviewer


def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Code Review Tool (GitHub/GitLab + Gemini)")
    parser.add_argument("merge_request_url", type=str, help="URL of the merge request to review")
    parser.add_argument("-o", "--output", type=str, help="Directory to write report file (default: ./outputs)")
    args = parser.parse_args()

    print("🚀 Запуск анализа merge request...")
    print(f"📍 URL: {args.merge_request_url}")

    # (Config is currently accessed internally by providers via environment variables)

    # Determine the provider based on the URL
    if "github.com" in args.merge_request_url:
        print("🔍 Определен провайдер: GitHub")
        provider = GitHubProvider()
    elif "gitlab.com" in args.merge_request_url:
        print("🔍 Определен провайдер: GitLab")
        provider = GitLabProvider()
    else:
        print("❌ Неподдерживаемый URL merge request")
        logging.error("Unsupported merge request URL")
        return

    # Fetch merge request data (providers expose fetch_merge_request or fetch_merge_request_data)
    print("📥 Получение данных merge request...")
    if hasattr(provider, "fetch_merge_request_data"):
        raw_data = provider.fetch_merge_request_data(args.merge_request_url)
        # Parse the data if provider has parser method
        if hasattr(provider, "parse_merge_request_data"):
            merge_request_data = provider.parse_merge_request_data(raw_data)
        else:
            merge_request_data = raw_data
    else:
        merge_request_data = provider.fetch_merge_request(args.merge_request_url)

    print(f"✅ Данные получены: '{merge_request_data.get('title', 'Unknown')}'")
    author_info = merge_request_data.get("author") or (
        merge_request_data.get("user", {}) if isinstance(merge_request_data.get("user"), dict) else {}
    )
    author_name = author_info.get("name") if isinstance(author_info, dict) else author_info or "Unknown"
    print(f"👤 Автор: {author_name}")

    # Process the data and generate a review report
    print("🤖 Запуск AI анализа...")
    reviewer = GeminiReviewer(merge_request_data)
    report_data = reviewer.generate_report_data()
    ai_sections = reviewer.get_review_comments()
    if ai_sections:
        print("✅ AI анализ завершен")
        report_data["ai_diff_comments"] = ai_sections.get("diff_comments", [])
        report_data["ai_summary"] = ai_sections.get("summary", "")
        report_data["file_reviews"] = ai_sections.get("file_reviews", [])
    else:
        print("ℹ️  AI анализ пропущен или не дал результатов")

    # Build the final report
    print("📝 Формирование отчета...")
    report_builder = ReportBuilder()
    report = report_builder.generate_report(report_data)

    # Output the report
    # Determine output directory and filename
    print("💾 Сохранение отчета...")
    if args.output:
        out_dir = Path(args.output)
    else:
        out_dir = Path.cwd() / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-UTC")
    filename = f"review-{ts}.md"
    out_path = out_dir / filename
    out_path.write_text(report, encoding="utf-8")
    print(f"✅ Отчет сохранен: {out_path}")
    print("🎉 Анализ завершен!")


if __name__ == "__main__":
    main()
