import streamlit as st
from util import FileState, ProjectsManager, ProjectState, TextFile
from create_project import create_project_workflow
from model import LLMHelper
import pandas as pd
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

projects_manager = ProjectsManager()

def main():
    setup_sidebar()
    
    if st.session_state.get('current_view') == 'create_project':
        create_project_workflow()
    else:
        show_project_list()

def setup_sidebar():
    st.sidebar.markdown('''
        <a href="https://practicalai.co.nz">
            <img src="https://practicalai.co.nz/content/WhiteLogo-BrandName-OnTransparent.png" alt="Practical:AI"/>
        </a>''',
        unsafe_allow_html=True
    )
    st.sidebar.subheader("OpenAI Structured Outputs")
    
    st.sidebar.button("Create New Project", on_click=set_current_view, args=('create_project',))

    project_list = [p.title for p in projects_manager.projects]
    st.sidebar.selectbox(
        "Select a project:",
        options=project_list,
        format_func=lambda x: f"{x} ({next(p for p in projects_manager.projects if p.title == x).state.value})",
        key='selected_project',
        on_change=update_selected_project
    )

    st.sidebar.file_uploader("Import Projects", type="json", on_change=import_projects, key="project_import")

    if projects_manager.projects:
        st.sidebar.download_button(
            label="Export Projects",
            data=projects_manager.save_to_file(),
            file_name="projects.json",
            mime="application/json"
        )

def set_current_view(view):
    st.session_state['current_view'] = view
    st.session_state.pop('confirm_delete', None)

def update_selected_project():
    st.session_state['current_view'] = 'project_details'
    st.session_state.pop('confirm_delete', None)

def import_projects():
    if st.session_state.project_import:
        projects_manager.load_from_file(st.session_state.project_import)

def show_project_list():
    st.title("Projects")
    for project in projects_manager.projects:
        st.write(f"{project.title} ({project.state.value})")
    
    if st.session_state.get('selected_project'):
        project = next(p for p in projects_manager.projects if p.title == st.session_state.selected_project)
        show_project_details(project)

def show_project_details(project):
    st.title(project.title)
    st.write(project.description)
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("Run", key=f"run_project_{project.title}", on_click=run_project, args=(project,))
    with col2:
        st.button("Delete", key=f"delete_project_{project.title}", on_click=confirm_delete_project, args=(project,))
    
    if st.session_state.get('confirm_delete'):
        st.button("Confirm Delete", key=f"confirm_delete_{project.title}", on_click=delete_project, args=(project,))
    
    new_title = st.text_input("Title", value=project.title, key="edit_project_title")
    new_description = st.text_area("Description", value=project.description, key="edit_project_description")
    new_prompt = st.text_area("Prompt", value=project.prompt, key="edit_project_prompt")

    st.button("Save Changes", on_click=save_project_changes, args=(project, new_title, new_description, new_prompt))

    display_schema(project)
    display_files(project)
    display_results(project)

def confirm_delete_project(project):
    st.session_state['confirm_delete'] = True

def delete_project(project):
    projects_manager.delete_project(project)
    st.session_state.pop('selected_project', None)
    st.session_state.pop('confirm_delete', None)
    st.session_state['current_view'] = 'project_list'

def save_project_changes(project, new_title, new_description, new_prompt):
    if (new_title != project.title or 
        new_description != project.description or 
        new_prompt != project.prompt):
        project.title = new_title
        project.description = new_description
        project.prompt = new_prompt
        projects_manager.save_project(project)
        st.success("Project changes saved successfully!")

def display_schema(project):
    if project.schema:
        st.subheader("Schema")
        schema_df = pd.DataFrame([{k: v for k, v in vars(field).items() if k != "value"} for field in project.schema.data_fields])
        st.dataframe(schema_df, hide_index=True)

def display_files(project):
    st.subheader("Files")
    st.file_uploader("Add files", accept_multiple_files=True, key="add_files", on_change=add_files_to_project, args=(project,))

    if project.files:
        df = pd.DataFrame({"file_name": [file.file_name for file in project.files]})
        st.dataframe(df, hide_index=True)

def add_files_to_project(project):
    if st.session_state.add_files:
        for file in st.session_state.add_files:
            file_contents = file.read().decode("utf-8")
            new_file = TextFile(file.name, file_contents)
            project.files.append(new_file)
        projects_manager.save_project(project)
        st.success(f"{len(st.session_state.add_files)} file(s) added successfully!")
        st.session_state.add_files = None

def display_results(project):
    if project.state == ProjectState.COMPLETE and project.files and project.files[0].results:
        st.subheader("Results")
        df = pd.DataFrame([{field.name: field.value for field in result.data_fields} for result in project.files[0].results])
        st.dataframe(df, hide_index=True)
        
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name="extracted_data.csv",
            mime="text/csv",
        )

def run_project(project):
    project.state = ProjectState.RUNNING
    projects_manager.save_project(project)
    
    for file in project.files:
        try:
            file = run_file(file, project)
        except Exception as e:
            logger.error(f"Error processing file {file.file_name}: {str(e)}")
            project.state = ProjectState.ERROR
            projects_manager.save_project(project)
            return
    
    project.state = ProjectState.COMPLETE
    projects_manager.save_project(project)

def run_file(file, project):
    file.state = FileState.RUNNING
    file.results = LLMHelper().run_schema(project.prompt, file.contents, project.schema)
    file.state = FileState.FINISHED
    return file

if __name__ == "__main__":
    main()