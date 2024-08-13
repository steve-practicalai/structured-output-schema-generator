from enum import Enum
import html
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
        if 'projects' not in st.session_state:
            st.session_state.projects = []

    @property
    def projects(self) -> List[Project]:
        return st.session_state.projects

    def save_to_file(self):
        if(self.projects):
            active_project = st.session_state.active_project
            for i, project in enumerate(self.projects):
                if project is active_project:
                    st.session_state.projects[i] = active_project
                    break
            else:
                st.session_state.projects.append(active_project)
            projects_data = [project.to_dict() for project in self.projects]
            json_str = json.dumps(projects_data, indent=2)
            st.download_button(
                label="Export Projects",
                data=json_str,
                file_name="projects.json",
                mime="application/json"
            )

    def load_from_file(self):
        st.text("Import Projects")
        uploaded_file = st.file_uploader("Import Projects", label_visibility="collapsed", type="json")
        if uploaded_file is not None:
            projects_data = json.load(uploaded_file)
            loaded_projects = []
            for data in projects_data:
                project = Project.from_dict(data)
                # Ensure file contents are properly loaded
                project.files = [TextFile.from_dict(file_data) for file_data in data.get('files', [])]
                loaded_projects.append(project)
            st.session_state.projects = loaded_projects
            if(loaded_projects):
                st.session_state.active_project = loaded_projects[0]
                st.success("Projects loaded successfully!")

    def append(self, project: Project):
        st.session_state.projects.append(project)

    def __setitem__(self, key, value):
        st.session_state.projects[key] = value

    def __getitem__(self, key):
        return st.session_state.projects[key]

    def __delitem__(self, key: int):
        del st.session_state.projects[key]

    def __len__(self):
        return len(st.session_state.projects)