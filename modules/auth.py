"""
Authentication Module
Handles user login, signup, and session management
"""

import bcrypt
import streamlit as st
from database.db_manager import DatabaseManager

class AuthManager:
    """Manages user authentication"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storing"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against a hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def signup(self, username: str, email: str, password: str) -> tuple[bool, str]:
        """
        Register a new user
        Returns: (success: bool, message: str)
        """
        # Validate inputs
        if not username or not email or not password:
            return False, "All fields are required"
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        if '@' not in email:
            return False, "Invalid email format"
        
        # Hash password
        password_hash = self.hash_password(password)
        
        # Create user
        success = self.db.create_user(username, email, password_hash)
        
        if success:
            return True, "Account created successfully! Please login."
        else:
            return False, "Username or email already exists"
    
    def login(self, username: str, password: str) -> tuple[bool, str, dict]:
        """
        Authenticate a user
        Returns: (success: bool, message: str, user_data: dict)
        """
        if not username or not password:
            return False, "Username and password are required", {}
        
        # Get user from database
        user = self.db.get_user_by_username(username)
        
        if not user:
            return False, "Invalid username or password", {}
        
        # Verify password
        if self.verify_password(password, user['password_hash']):
            # Update last login
            self.db.update_last_login(user['user_id'])
            return True, "Login successful!", user
        else:
            return False, "Invalid username or password", {}
    
    @staticmethod
    def logout():
        """Logout the current user"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
    
    @staticmethod
    def is_logged_in() -> bool:
        """Check if a user is logged in"""
        return 'user_id' in st.session_state and st.session_state.user_id is not None
    
    @staticmethod
    def get_current_user_id() -> int:
        """Get the current logged-in user ID"""
        return st.session_state.get('user_id', None)
    
    @staticmethod
    def get_current_username() -> str:
        """Get the current logged-in username"""
        return st.session_state.get('username', 'Guest')


def show_auth_page(auth_manager: AuthManager):
    """Display the authentication page (login/signup)"""
    
    st.title("🎯 Interview Tracker")
    st.subheader("Track Your Career Journey")
    
    # Create tabs for login and signup
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    # Login Tab
    with tab1:
        st.subheader("Login to Your Account")
        
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                success, message, user_data = auth_manager.login(username, password)
                
                if success:
                    # Set session state
                    st.session_state.user_id = user_data['user_id']
                    st.session_state.username = user_data['username']
                    st.session_state.email = user_data['email']
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    # Signup Tab
    with tab2:
        st.subheader("Create New Account")
        
        with st.form("signup_form"):
            new_username = st.text_input("Username", key="signup_username")
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            submit = st.form_submit_button("Sign Up", use_container_width=True)
            
            if submit:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success, message = auth_manager.signup(new_username, new_email, new_password)
                    
                    if success:
                        st.success(message)
                        st.info("Please switch to the Login tab to access your account")
                    else:
                        st.error(message)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>Built with ❤️ using Python & Streamlit</p>
        <p>© 2024 Interview Tracker | Secure & Private</p>
    </div>
    """, unsafe_allow_html=True)