import streamlit as st
import os
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------- Load Student Data ----------
STUDENT_DATA_PATH = "data/student_data.json"
def load_data():
    if not os.path.exists(STUDENT_DATA_PATH):
        return {}
    with open(STUDENT_DATA_PATH, "r") as f:
        return json.load(f)

def save_data(data):
    with open(STUDENT_DATA_PATH, "w") as f:
        json.dump(data, f, indent=4)

student_data = load_data()

# ---------- Authentication ----------
def login():
    st.title("🔐 PhD Progress Tracker Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")

    if login_btn:
        if username == "amit" and password == "admin123":
            st.session_state.user = "supervisor"
            st.session_state.username = "Dr.Amit Dharnaik"
            st.success("Logged in as Supervisor")
            st.experimental_rerun()
        elif username in student_data and student_data[username].get("password") == password:
            st.session_state.user = "student"
            st.session_state.username = username
            st.success(f"Logged in as {username}")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

if "user" not in st.session_state:
    login()
    st.stop()

# ---------- Logout Button ----------
st.sidebar.title("⚙️ Settings")
if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.experimental_rerun()

# ---------- Supervisor Dashboard ----------
def supervisor_dashboard():
    st.title("🧑‍🏫 Supervisor Dashboard")

    # Manage student accounts
    st.subheader("👥 Manage Student Accounts")
    action = st.radio("Action", ["Create", "Reset Password", "Delete"])
    student_id = st.text_input("Student Username")
    new_password = st.text_input("New Password", type="password")

    if st.button("Apply Action"):
        if action == "Create":
            if student_id in student_data:
                st.warning("Student already exists.")
            else:
                student_data[student_id] = {"password": new_password, "rpr": {}, "aps": {}}
                save_data(student_data)
                st.success("Student created.")

        elif action == "Reset Password":
            if student_id in student_data:
                student_data[student_id]["password"] = new_password
                save_data(student_data)
                st.success("Password reset.")
            else:
                st.warning("Student does not exist.")

        elif action == "Delete":
            if student_id in student_data:
                del student_data[student_id]
                save_data(student_data)
                st.success("Student deleted.")
            else:
                st.warning("Student does not exist.")

    # View and export student progress
    st.subheader("📋 View Student Progress")
    selected_student = st.selectbox("Select Student", list(student_data.keys()))
    show_student_progress(selected_student)

    if st.button("📤 Export to Excel"):
        rpr = student_data[selected_student].get("rpr", {})
        aps = student_data[selected_student].get("aps", {})
        df_rpr = pd.DataFrame.from_dict(rpr, orient="index")
        df_aps = pd.DataFrame.from_dict(aps, orient="index")
        with pd.ExcelWriter(f"{selected_student}_progress.xlsx") as writer:
            df_rpr.to_excel(writer, sheet_name="RPR")
            df_aps.to_excel(writer, sheet_name="APS")
        st.success("Exported successfully! File saved to app directory.")

# ---------- Student Dashboard ----------
def student_dashboard():
    selected_student = st.session_state.username
    st.title(f"📘 Welcome, {selected_student}")
    show_student_progress(selected_student, editable=True)

# ---------- Shared Progress View ----------
def show_student_progress(selected_student, editable=False):
    # --- File Upload ---
    st.subheader("📁 Upload Documents")
    student_folder = os.path.join("data/uploads", selected_student)
    os.makedirs(student_folder, exist_ok=True)

    uploaded_file = st.file_uploader("Upload files (PDF)", type=["pdf"])
    if uploaded_file:
        save_path = os.path.join(student_folder, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"File uploaded successfully to {student_folder}.")

    # --- Show Uploaded Files ---
    if os.path.exists(student_folder):
        st.subheader("📂 Uploaded Files")
        uploaded_files = os.listdir(student_folder)
        if uploaded_files:
            for file in uploaded_files:
                st.markdown(f"- [{file}](./data/uploads/{selected_student}/{file})")
        else:
            st.info("No files uploaded yet.")

    # --- Charts: RPR & APS Completion ---
    st.subheader("📊 Progress Charts")

    if selected_student not in student_data:
        st.warning(f"No progress data found for {selected_student}. Please contact the supervisor.")
        return

    rpr_status = student_data[selected_student].get("rpr", {})
    aps_status = student_data[selected_student].get("aps", {})

    # Editable forms for student
    if editable:
        st.subheader("✏️ Update RPR Status")
        for r in range(1, 4):
            key = f"RPR{r}"
            completed = st.checkbox(f"{key} Completed", value=rpr_status.get(key, {}).get("completed", False))
            student_data[selected_student].setdefault("rpr", {})[key] = {"completed": completed}

        st.subheader("✏️ Update APS Status")
        for a in range(1, 4):
            key = f"APS{a}"
            completed = st.checkbox(f"{key} Completed", value=aps_status.get(key, {}).get("completed", False))
            student_data[selected_student].setdefault("aps", {})[key] = {"completed": completed}

        if st.button("💾 Save Progress"):
            save_data(student_data)
            st.success("Progress updated.")

    # Charts
    rpr_done = sum(1 for r in rpr_status if rpr_status[r].get("completed"))
    rpr_total = len(rpr_status)
    aps_done = sum(1 for a in aps_status if aps_status[a].get("completed"))
    aps_total = len(aps_status)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**RPR Completion**")
        fig1, ax1 = plt.subplots()
        ax1.pie([rpr_done, rpr_total - rpr_done], labels=["Completed", "Pending"], autopct='%1.1f%%', startangle=90, colors=["#4CAF50", "#FFC107"])
        ax1.axis('equal')
        st.pyplot(fig1)

    with col2:
        st.markdown("**APS Completion**")
        fig2, ax2 = plt.subplots()
        ax2.pie([aps_done, aps_total - aps_done], labels=["Completed", "Pending"], autopct='%1.1f%%', startangle=90, colors=["#2196F3", "#FF5722"])
        ax2.axis('equal')
        st.pyplot(fig2)

# ---------- Route to Appropriate Dashboard ----------
if st.session_state.user == "supervisor":
    supervisor_dashboard()
elif st.session_state.user == "student":
    student_dashboard()
