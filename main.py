import json
from typing import List
import pandas as pd
import streamlit as st
from model import LLMHelper, ResponseSchema
from util import FileState, Project, ProjectState, ProjectsManager, TextFile
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
    projects_manager = ProjectsManager()

    with st.sidebar:
        st.title("Projects")
        with st.container(height=400):
            if st.button("Create New Project", key="create_new_project"):
                st.session_state.creating_project = True
                st.session_state.active_project = None
                st.session_state.temp_project = None
                st.rerun()
            selected_project = st.radio(
                "Select a project:",
                options=projects_manager.projects,
                format_func=lambda p: f"{p.title} ({p.state.value})"
            )
    
    st.session_state.active_project = selected_project
    st.session_state.creating_project = False
    
    with st.sidebar:
        with st.container(height=70):
            projects_manager.save_to_file()
        with st.container(height=200):
            st.text("Import Projects")
            uploaded_file = st.file_uploader("Import Projects", label_visibility="collapsed", type="json")
            if st.session_state.active_project is None and uploaded_file is not None:
                projects_manager.load_from_file(uploaded_file)
                st.rerun()



def show_project_details():
    if st.session_state.active_project is not None:
        project: Project = st.session_state.active_project  # Now this is the actual Project object
        
        if "modal" not in st.session_state:
            st.session_state.modal = None

        if "run_data" not in st.session_state:
            st.session_state.run_data = None

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Run", key=f"run_project_{project.title}") or st.session_state.modal == "run_project":
                st.session_state.modal = "run_project"
                st.session_state.active_project = run_project(st.session_state.active_project)
        with col2:
            if st.button("Delete", key=f"delete_project_{project.title}"):
                delete_project(st.session_state.active_project)
        
        st.text_input("Title", value=project.title, key="edit_project_title")
        st.text_area("Description", value=project.description, key="edit_project_description")
        st.text_area("Prompt", value=project.prompt, key="edit_project_prompt")

        # Display schema
        schema_df = pd.DataFrame([{k: v for k, v in vars(field).items() if k != "value"} for field in project.schema.data_fields])
        st.dataframe(schema_df, hide_index=True)

        # Display files
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
            st.dataframe(df, hide_index=True)
            
            # Add download button for CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name="extracted_data.csv",
                mime="text/csv",
            )
        df = pd.DataFrame({"file_name": [file.file_name for file in project.files]})
        st.dataframe(df, hide_index=True)
        
        if st.button("Save Changes", key="save_project_changes"):
            save_project_changes()

def run_project(project: Project):
    project.state = ProjectState.RUNNING
    for file in project.files:
        try:
            file = run_file(file)
        except Exception as e:
            st.error(f"Error processing file {file.file_name}: {str(e)}")
            return
    project.state = ProjectState.COMPLETE
    return project

def run_file(file: TextFile):
    file.state = FileState.RUNNING
    file.results = LLMHelper().run_schema(st.session_state.active_project.prompt, file.contents, st.session_state.active_project.schema)
    file.state = FileState.FINISHED
    return file

def delete_project(project: Project):
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
    
    # logger.error(f"Project 1: {projects_manager.projects[0]}")
    # logger.error(f"Project 1 file 1: {projects_manager.projects[0].files[0]}")
    # logger.error(f"Project 1 file 1 Result 1: {projects_manager.projects[0].files[0].results[0]}")
    st.sidebar.markdown('''
        <a href="https://practicalai.co.nz">
            <img src="https://practicalai.co.nz/content/WhiteLogo-BrandName-OnTransparent.png" alt="Practical:AI"/>
        </a>''',
        unsafe_allow_html=True
    )
    st.sidebar.subheader("OpenAI Structured Outputs")


    if st.session_state.creating_project:
        new_project = create_project_workflow()
        if new_project and new_project.state == ProjectState.COMPLETE:
            projects_manager.append(new_project)
            st.session_state.active_project = new_project
            st.session_state.creating_project = False
            st.session_state.temp_project = None
            st.success("Project created successfully!")
            st.rerun()
    else:
        show_project_list()

        if st.session_state.active_project is not None:
            show_project_details()

if __name__ == "__main__":
    main()