import streamlit as st
from util import Project, ProjectState, TextFile, projects_manager
from model import LLMHelper
import pandas as pd

def create_project_workflow():
    st.title("Create New Project")
    
    if "create_project_step" not in st.session_state:
        st.session_state.create_project_step = "GOAL_SET"
    if "temp_project" not in st.session_state:
        st.session_state.temp_project = None

    step = st.session_state.create_project_step

    if step == "GOAL_SET":
        goal_set_step()
    elif step == "FILE_UPLOAD":
        file_upload_step()
    elif step == "SCHEMA_REVIEW":
        schema_review_step()
    elif step == "COMPLETE":
        complete_step()

def goal_set_step():
    st.write("Step 1: Set Project Goal")
    user_input = st.text_input("What information would you like to extract?", key="project_goal")
    
    st.button("Next", on_click=setup_project, args=(user_input,))

def setup_project(user_input):
    with st.spinner("Setting up project..."):
        project_setup = LLMHelper().project_setup(user_input)
    st.session_state.temp_project = Project(project_setup.title, project_setup.description, project_setup.prompt)
    st.session_state.create_project_step = "FILE_UPLOAD"

def file_upload_step():
    st.write("Step 2: Upload File")
    st.file_uploader("Choose a file", key="new_project_file_upload", on_change=process_uploaded_file)
    
    st.button("Back", on_click=go_back_to_goal_set)

def process_uploaded_file():
    if st.session_state.new_project_file_upload:
        file_contents = st.session_state.new_project_file_upload.read().decode("utf-8")
        file = TextFile(st.session_state.new_project_file_upload.name, file_contents)
        st.session_state.temp_project.files = [file]
        st.session_state.create_project_step = "SCHEMA_REVIEW"

def go_back_to_goal_set():
    st.session_state.create_project_step = "GOAL_SET"

def schema_review_step():
    st.write("Step 3: Review Schema")
    project = st.session_state.temp_project
    
    if 'schema_response' not in st.session_state:
        with st.spinner("Generating Schema..."):
            st.session_state.schema_response = LLMHelper().extract_schema(project.files[0].contents, project.prompt)
    
    schema_df = pd.DataFrame([vars(field) for field in st.session_state.schema_response.data_fields])
    st.table(schema_df)
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("Back", on_click=go_back_to_file_upload)
    with col2:
        st.button("Approve Schema", on_click=approve_schema)

def go_back_to_file_upload():
    st.session_state.create_project_step = "FILE_UPLOAD"
    st.session_state.pop('schema_response', None)

def approve_schema():
    project = st.session_state.temp_project
    project.schema = st.session_state.schema_response
    project.state = ProjectState.SCHEMA_APPROVED
    st.session_state.create_project_step = "COMPLETE"
    st.session_state.pop('schema_response', None)

def complete_step():
    st.write("Project Creation Complete!")
    project = st.session_state.temp_project
    
    st.write(f"Title: {project.title}")
    st.write(f"Description: {project.description}")
    st.write(f"Prompt: {project.prompt}")
    
    st.button("Save Project", on_click=save_project)
    st.button("Cancel", on_click=cancel_project_creation)

def save_project():
    project = st.session_state.temp_project
    project.state = ProjectState.COMPLETE
    projects_manager.save_project(project)
    st.session_state['current_view'] = 'project_details'
    cleanup_project_creation()
    st.success("Project created successfully!")

def cancel_project_creation():
    cleanup_project_creation()

def cleanup_project_creation():
    st.session_state.pop('create_project_step', None)
    st.session_state.pop('temp_project', None)
   

if __name__ == "__main__":
    create_project_workflow()