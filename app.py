
import streamlit as st
import json
import os
from datetime import datetime, date

# Load data
data_file = "data/student_data.json"
with open(data_file, "r") as f:
    student_data = json.load(f)

students = list(student_data.keys())
selected_student = st.selectbox("Select Student", students)

st.title(f"PhD Progress Tracker – {selected_student}")

# Milestone checklist
st.header("📋 Milestones")
milestones = list(student_data[selected_student]["milestones"].keys())
updated_milestones = {}
progress_count = 0

for m in milestones:
    status = st.checkbox(m, value=student_data[selected_student]["milestones"].get(m, False))
    updated_milestones[m] = status
    if status:
        progress_count += 1

st.progress(progress_count / len(milestones))

# File upload
st.subheader("📁 Upload Documents")
uploaded_file = st.file_uploader("Upload files (PDF)", type=["pdf"])
if uploaded_file:
    save_path = os.path.join("data/uploads", f"{selected_student}_{uploaded_file.name}")
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success("File uploaded successfully.")

# Supervisor remarks
st.subheader("💬 Supervisor Remarks")
remarks = st.text_area("Remarks", student_data[selected_student].get("remarks", ""))

# RPR tracking
st.subheader("📄 RPR Progress (Every 6 Months)")
rpr_data = {}
for i in range(1, 7):
    key = f"rpr{i}"
    entry = student_data[selected_student].get("rpr", {}).get(key, {})
    due_date = st.date_input(f"{key.upper()} Due Date", value=datetime.strptime(entry["date"], "%Y-%m-%d"), key=f"{key}_date")
    completed = st.checkbox(f"{key.upper()} Completed", value=entry["completed"], key=f"{key}_done")
    rpr_data[key] = {"date": due_date.isoformat(), "completed": completed}
    if not completed:
        days_left = (due_date - date.today()).days
        st.info(f"{key.upper()} due in {days_left} days")

# APS tracking
st.subheader("🎤 APS Progress (Every Year)")
aps_data = {}
for i in range(1, 4):
    key = f"aps{i}"
    entry = student_data[selected_student].get("aps", {}).get(key, {})
    due_date = st.date_input(f"{key.upper()} Due Date", value=datetime.strptime(entry["date"], "%Y-%m-%d"), key=f"{key}_date")
    completed = st.checkbox(f"{key.upper()} Completed", value=entry["completed"], key=f"{key}_done")
    aps_data[key] = {"date": due_date.isoformat(), "completed": completed}
    if not completed:
        days_left = (due_date - date.today()).days
        st.warning(f"{key.upper()} due in {days_left} days")

# Save data
if st.button("💾 Save All Progress"):
    student_data[selected_student]["milestones"] = updated_milestones
    student_data[selected_student]["remarks"] = remarks
    student_data[selected_student]["rpr"] = rpr_data
    student_data[selected_student]["aps"] = aps_data
    with open(data_file, "w") as f:
        json.dump(student_data, f, indent=2)
    st.success("Progress saved successfully.")
