import json
from typing import List
import pandas as pd
import streamlit as st
from model import LLMHelper, ResponseSchema
from util import Project, ProjectState, ProjectsManager, TextFile
from create_project import create_project_workflow
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def initialize_session_state():
    if "active_project" not in st.session_state:
        st.session_state.active_project = None
    if "creating_project" not in st.session_state:
        st.session_state.creating_project = False

def show_project_list():
    st.sidebar.title("Projects")
    projects_manager = ProjectsManager()

    # Rest of the function remains the same
    selected_project = st.sidebar.radio(
        "Select a project:",
        options=projects_manager.projects,
        format_func=lambda p: f"{p.title} ({p.state.value})"
    )
    
    st.session_state.active_project = selected_project
    st.session_state.creating_project = False
    
    if st.sidebar.button("Save Projects", key=f"save_projects"):
        projects_manager.save_to_file()

    if st.sidebar.button("Load Projects", key=f"load_projects"):
        projects_manager.load_from_file()



def show_project_details():
    if st.session_state.active_project is not None:
        project: Project = st.session_state.active_project  # Now this is the actual Project object
        
        if "modal" not in st.session_state:
            st.session_state.modal = None

        if "run_data" not in st.session_state:
            st.session_state.run_data = None

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("Edit Prompt", key=f"edit_prompt_{project.title}"):
                show_edit_prompt_modal(project)
        with col2:
            if st.button("Edit Schema", key=f"edit_schema_{project.title}"):
                show_edit_schema_modal(project)
        with col3:
            if st.button("Run", key=f"run_project_{project.title}") or st.session_state.modal == "run_project":
                st.session_state.modal = "run_project"
                st.session_state.run_data = run_project()
        with col4:
            if st.button("Delete", key=f"delete_project_{project.title}"):
                delete_project()
        
        st.text_input("Title", value=project.title, key="edit_project_title")
        st.text_area("Description", value=project.description, key="edit_project_description")
        st.subheader("Files")
        uploaded_files = st.file_uploader("Choose files", accept_multiple_files=True, key="add_files")
        if uploaded_files:
            for file in uploaded_files:
                file_contents = file.read().decode("utf-8")
                new_file = TextFile(file.name, file_contents)
                st.session_state.active_project.files.append(new_file)
                st.session_state.modal = ""
                logger.error((f"{len(uploaded_files)} file(s) added successfully!"))
            
            st.success(f"{len(uploaded_files)} file(s) added successfully!")
        else:
            st.warning("No files selected. Please choose files before clicking 'Add Files'.")
        if st.session_state.run_data is not None:
            st.session_state.modal = ""
            df = pd.DataFrame(st.session_state.run_data)
            st.dataframe(df)
            
            # Add download button for CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name="extracted_data.csv",
                mime="text/csv",
            )
        df = pd.DataFrame({"file_name": [file.file_name for file in project.files]})
        st.table(df)
        
        if st.button("Save Changes", key="save_project_changes"):
            save_project_changes()

def show_edit_prompt_modal(project):
    # Placeholder for edit prompt modal
    st.text_area("Edit Prompt", value=project.prompt, key="edit_prompt")
    if st.button("Save Prompt"):
        project.prompt = st.session_state.edit_prompt

def show_edit_schema_modal(project):
    # Placeholder for edit schema modal
    st.text_area("Edit Schema", value=project.schema, key="edit_schema")
    if st.button("Save Schema"):
        project.schema = st.session_state.edit_schema

def show_add_files_modal():
    uploaded_files = st.file_uploader("Choose files", accept_multiple_files=True, key="add_files")
    if uploaded_files:
        for file in uploaded_files:
            file_contents = file.read().decode("utf-8")
            new_file = TextFile(file.name, file_contents)
            st.session_state.active_project.files.append(new_file)
            st.session_state.modal = ""
            logger.error((f"{len(uploaded_files)} file(s) added successfully!"))
        
        st.success(f"{len(uploaded_files)} file(s) added successfully!")
    else:
        st.warning("No files selected. Please choose files before clicking 'Add Files'.")

def run_project():
    project = st.session_state.active_project
    all_data = []
    for file in project.files:
        try:
            responses: List[ResponseSchema] = LLMHelper().run_schema(project.prompt, file.contents, project.schema)
            for response in responses:
                row = {'File': file.file_name}
                for field in response.data_fields:
                    row[field.name] = field.value
                all_data.append(row)
        except Exception as e:
            st.error(f"Error processing file {file.file_name}: {str(e)}")
            return

    return all_data

def delete_project():
    if st.button("Confirm Delete"):
        projects_manager = ProjectsManager()
        del projects_manager[st.session_state.active_project]
        st.session_state.active_project = None
        st.rerun()

def save_project_changes():
    projects_manager = ProjectsManager()
    project = projects_manager[st.session_state.active_project]
    project.title = st.session_state.project_title
    project.description = st.session_state.project_description

def main():
    initialize_session_state()
    projects_manager = ProjectsManager()
    st.title("OpenAI Structured Output Schema Generator!")

    st.sidebar.image("https://practicalai.co.nz/content/WhiteLogo-BrandName-OnTransparent.png")
    if st.sidebar.button("Create New Project", key="create_new_project"):
        st.session_state.creating_project = True
        st.session_state.active_project = None
        st.session_state.temp_project = None
        st.rerun()

    if st.session_state.creating_project:
        new_project = create_project_workflow()
        if new_project and new_project.state == ProjectState.COMPLETE:
            projects_manager.append(new_project)
            st.session_state.active_project = new_project
            st.session_state.creating_project = False
            st.session_state.temp_project = None
            st.success("Project created successfully!")
            st.rerun()

    if not st.session_state.creating_project:
        show_project_list()

    if st.session_state.active_project is not None:
        show_project_details()

if __name__ == "__main__":
    main()