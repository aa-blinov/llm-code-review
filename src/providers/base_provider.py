from abc import ABC, abstractmethod


class BaseProvider(ABC):
    @abstractmethod
    def fetch_merge_request(self, mr_url: str):
        pass

    @abstractmethod
    def get_comments(self, mr_id: str):
        pass

    @abstractmethod
    def post_comment(self, mr_id: str, comment: str):
        pass

    @abstractmethod
    def get_diff(self, mr_id: str):
        pass

    @abstractmethod
    def get_file_changes(self, mr_id: str):
        pass
