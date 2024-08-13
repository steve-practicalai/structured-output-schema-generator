from enum import Enum
from typing import List

class ProjectState(Enum):
    GOAL_SET = "Goal Set"
    FILE_UPLOADED = "File Uploaded"
    SCHEMA_RETURNED = "Schema Returned"
    SCHEMA_APPROVED = "Schema Approved"
    EXAMPLE_GENERATED = "Example Generated"
    COMPLETE = "Complete"
    RUNNING = "Running"

class TextFile:
    def __init__(self, file_name: str, contents: str):
        self.file_path = file_name
        self.contents = contents

class Project:
    def __init__(self, title: str, description: str, prompt: str):
        self.title = title
        self.description = description
        self.prompt = prompt
        self.files: List[TextFile] = []
        self.output: List[str] = []
        self.schema = None
        self.state = ProjectState.GOAL_SET

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "prompt": self.prompt,
            "files": self.files,
            "output": self.output,
            "schema": self.schema,
            "state": self.state.value
        }

    @classmethod
    def from_dict(cls, data):
        project = cls(data["title"], data["description"], data["prompt"])
        project.files = data["files"]
        project.output = data["output"]
        project.schema = data["schema"]
        project.state = ProjectState(data["state"])
        return project