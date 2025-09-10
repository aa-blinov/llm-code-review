class MergeRequest:
    def __init__(self, mr_id, title, description, author, created_at, updated_at, files_changed):
        self.id = mr_id
        self.title = title
        self.description = description
        self.author = author
        self.created_at = created_at
        self.updated_at = updated_at
        self.files_changed = files_changed


class ReviewReport:
    def __init__(self, merge_request, comments):
        self.merge_request = merge_request
        self.comments = comments

    def add_comment(self, comment):
        self.comments.append(comment)

    def generate_report(self):
        report_content = f"## Review Report for Merge Request: {self.merge_request.title}\n"
        report_content += f"**Author:** {self.merge_request.author}\n"
        report_content += f"**Created At:** {self.merge_request.created_at}\n"
        report_content += f"**Updated At:** {self.merge_request.updated_at}\n"
        report_content += f"**Description:** {self.merge_request.description}\n\n"
        report_content += "### Comments:\n"
        for comment in self.comments:
            report_content += f"- {comment}\n"
        return report_content
