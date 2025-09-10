import pytest

from src.providers.gitlab_provider import GitLabProvider


@pytest.fixture
def provider():
    return GitLabProvider()


def test_fetch_merge_request_data(provider):
    mock_mr_url = "https://gitlab.com/owner/repo/-/merge_requests/1"
    expected_data = {
        "id": 1,
        "title": "Sample Merge Request",
        "description": "This is a sample merge request.",
        "author": "author_name",
        "changes": [],
    }
    data = provider.fetch_merge_request_data(mock_mr_url)
    assert data["id"] == expected_data["id"]
    assert data["title"] == expected_data["title"]
    assert data["description"] == expected_data["description"]
    assert data["author"] == expected_data["author"]


def test_handle_api_error(provider):
    invalid_url = "https://gitlab.com/owner/repo/-/merge_requests/invalid"
    with pytest.raises(Exception) as exc:
        provider.fetch_merge_request_data(invalid_url)
    assert "Error fetching data" in str(exc.value)
