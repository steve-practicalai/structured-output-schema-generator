import streamlit as st
from util import Project, ProjectState
from create_project import create_project_workflow

def initialize_session_state():
    if "projects" not in st.session_state:
        st.session_state.projects = []
    if "active_project" not in st.session_state:
        st.session_state.active_project = None
    if "creating_project" not in st.session_state:
        st.session_state.creating_project = False

def show_project_list():
    st.sidebar.title("Projects")
    
    # Use the actual project objects for selection
    selected_project = st.sidebar.radio(
        "Select a project:",
        options=st.session_state.projects,
        format_func=lambda p: f"{p.title} ({p.state.value})"
    )
    
    # Set the active project to the selected project object
    st.session_state.active_project = selected_project
    st.session_state.creating_project = False

def show_project_details():
    if st.session_state.active_project is not None:
        project = st.session_state.active_project  # Now this is the actual Project object
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("Edit Prompt", key=f"edit_prompt_{project.title}"):
                show_edit_prompt_modal(project)
        with col2:
            if st.button("Edit Schema", key=f"edit_schema_{project.title}"):
                show_edit_schema_modal(project)
        with col3:
            if st.button("Add Files", key=f"add_files_{project.title}"):
                show_add_files_modal(project)
        with col4:
            if st.button("Run", key=f"run_project_{project.title}"):
                run_project(project)
        with col5:
            if st.button("Delete", key=f"delete_project_{project.title}"):
                delete_project()

        st.text_input("Title", value=project.title, key="edit_project_title")
        st.text_area("Description", value=project.description, key="edit_project_description")
        
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

def show_add_files_modal(project):
    # Placeholder for add files modal
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        project.files.append(uploaded_file.name)

def run_project(project):
    project.state = ProjectState.RUNNING
    # Placeholder for running project logic

def delete_project():
    if st.button("Confirm Delete"):
        del st.session_state.projects[st.session_state.active_project]
        st.session_state.active_project = None
        st.rerun()

def save_project_changes():
    project = st.session_state.projects[st.session_state.active_project]
    project.title = st.session_state.project_title
    project.description = st.session_state.project_description

def main():
    initialize_session_state()
    
    st.title("OpenAI Structured Output Schema Generator")

    st.sidebar.image("https://practicalai.co.nz/content/WhiteLogo-BrandName-OnTransparent.png")
    if st.sidebar.button("Create New Project", key="create_new_project"):
        st.session_state.creating_project = True
        st.session_state.active_project = None
        st.session_state.temp_project = None
        st.rerun()

    if st.session_state.creating_project:
        new_project = create_project_workflow()
        if new_project and new_project.state == ProjectState.COMPLETE:
            st.session_state.projects.append(new_project)
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