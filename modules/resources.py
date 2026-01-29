"""
Reminders Module
Handles email reminders for upcoming interviews
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class ReminderManager:
    """Manages interview reminders"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def show_reminders_page(self, user_id: int):
        """Display reminders management page"""
        
        st.title("🔔 Interview Reminders")
        st.markdown("Never miss an interview! Set up automatic email reminders.")
        
        # Get upcoming interviews
        interviews = self.db.get_user_interviews(user_id)
        df = pd.DataFrame(interviews)
        
        if df.empty:
            st.info("📋 No interviews scheduled. Add some interviews first!")
            return
        
        # Filter upcoming interviews
        df['interview_date'] = pd.to_datetime(df['interview_date'])
        today = pd.Timestamp.now().normalize()
        upcoming = df[df['interview_date'] >= today].sort_values('interview_date')
        
        if upcoming.empty:
            st.info("🎉 No upcoming interviews scheduled!")
            return
        
        st.subheader(f"📅 Upcoming Interviews ({len(upcoming)})")
        
        # Display upcoming interviews with reminder options
        for idx, interview in upcoming.iterrows():
            self._display_interview_reminder_card(interview, user_id)
        
        # Email configuration
        st.markdown("---")
        st.subheader("⚙️ Email Configuration")
        
        with st.expander("📧 Configure Email Settings", expanded=False):
            st.info("""
            **Note:** For security reasons, email functionality requires your own SMTP configuration.
            
            **How to set up:**
            1. Use Gmail App Password (recommended)
            2. Enable "Less secure app access" (not recommended)
            3. Use a dedicated email service
            
            **Gmail App Password Setup:**
            1. Go to Google Account Settings
            2. Security → 2-Step Verification
            3. App passwords → Generate new
            4. Use the 16-character password here
            """)
            
            with st.form("email_config"):
                col1, col2 = st.columns(2)
                
                with col1:
                    email = st.text_input("Your Email", value=st.session_state.get('email', ''))
                    smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
                    smtp_port = st.number_input("SMTP Port", value=587, min_value=1, max_value=65535)
                
                with col2:
                    email_password = st.text_input("Email Password / App Password", type="password")
                    reminder_days = st.number_input("Send Reminder (days before)", value=1, min_value=0, max_value=7)
                
                save_config = st.form_submit_button("💾 Save Configuration")
                
                if save_config:
                    st.session_state.email_config = {
                        'email': email,
                        'password': email_password,
                        'smtp_server': smtp_server,
                        'smtp_port': smtp_port,
                        'reminder_days': reminder_days
                    }
                    st.success("✅ Email configuration saved!")
        
        # Test email button
        if 'email_config' in st.session_state:
            if st.button("📧 Send Test Email"):
                success = self._send_test_email(st.session_state.email_config)
                if success:
                    st.success("✅ Test email sent successfully!")
                else:
                    st.error("❌ Failed to send email. Please check your configuration.")
    
    def _display_interview_reminder_card(self, interview, user_id: int):
        """Display a single interview with reminder options"""
        
        days_until = (pd.to_datetime(interview['interview_date']) - pd.Timestamp.now()).days
        
        # Status indicator
        if days_until < 0:
            status_color = "🔴"
            status_text = "Passed"
        elif days_until == 0:
            status_color = "🟠"
            status_text = "Today!"
        elif days_until <= 3:
            status_color = "🟡"
            status_text = f"In {days_until} days"
        else:
            status_color = "🟢"
            status_text = f"In {days_until} days"
        
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.markdown(f"### {status_color} {interview['company_name']}")
                st.markdown(f"**Role:** {interview['role']}")
            
            with col2:
                st.markdown(f"**Date:** {interview['interview_date'].strftime('%Y-%m-%d')}")
                st.markdown(f"**Status:** {status_text}")
            
            with col3:
                prep_stars = '⭐' * interview['preparation_level']
                st.markdown(f"**Preparation:** {prep_stars}")
            
            with col4:
                reminder_sent = interview.get('reminder_sent', 0)
                if reminder_sent:
                    st.success("✅ Sent")
                else:
                    if st.button("🔔", key=f"remind_{interview['interview_id']}", help="Send Reminder"):
                        if 'email_config' in st.session_state:
                            success = self._send_reminder_email(interview, st.session_state.email_config)
                            if success:
                                st.success("Reminder sent!")
                                st.rerun()
                            else:
                                st.error("Failed to send")
                        else:
                            st.warning("Configure email first!")
            
            st.divider()
    
    def _send_reminder_email(self, interview, config: dict) -> bool:
        """Send reminder email for an interview"""
        
        try:
            # Create email content
            subject = f"Interview Reminder: {interview['company_name']} - {interview['role']}"
            
            body = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #4169E1;">🎯 Interview Reminder</h2>
                    
                    <p>Hi there!</p>
                    
                    <p>This is a friendly reminder about your upcoming interview:</p>
                    
                    <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Company:</strong> {interview['company_name']}</p>
                        <p><strong>Role:</strong> {interview['role']}</p>
                        <p><strong>Date:</strong> {interview['interview_date'].strftime('%B %d, %Y')}</p>
                        <p><strong>Your Preparation Level:</strong> {'⭐' * interview['preparation_level']}</p>
                    </div>
                    
                    <h3 style="color: #32CD32;">💡 Quick Tips:</h3>
                    <ul>
                        <li>Review the job description and company background</li>
                        <li>Prepare questions to ask the interviewer</li>
                        <li>Practice common interview questions</li>
                        <li>Get a good night's sleep before the interview</li>
                        <li>Test your tech setup (if virtual interview)</li>
                    </ul>
                    
                    <p style="margin-top: 30px;">Good luck! You've got this! 🚀</p>
                    
                    <hr style="margin-top: 30px;">
                    <p style="color: gray; font-size: 12px;">
                        Sent from Interview Tracker App<br>
                        To manage your reminders, visit the app.
                    </p>
                </body>
            </html>
            """
            
            # Send email
            success = self._send_email(
                config['email'],
                config['email'],
                subject,
                body,
                config['smtp_server'],
                config['smtp_port'],
                config['password']
            )
            
            return success
            
        except Exception as e:
            print(f"Error sending reminder: {e}")
            return False
    
    def _send_test_email(self, config: dict) -> bool:
        """Send a test email"""
        
        subject = "Test Email from Interview Tracker"
        body = """
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #4169E1;">✅ Test Email Successful!</h2>
                <p>Your email configuration is working correctly.</p>
                <p>You will now receive interview reminders at this email address.</p>
                <hr style="margin-top: 30px;">
                <p style="color: gray; font-size: 12px;">Interview Tracker App</p>
            </body>
        </html>
        """
        
        return self._send_email(
            config['email'],
            config['email'],
            subject,
            body,
            config['smtp_server'],
            config['smtp_port'],
            config['password']
        )
    
    def _send_email(self, from_email: str, to_email: str, subject: str, 
                   body: str, smtp_server: str, smtp_port: int, password: str) -> bool:
        """Core email sending function"""
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach HTML body
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            # Connect to SMTP server
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(from_email, password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Email error: {e}")
            return False