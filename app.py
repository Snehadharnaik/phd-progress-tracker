from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
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

# ---------------- Google Drive Backup (Service Account) ----------------
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_drive_service():
    sa_json = os.getenv("GDRIVE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        return None
    try:
        info = json.loads(sa_json)
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception:
        return None

def find_file_in_folder(service, filename: str, folder_id: str):
    q = f"'{folder_id}' in parents and name='{filename}' and trashed=false"
    res = service.files().list(q=q, fields="files(id,name)").execute()
    files = res.get("files", [])
    return files[0]["id"] if files else None

def upload_or_update_file(service, local_path: str, drive_filename: str, folder_id: str):
    media = MediaFileUpload(local_path, resumable=True)
    existing_id = find_file_in_folder(service, drive_filename, folder_id)

    if existing_id:
        service.files().update(fileId=existing_id, media_body=media).execute()
        return existing_id
    else:
        meta = {"name": drive_filename, "parents": [folder_id]}
        created = service.files().create(body=meta, media_body=media, fields="id").execute()
        return created["id"]

def backup_json_to_drive(local_json_path: str, drive_filename: str = "student_data.json"):
    folder_id = os.getenv("GDRIVE_FOLDER_ID")
    service = get_drive_service()
    if not folder_id or service is None:
        return False
    if not os.path.exists(local_json_path):
        return False
    try:
        upload_or_update_file(service, local_json_path, drive_filename, folder_id)
        return True
    except Exception:
        return False

def backup_pdf_to_drive(local_pdf_path: str, student_name: str):
    """
    Upload PDFs into a subfolder inside your main backup folder.
    """
    folder_id = os.getenv("GDRIVE_FOLDER_ID")
    service = get_drive_service()
    if not folder_id or service is None:
        return False

    try:
        # Find or create student folder inside main folder
        q = (
            f"'{folder_id}' in parents and "
            f"name='{student_name}' and "
            "mimeType='application/vnd.google-apps.folder' and trashed=false"
        )
        res = service.files().list(q=q, fields="files(id,name)").execute()
        files = res.get("files", [])

        if files:
            student_folder_id = files[0]["id"]
        else:
            meta = {
                "name": student_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [folder_id],
            }
            created = service.files().create(body=meta, fields="id").execute()
            student_folder_id = created["id"]

        pdf_name = os.path.basename(local_pdf_path)
        upload_or_update_file(service, local_pdf_path, pdf_name, student_folder_id)
        return True
    except Exception:
        return False

# ---------- Safe logout cleanup ----------
if st.session_state.get("logout"):
    st.session_state.clear()
    st.rerun()

# ---------- Authentication ----------
def login():
    st.title("🔐 PhD Progress Tracker Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")

    if login_btn and username and password:
        if username == "amit" and password == "admin123":
            st.session_state.user = "supervisor"
            st.session_state.username = "Dr.Amit Dharnaik"
        elif username in student_data and student_data[username].get("password") == password:
            st.session_state.user = "student"
            st.session_state.username = username
            if student_data[username].get("force_change", False):
                st.session_state.force_change = True
        else:
            st.error("Invalid credentials")

if "user" not in st.session_state:
    login()
    st.stop()

# ---------- Password Change Enforcement ----------
if st.session_state.get("user") == "student" and st.session_state.get("force_change"):
    st.warning("⚠️ Please change your password before proceeding.")
    new_pw = st.text_input("New Password", type="password")
    confirm_pw = st.text_input("Confirm New Password", type="password")
    if st.button("Update Password"):
        uname = st.session_state.username
        if new_pw != confirm_pw:
            st.error("Passwords do not match.")
        elif len(new_pw) < 6:
            st.error("Password must be at least 6 characters long.")
        else:
            student_data[uname]["password"] = new_pw
            student_data[uname]["force_change"] = False
            save_data(student_data)
            st.success("Password updated successfully. Reloading dashboard...")
            st.session_state.force_change = False
            st.rerun()
    st.stop()

# ---------- Logout Button and Settings ----------
st.sidebar.title("⚙️ Settings")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logout = True
    st.rerun()

# Student password change
if st.session_state.user == "student":
    with st.sidebar.expander("🔐 Change Password"):
        current_pw = st.text_input("Current Password", type="password")
        new_pw = st.text_input("New Password", type="password")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        if st.button("Update Password"):
            uname = st.session_state.username
            if student_data[uname].get("password") != current_pw:
                st.error("Current password is incorrect.")
            elif new_pw != confirm_pw:
                st.error("New passwords do not match.")
            else:
                student_data[uname]["password"] = new_pw
                save_data(student_data)
                st.success("Password updated successfully.")

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
                student_data[student_id] = {"password": new_password, "rpr": {}, "aps": {}, "force_change": True}
                save_data(student_data)
                st.success("Student created and must change password on first login.")

        elif action == "Reset Password":
            if student_id in student_data:
                student_data[student_id]["password"] = new_password
                student_data[student_id]["force_change"] = True
                save_data(student_data)
                st.success("Password reset. Student must change password on next login.")
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
