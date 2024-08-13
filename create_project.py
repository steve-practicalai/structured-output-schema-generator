import json
import pandas as pd
import streamlit as st
from model import LLMHelper
from util import Project, ProjectState, TextFile

def create_project_workflow():
    st.subheader("Create New Project")
    
    if "create_project_step" not in st.session_state:
        st.session_state.create_project_step = "GOAL_SET"
    if "temp_project" not in st.session_state:
        st.session_state.temp_project = None

    step = st.session_state.create_project_step
    project = st.session_state.temp_project

    if step == "GOAL_SET":
        project = goal_set_step()
    elif step == "FILE_UPLOADED":
        project = file_upload_step(project)
    elif step == "SCHEMA_RETURNED":
        project = schema_returned_step(project)
    elif step == "SCHEMA_APPROVED":
        project = example_generated_step(project)
    elif step == "COMPLETE":
        return complete_step(project)
    
    if project:
        st.session_state.temp_project = project
    return project

def goal_set_step():
    st.write("Step: Set Project Goal")
    st.write("I'm here to help you create a structured output analysis. What kind of information would you like to extract?")

    if 'user_input' not in st.session_state:
        st.session_state.user_input = None
    
    if 'project_setup' not in st.session_state:
        st.session_state.project_setup = None

    if st.session_state.user_input is None:
        user_input = st.chat_input("e.g. Extract meeting action items")
        if user_input:
            st.session_state.user_input = user_input
            st.rerun()

    if st.session_state.user_input and not st.session_state.project_setup:
        with st.spinner("Setting up project..."):
            st.session_state.project_setup = LLMHelper().project_setup(st.session_state.user_input)
        st.rerun()

    if st.session_state.project_setup is not None:
        st.write(f"Project Goal: {st.session_state.user_input}")
        title = st.text_input("Project Title", key="new_project_title", value=st.session_state.project_setup.title)
        description = st.text_area("Project Description", key="new_project_description", value=st.session_state.project_setup.description)
        prompt = st.text_area("Project Prompt", key="new_project_prompt", value=st.session_state.project_setup.prompt)
        st.session_state.temp_project = Project(title, description, prompt)

        if st.button("Next", key="goal_set_next"):
            st.session_state.create_project_step = "FILE_UPLOADED"
            # Reset goal_set_step session state
            st.session_state.user_input = None
            st.session_state.project_setup = None
            st.rerun()

    return st.session_state.get("temp_project")

def file_upload_step(project):
    st.write("Step: Upload Files")
    uploaded_file = st.file_uploader("Choose a file", key="new_project_file_upload")
    if uploaded_file is not None:
        file = TextFile(uploaded_file.name, uploaded_file.read().decode("utf-8"))
        st.session_state.temp_project.files.append(file)
        st.write(f"File {uploaded_file.name} uploaded successfully!")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back", key="file_upload_back"):
            st.session_state.create_project_step = "GOAL_SET"
            st.rerun()
    with col2:
        if st.button("Next", key="file_upload_next"):
            st.session_state.create_project_step = "SCHEMA_RETURNED"
            st.rerun()
    
    return project

def schema_returned_step(project):
    st.write("Step: Review Returned Schema")
    if 'schema_response' not in st.session_state:
        st.session_state.schema_response = None

    if st.session_state.schema_response is None:
        with st.spinner("Generating Schema..."):
            st.session_state.schema_response = LLMHelper().extract_schema(st.session_state.temp_project.files[0].contents, project.prompt)
        st.rerun()
    else:
        df = pd.DataFrame([vars(field) for field in st.session_state.schema_response.data_fields])

        st.table(df)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back", key="schema_back"):
            st.session_state.create_project_step = "FILE_UPLOADED"
            st.rerun()
    with col2:
        if st.button("Approve Schema", key="schema_approve"):
            st.session_state.create_project_step = "SCHEMA_APPROVED"
            st.session_state.temp_project.schema = st.session_state.schema_response
            st.session_state.schema_response = None
            st.rerun()
    
    return project

def example_generated_step(project):
    st.write("Step: Review Generated Example")
    project = st.session_state.temp_project
    if 'example_response' not in st.session_state:
        st.session_state.example_response = None

    if st.session_state.example_response is None:
        with st.spinner("Generating Example..."):
            st.session_state.example_response = LLMHelper().run_schema(project.prompt, project.files[0].contents, project.schema)
        st.rerun()
    else:
        # convert data_fields to a DataFrame
        df = pd.DataFrame([vars(field) for field in st.session_state.example_response.data_fields])
        st.table(df)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back", key="example_back"):
            st.session_state.create_project_step = "SCHEMA_RETURNED"
            st.rerun()
    with col2:
        if st.button("Complete", key="example_complete"):
            st.session_state.create_project_step = "COMPLETE"
            st.session_state.example_response = None
            st.rerun()
    
    return project

def complete_step(project):
    st.write("Project Creation Complete!")
    
    # Retrieve project details from session state if project is None
    title = project.title if project else st.session_state.get("new_project_title", "")
    description = project.description if project else st.session_state.get("new_project_description", "")
    prompt = project.prompt if project else st.session_state.get("new_project_prompt", "")
    
    # Display the project details for confirmation
    st.write(f"Title: {title}")
    st.write(f"Description: {description}")
    st.write(f"Prompt: {prompt}")
    
    if st.button("Save Project", key="create_project_final"):
        new_project = Project(title, description, prompt)
        new_project.state = ProjectState.COMPLETE
        # Reset the create project state
        st.session_state.create_project_step = "GOAL_SET"
        st.session_state.temp_project = None
        st.session_state.project_created = True
        return new_project
    return None