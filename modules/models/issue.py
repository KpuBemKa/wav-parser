from .issue_department import IssueDepartment


class Issue:
    def __init__(self, description: str, departments: list[IssueDepartment]) -> None:
        self.description = description
        self.departments = departments
