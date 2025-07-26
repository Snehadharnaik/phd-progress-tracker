import streamlit as st
import json
import os
from datetime import datetime, date

# --- File and Data Setup ---
data_file = "data/student_data.json"
if not os.path.exists(data_file):
    st.error("student_data.json not found! Please upload or create the file.")
    st.stop()

with open(data_file, "r") as f:
    student_data = json.load(f)

students = list(student_data.keys())
selected_student = st.selectbox("Select Student", students)

st.title(f"PhD Progress Tracker – {selected_student}")

# --- Rename Student ---
st.markdown("### ✏️ Rename Student")
with st.form("rename_form"):
    new_name = st.text_input("Enter new name for the selected student", value=selected_student)
    submit_rename = st.form_submit_button("Rename Student")

if submit_rename:
    if new_name and new_name != selected_student:
        student_data[new_name] = student_data.pop(selected_student)
        with open(data_file, "w") as f:
            json.dump(student_data, f, indent=2)
        st.success(f"✅ Student renamed to {new_name}. Please reload the app.")
        st.stop()
    elif new_name == selected_student:
        st.info("ℹ️ New name is the same as current.")
    else:
        st.warning("⚠️ Please enter a valid new name.")

# --- Milestones ---
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

# --- File Upload ---
st.subheader("📁 Upload Documents")
uploaded_file = st.file_uploader("Upload files (PDF)", type=["pdf"])
if uploaded_file:
    save_path = os.path.join("data/uploads", f"{selected_student}_{uploaded_file.name}")
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success("File uploaded successfully.")

# --- Supervisor Remarks ---
st.subheader("💬 Supervisor Remarks")
remarks = st.text_area("Remarks", student_data[selected_student].get("remarks", ""))

# --- RPR Tracking (6 Monthly) ---
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

# --- APS Tracking (Yearly) ---
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

# --- Save Button ---
if st.button("💾 Save All Progress"):
    student_data[selected_student]["milestones"] = updated_milestones
    student_data[selected_student]["remarks"] = remarks
    student_data[selected_student]["rpr"] = rpr_data
    student_data[selected_student]["aps"] = aps_data
    with open(data_file, "w") as f:
        json.dump(student_data, f, indent=2)
    st.success("Progress saved successfully.")
