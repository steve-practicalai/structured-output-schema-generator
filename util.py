from enum import Enum
import json
from typing import List
import streamlit as st
import logging

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

from model import ResponseSchema

class ProjectState(Enum):
    GOAL_SET = "Goal Set"
    FILE_UPLOADED = "File Uploaded"
    SCHEMA_RETURNED = "Schema Returned"
    SCHEMA_APPROVED = "Schema Approved"
    EXAMPLE_GENERATED = "Example Generated"
    COMPLETE = "Complete"
    RUNNING = "Running"
    ERROR = "Error"

class FileState(Enum):
    NOT_STARTED = "Not Started"
    RUNNING = "Running"
    FINISHED = "Finished"

class TextFile:
    def __init__(self, file_name: str, contents: str, results: List[ResponseSchema] | None = None, state: FileState = FileState.NOT_STARTED):
        self.file_name = file_name
        self.contents = contents
        self.results = results if results is not None else []
        self.state = state

    def to_dict(self):
        return {
            "file_name": self.file_name,
            "contents": self.contents,
            "results": [result.to_dict() for result in self.results] if self.results else [],
            "state": self.state.value
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            file_name=data["file_name"],
            contents=data["contents"],
            results=[ResponseSchema.from_dict(result) for result in data.get("results", [])],
            state=FileState(data.get("state", FileState.NOT_STARTED.value))
        )

class Project:
    def __init__(self, title: str, description: str, prompt: str):
        self.title = title
        self.description = description
        self.prompt = prompt
        self.files: List[TextFile] = []
        self.schema = None
        self.state = ProjectState.GOAL_SET

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "prompt": self.prompt,
            "files": [file.to_dict() for file in self.files],
            "schema": self.schema.to_dict() if self.schema else None,
            "state": self.state.value
        }

    @classmethod
    def from_dict(cls, data):
        project = cls(data["title"], data["description"], data["prompt"])
        project.files = [TextFile.from_dict(file_data) for file_data in data["files"]]
        project.schema = ResponseSchema.from_dict(data["schema"]) if data["schema"] else None
        project.state = ProjectState(data["state"])
        return project

class ProjectsManager:
    def __init__(self):
        if 'projects' not in st.session_state:
            st.session_state.projects = []

    @property
    def projects(self) -> List[Project]:
        return st.session_state.projects

    def save_project(self, project):
        if project not in self.projects:
            self.projects.append(project)
        else:
            index = self.projects.index(project)
            self.projects[index] = project

    def delete_project(self, project):
        if project in self.projects:
            self.projects.remove(project)

    def save_to_file(self):
        if self.projects:
            projects_data = [project.to_dict() for project in self.projects]
            return json.dumps(projects_data, indent=2)

    def load_from_file(self, uploaded_file):
        projects_data = json.load(uploaded_file)
        loaded_projects = []
        for data in projects_data:
            project = Project.from_dict(data)
            loaded_projects.append(project)
        st.session_state.projects = loaded_projects
        st.session_state.selected_project = loaded_projects[0].title
        st.success("Projects loaded successfully!")

projects_manager = ProjectsManager()