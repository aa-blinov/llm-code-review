import pytest

from src.providers.github_provider import GitHubProvider


@pytest.fixture
def github_provider():
    return GitHubProvider()


def test_fetch_merge_request_data(github_provider):
    url = "https://api.github.com/repos/user/repo/pulls/1"
    data = github_provider.fetch_merge_request_data(url)
    assert data is not None
    assert "id" in data
    assert "title" in data
    assert "user" in data


def test_fetch_merge_request_data_invalid_url(github_provider):
    url = "https://api.github.com/repos/user/repo/pulls/invalid"
    with pytest.raises(Exception):
        github_provider.fetch_merge_request_data(url)


def test_parse_merge_request_data(github_provider):
    sample_data = {"id": 1, "title": "Sample PR", "user": {"login": "user"}, "body": "This is a sample pull request."}
    parsed_data = github_provider.parse_merge_request_data(sample_data)
    assert parsed_data["id"] == 1
    assert parsed_data["title"] == "Sample PR"
    assert parsed_data["author"] == "user"
