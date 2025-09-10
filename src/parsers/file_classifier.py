class FileClassifier:
    def __init__(self):
        self.file_types = {
            "python": [".py"],
            "markdown": [".md"],
            "text": [".txt"],
            "javascript": [".js"],
            "html": [".html"],
            "css": [".css"],
            "json": [".json"],
            "xml": [".xml"],
            "other": [],
        }

    def classify_file(self, file_name):
        extension = self.get_file_extension(file_name)
        for file_type, extensions in self.file_types.items():
            if extension in extensions:
                return file_type
        return "other"

    def get_file_extension(self, file_name):
        return file_name.split(".")[-1] if "." in file_name else ""

    def classify_files(self, file_list):
        classified_files = {}
        for file in file_list:
            file_type = self.classify_file(file)
            if file_type not in classified_files:
                classified_files[file_type] = []
            classified_files[file_type].append(file)
        return classified_files
