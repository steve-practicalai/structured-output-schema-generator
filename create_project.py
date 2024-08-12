import streamlit as st
from util import Project, ProjectState

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
        project = schema_approved_step(project)
    elif step == "EXAMPLE_GENERATED":
        project = example_generated_step(project)
    elif step == "COMPLETE":
        return complete_step(project)
    
    if project:
        st.session_state.temp_project = project
    return project

def goal_set_step():
    st.write("Step: Set Project Goal")
    
    title = st.text_input("Project Title", key="new_project_title")
    description = st.text_area("Project Description", key="new_project_description")
    prompt = st.text_area("Project Prompt", key="new_project_prompt")
    
    if st.button("Next", key="goal_set_next"):
        project = Project(title, description, prompt)
        st.session_state.create_project_step = "FILE_UPLOADED"
        st.session_state.temp_project = project
        st.rerun()
    
    return st.session_state.get("temp_project")

def file_upload_step(project):
    st.write("Step: Upload Files")
    uploaded_file = st.file_uploader("Choose a file", key="new_project_file_upload")
    if uploaded_file is not None:
        st.write(f"File {uploaded_file.name} uploaded successfully!")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Next", key="file_upload_next"):
            st.session_state.create_project_step = "SCHEMA_RETURNED"
            st.rerun()
    with col2:
        if st.button("Back", key="file_upload_back"):
            st.session_state.create_project_step = "GOAL_SET"
            st.rerun()
    
    return project

def schema_returned_step(project):
    st.write("Step: Review Returned Schema")
    st.text_area("Generated Schema", value="Sample schema...", disabled=True, key="new_project_schema")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Approve Schema", key="schema_approve"):
            st.session_state.create_project_step = "SCHEMA_APPROVED"
            st.rerun()
    with col2:
        if st.button("Back", key="schema_back"):
            st.session_state.create_project_step = "FILE_UPLOADED"
            st.rerun()
    
    return project

def schema_approved_step(project):
    st.write("Step: Generate Example")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate Example", key="generate_example"):
            st.write("Example generated!")
            st.session_state.create_project_step = "EXAMPLE_GENERATED"
            st.rerun()
    with col2:
        if st.button("Back", key="schema_approved_back"):
            st.session_state.create_project_step = "SCHEMA_RETURNED"
            st.rerun()
    
    return project

def example_generated_step(project):
    st.write("Step: Review Generated Example")
    st.text_area("Generated Example", value="Sample example...", disabled=True, key="new_project_example")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Complete", key="example_complete"):
            st.session_state.create_project_step = "COMPLETE"
            st.rerun()
    with col2:
        if st.button("Back", key="example_back"):
            st.session_state.create_project_step = "SCHEMA_APPROVED"
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
    
    if st.button("Create Project", key="create_project_final"):
        new_project = Project(title, description, prompt)
        new_project.state = ProjectState.COMPLETE
        # Reset the create project state
        st.session_state.create_project_step = "GOAL_SET"
        st.session_state.temp_project = None
        st.session_state.project_created = True
        return new_project
    return None