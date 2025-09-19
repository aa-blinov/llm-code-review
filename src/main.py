import argparse
from datetime import UTC, datetime
from pathlib import Path

from src.config import Config
from src.providers.github_provider import GitHubProvider
from src.providers.gitlab_provider import GitLabProvider
from src.report.report_builder import ReportBuilder
from src.reviewers.reviewer_factory import ReviewerFactory
from src.utils.logging import get_logger

logger = get_logger()


def main():
    parser = argparse.ArgumentParser(description="Code Review Tool (GitHub/GitLab + Gemini)")
    parser.add_argument("merge_request_url", type=str, help="URL of the merge request to review")
    parser.add_argument("-o", "--output", type=str, help="Directory to write report file (default: ./outputs)")
    args = parser.parse_args()

    logger.info("Starting merge request analysis...")
    logger.info(f"URL: {args.merge_request_url}")

    # Log configured AI provider and model at startup
    configured_provider = (Config.REVIEWER_PROVIDER or "unknown").lower()
    if configured_provider == "gemini":
        logger.info(f"AI configured: provider=gemini, model={Config.GEMINI_MODEL}")
    elif configured_provider == "openai_like":
        logger.info(
            f"AI configured: provider=openai_like, model={Config.OPENAI_LIKE_MODEL}, "
            f"base_url={Config.OPENAI_LIKE_BASE_URL}"
        )
    else:
        logger.info(f"AI configured: provider={configured_provider}")


    if "github.com" in args.merge_request_url:
        logger.info("Provider detected: GitHub")
        provider = GitHubProvider()
    elif "gitlab.com" in args.merge_request_url:
        logger.info("Provider detected: GitLab")
        provider = GitLabProvider()
    else:
        logger.error("Unsupported merge request URL")
        return

    logger.info("Fetching merge request data...")
    if hasattr(provider, "fetch_merge_request_data"):
        raw_data = provider.fetch_merge_request_data(args.merge_request_url)
        if hasattr(provider, "parse_merge_request_data"):
            merge_request_data = provider.parse_merge_request_data(raw_data)
        else:
            merge_request_data = raw_data
    else:
        merge_request_data = provider.fetch_merge_request(args.merge_request_url)

    logger.info(f"Data received: '{merge_request_data.get('title', 'Unknown')}'")
    author_info = merge_request_data.get("author") or (
        merge_request_data.get("user", {}) if isinstance(merge_request_data.get("user"), dict) else {}
    )
    author_name = author_info.get("name") if isinstance(author_info, dict) else author_info or "Unknown"
    logger.info(f"Author: {author_name}")

    logger.info("Starting AI analysis...")
    validation = ReviewerFactory.validate_configuration()
    if not validation["valid"]:
        for error in validation["errors"]:
            logger.error(f"Configuration error: {error}")
        logger.error("Terminating due to configuration errors")
        return

    for warning in validation["warnings"]:
        logger.warning(f"Warning: {warning}")

    try:
        reviewer = ReviewerFactory.create_reviewer(merge_request_data)
    except ValueError as e:
        logger.error(str(e))
        logger.error("Terminating: AI reviewer unavailable")
        return

    report_data = reviewer.generate_report_data()
    ai_sections = reviewer.get_review_comments()
    if ai_sections:
        logger.info("AI analysis completed")
        report_data["ai_diff_comments"] = ai_sections.get("diff_comments", [])
        report_data["ai_summary"] = ai_sections.get("summary", "")
        report_data["file_reviews"] = ai_sections.get("file_reviews", [])
    else:
        logger.info("ℹ️  AI analysis skipped or yielded no results")

    logger.info("Building report...")
    report_builder = ReportBuilder()
    report = report_builder.generate_report(report_data)

    logger.info("Saving report...")
    if args.output:
        out_dir = Path(args.output)
    else:
        out_dir = Path.cwd() / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-UTC")
    filename = f"review-{ts}.md"
    out_path = out_dir / filename
    out_path.write_text(report, encoding="utf-8")
    logger.info(f"Report saved: {out_path}")
    # Log token usage if available from reviewer
    try:
        usage = getattr(reviewer, "get_usage", None)
        if callable(usage):
            tokens = reviewer.get_usage()
            in_t = tokens.get("prompt_tokens", 0)
            out_t = tokens.get("completion_tokens", 0)
            total_t = tokens.get("total_tokens", in_t + out_t)
            logger.info(f"Token usage — input: {in_t}, output: {out_t}, total: {total_t}")
    except Exception as exc:
        logger.debug(f"Token usage logging failed: {exc}")
    logger.info("Analysis completed!")


if __name__ == "__main__":
    main()
