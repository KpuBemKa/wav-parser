from modules.models.issue_department import IssueDepartment


class Issue:
    def __init__(self, description: str, department: IssueDepartment) -> None:
        self.description = description
        self.department = department

    def to_dict(self):
        return {
            "description": self.description,
            "departments": self.department.value,
        }
