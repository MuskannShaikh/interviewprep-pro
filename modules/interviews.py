"""
Interview Manager Module
Handles CRUD operations for interview records
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from database.db_manager import DatabaseManager

class InterviewManager:
    """Manages interview CRUD operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def show_interview_form(self, user_id: int, interview_id: int = None):
        """Display form to add or edit interview"""
        
        # Check if editing existing interview
        existing_interview = None
        if interview_id:
            existing_interview = self.db.get_interview_by_id(interview_id)
            st.subheader("✏️ Edit Interview")
        else:
            st.subheader("➕ Add New Interview")
        
        with st.form("interview_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input(
                    "Company Name *",
                    value=existing_interview['company_name'] if existing_interview else "",
                    placeholder="e.g., Google, Microsoft, Amazon"
                )
                
                role = st.text_input(
                    "Role/Position *",
                    value=existing_interview['role'] if existing_interview else "",
                    placeholder="e.g., Software Engineer, Data Analyst"
                )
                
                interview_date = st.date_input(
                    "Interview Date *",
                    value=datetime.strptime(existing_interview['interview_date'], '%Y-%m-%d').date() 
                          if existing_interview else date.today()
                )
            
            with col2:
                status = st.selectbox(
                    "Status *",
                    options=['Applied', 'Interviewed', 'Selected', 'Rejected'],
                    index=['Applied', 'Interviewed', 'Selected', 'Rejected'].index(
                        existing_interview['status']) if existing_interview else 0
                )
                
                preparation_level = st.slider(
                    "Preparation Level *",
                    min_value=1,
                    max_value=5,
                    value=existing_interview['preparation_level'] if existing_interview else 3,
                    help="Rate your preparation from 1 (Low) to 5 (High)"
                )
                
                technical_topics = st.text_input(
                    "Technical Topics Covered",
                    value=existing_interview.get('technical_topics', '') if existing_interview else "",
                    placeholder="e.g., DSA, System Design, SQL"
                )
            
            notes = st.text_area(
                "Notes",
                value=existing_interview['notes'] if existing_interview else "",
                placeholder="Add any additional notes, feedback, or observations...",
                height=100
            )
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                submit = st.form_submit_button(
                    "💾 Update" if existing_interview else "➕ Add Interview",
                    use_container_width=True
                )
            
            with col2:
                if existing_interview:
                    cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
                    if cancel:
                        st.session_state.editing_interview_id = None
                        st.rerun()
            
            if submit:
                # Validate required fields
                if not company_name or not role:
                    st.error("Company Name and Role are required!")
                    return
                
                # Add or update interview
                if existing_interview:
                    success = self.db.update_interview(
                        interview_id, company_name, role, str(interview_date),
                        status, preparation_level, notes, technical_topics
                    )
                    if success:
                        st.success("✅ Interview updated successfully!")
                        st.session_state.editing_interview_id = None
                        st.rerun()
                    else:
                        st.error("Failed to update interview")
                else:
                    interview_id = self.db.add_interview(
                        user_id, company_name, role, str(interview_date),
                        status, preparation_level, notes, technical_topics
                    )
                    if interview_id:
                        st.success("✅ Interview added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add interview")
    
    def show_interviews_list(self, user_id: int):
        """Display list of all interviews with actions"""
        
        interviews = self.db.get_user_interviews(user_id)
        
        if not interviews:
            st.info("📋 No interviews recorded yet. Add your first interview above!")
            return
        
        st.subheader(f"📊 Your Interviews ({len(interviews)} Total)")
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(interviews)
        
        # Add filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.multiselect(
                "Filter by Status",
                options=['Applied', 'Interviewed', 'Selected', 'Rejected'],
                default=['Applied', 'Interviewed', 'Selected', 'Rejected']
            )
        
        with col2:
            sort_by = st.selectbox(
                "Sort by",
                options=['Interview Date (Newest)', 'Interview Date (Oldest)', 
                        'Company Name', 'Preparation Level']
            )
        
        # Apply filters
        filtered_df = df[df['status'].isin(status_filter)]
        
        # Apply sorting
        if sort_by == 'Interview Date (Newest)':
            filtered_df = filtered_df.sort_values('interview_date', ascending=False)
        elif sort_by == 'Interview Date (Oldest)':
            filtered_df = filtered_df.sort_values('interview_date', ascending=True)
        elif sort_by == 'Company Name':
            filtered_df = filtered_df.sort_values('company_name')
        elif sort_by == 'Preparation Level':
            filtered_df = filtered_df.sort_values('preparation_level', ascending=False)
        
        # Display interviews as cards
        for idx, interview in filtered_df.iterrows():
            self._display_interview_card(interview)
    
    def _display_interview_card(self, interview):
        """Display a single interview as a card"""
        
        # Status color coding
        status_colors = {
            'Applied': '🟡',
            'Interviewed': '🔵',
            'Selected': '🟢',
            'Rejected': '🔴'
        }
        
        # Preparation level stars
        prep_stars = '⭐' * interview['preparation_level']
        
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.markdown(f"### {status_colors.get(interview['status'], '⚪')} {interview['company_name']}")
                st.markdown(f"**Role:** {interview['role']}")
            
            with col2:
                st.markdown(f"**Date:** {interview['interview_date']}")
                st.markdown(f"**Status:** {interview['status']}")
            
            with col3:
                st.markdown(f"**Preparation:** {prep_stars}")
                if interview.get('technical_topics'):
                    st.markdown(f"**Topics:** {interview['technical_topics']}")
            
            with col4:
                if st.button("✏️", key=f"edit_{interview['interview_id']}", help="Edit"):
                    st.session_state.editing_interview_id = interview['interview_id']
                    st.rerun()
                
                if st.button("🗑️", key=f"delete_{interview['interview_id']}", help="Delete"):
                    if self.db.delete_interview(interview['interview_id']):
                        st.success("Interview deleted!")
                        st.rerun()
            
            # Show notes if present
            if interview.get('notes'):
                with st.expander("📝 View Notes"):
                    st.write(interview['notes'])
            
            st.divider()


def show_interview_management_page(db_manager: DatabaseManager, user_id: int):
    """Main page for interview management"""
    
    manager = InterviewManager(db_manager)
    
    # Check if editing an existing interview
    editing_id = st.session_state.get('editing_interview_id', None)
    
    # Show form
    manager.show_interview_form(user_id, editing_id)
    
    st.markdown("---")
    
    # Show list of interviews
    manager.show_interviews_list(user_id)