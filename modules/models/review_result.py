from .issue import Issue


class ReviewResult:
    def __init__(self, corrected_text: str = "", summary: str = "", issues: list[Issue] = [], completed= True) -> None:
        self.corrected_text = corrected_text
        self.summary = summary
        self.issues = issues
        self.completed = completed
