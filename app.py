import streamlit as st
import os
import json
import matplotlib.pyplot as plt
import numpy as np

# Load student data
with open("data/student_data.json", "r") as f:
    student_data = json.load(f)

# Example session username (Replace this with your actual session login logic)
selected_student = st.session_state.get("username", "student1")

# --- File Upload ---
st.subheader("📁 Upload Documents")
uploaded_file = st.file_uploader("Upload files (PDF)", type=["pdf"])
if uploaded_file:
    student_folder = os.path.join("data/uploads", selected_student)
    os.makedirs(student_folder, exist_ok=True)
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

# RPR Chart
rpr_status = student_data[selected_student].get("rpr", {})
rpr_done = sum(1 for r in rpr_status if rpr_status[r]["completed"])
rpr_total = len(rpr_status)

# APS Chart
aps_status = student_data[selected_student].get("aps", {})
aps_done = sum(1 for a in aps_status if aps_status[a]["completed"])
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
