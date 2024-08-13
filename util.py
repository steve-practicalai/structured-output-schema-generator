from enum import Enum
import json
from typing import Dict, List
import streamlit as st

from model import ResponseSchema

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
        self.file_name = file_name
        self.contents = contents

    def to_dict(self):
        return {
            "file_name": self.file_name,
            "contents": self.contents
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data["file_name"], data["contents"])

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
            "files": [file.to_dict() for file in self.files],
            "output": self.output,
            "schema": self.schema.to_dict() if self.schema else None,
            "state": self.state.value
        }

    @classmethod
    def from_dict(cls, data):
        project = cls(data["title"], data["description"], data["prompt"])
        project.files = [TextFile.from_dict(file_data) for file_data in data["files"]]
        project.output = data["output"]
        project.schema = ResponseSchema.from_dict(data["schema"]) if data["schema"] else None
        project.state = ProjectState(data["state"])
        return project
    

class ProjectsManager:
    def __init__(self):
        self._initialize_local_storage()
        if "projects" not in st.session_state:
            st.session_state.projects = self._load_projects()
    

    def _initialize_local_storage(self):
        st.components.v1.html(
            """
            <script>
            if (!localStorage.getItem('projects')) {
                localStorage.setItem('projects', JSON.stringify([]));
            }
            const projects = localStorage.getItem('projects');
            window.parent.postMessage({type: 'SET_PROJECTS', projects: projects}, '*');
            </script>
            """,
            height=0,
        )

    @property
    def projects(self) -> List[Project]:
        return st.session_state.projects

    def _load_projects(self) -> List[Project]:
        if "projects_data" not in st.session_state:
            return []
        
        projects_data = json.loads(st.session_state.projects_data)
        return [Project.from_dict(project_data) for project_data in projects_data]

    def _save_projects(self):
        projects_data = [project.to_dict() for project in self.projects]
        projects_json = json.dumps(projects_data)
        st.components.v1.html(
            f"""
            <script>
            localStorage.setItem('projects', '{projects_json}');
            </script>
            """,
            height=0,
        )

    def __setitem__(self, key, value):
        self.projects[key] = value
        self._save_projects()

    def __getitem__(self, key):
        return self.projects[key]

    def __delitem__(self, key: int):
        del self.projects[key]
        self._save_projects()

    def append(self, project: Project):
        self.projects.append(project)
        self._save_projects()

    def __len__(self):
        return len(self.projects)

