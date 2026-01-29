import streamlit as st
import os
from database.db import init_db
from modules.auth import login, register
from modules.dashboard import show_dashboard
from modules.resources import show_resources
from modules.roadmap import show_roadmap
from modules.interviews import show_interviews
from modules.analytics import show_analytics


# Setup
st.set_page_config("InterviewPrep Pro", "🚀", layout="wide")
# Load custom CSS
css_path = os.path.join("assets","style.css")
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

init_db()


# Session
if "user" not in st.session_state:
    st.session_state.user = None


# AUTH
if not st.session_state.user:

    st.title("🚀 InterviewPrep Pro")

    t1,t2 = st.tabs(["Login","Register"])

    with t1:

        e = st.text_input("Email")
        p = st.text_input("Password", type="password")

        if st.button("Login"):

            u = login(e,p)

            if u:
                st.session_state.user = u
                st.experimental_rerun()
            else:
                st.error("Invalid")

    with t2:

        n = st.text_input("Name")
        e2 = st.text_input("Email ")
        p2 = st.text_input("Password ")

        if st.button("Register"):

            if register(n,e2,p2):
                st.success("Registered")
            else:
                st.error("Exists")

    st.stop()


# SIDEBAR
st.sidebar.success(st.session_state.user["name"])

page = st.sidebar.radio("Menu",[
    "Dashboard",
    "Resources",
    "Roadmap",
    "Interviews",
    "Analytics",
    "Logout"
])


# ROUTING
if page=="Dashboard":
    show_dashboard(st.session_state.user)

elif page=="Resources":
    show_resources(st.session_state.user)

elif page=="Roadmap":
    show_roadmap(st.session_state.user)

elif page=="Interviews":
    show_interviews(st.session_state.user)

elif page=="Analytics":
    show_analytics(st.session_state.user)

elif page=="Logout":
    st.session_state.user=None
    st.experimental_rerun()
