import streamlit as st
import chardet
import os
import json
import shutil
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from zipfile import ZipFile
from datetime import datetime

# Setup folders
OUTPUT_DIR = "corrected_json"
REPORT_FILE = "report.xlsx"
ZIP_NAME = "utf8_results.zip"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# UI Configuration
st.set_page_config(page_title="UTF-8 JSON Fixer", layout="wide", page_icon="🤖")
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: white; font-family: 'Courier New'; }
    .stButton>button { background-color: #4CAF50; color: white; }
    .stTextInput>div>input { background-color: #161b22; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 UTF-8 JSON Encoding Fixer by Dhritii.AI")
st.markdown("Upload your `.json` files. The app will detect non-UTF-8 encoded files, fix them, and give you a downloadable report and ZIP of all files.")

# Upload files
uploaded_files = st.file_uploader("Upload JSON Files", type=["json"], accept_multiple_files=True)

# Clear output
if st.button("🔄 Clear All"):
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    st.experimental_rerun()

# Process
valid_count = 0
fixed_count = 0
error_count = 0
report_rows = []

if uploaded_files:
    with st.spinner("🔍 Checking and fixing encoding..."):
        progress = st.progress(0)
        for i, file in enumerate(uploaded_files):
            filename = file.name
            try:
                raw_data = file.read()
                detected = chardet.detect(raw_data)
                encoding = detected['encoding']
                confidence = detected['confidence']

                if encoding.lower() != 'utf-8':
                    try:
                        text = raw_data.decode(encoding)
                        utf8_data = text.encode('utf-8')
                        with open(os.path.join(OUTPUT_DIR, filename), 'wb') as out:
                            out.write(utf8_data)
                        fixed_count += 1
                        report_rows.append([filename, encoding, confidence, "Fixed"])
                    except Exception as e:
                        error_count += 1
                        report_rows.append([filename, encoding, confidence, f"Error: {e}"])
                else:
                    with open(os.path.join(OUTPUT_DIR, filename), 'wb') as out:
                        out.write(raw_data)
                    valid_count += 1
                    report_rows.append([filename, encoding, confidence, "Valid"])
            except Exception as e:
                error_count += 1
                report_rows.append([filename, "N/A", 0, f"Error: {e}"])
            progress.progress((i + 1) / len(uploaded_files))

    # Stats Boxes
    col1, col2, col3 = st.columns(3)
    col1.metric("📁 Total Uploaded", len(uploaded_files))
    col2.metric("✅ Valid", valid_count)
    col3.metric("🛠️ Fixed", fixed_count)

    # Pie Chart
    fig, ax = plt.subplots()
    ax.pie([valid_count, fixed_count, error_count], labels=["Valid", "Fixed", "Error"], autopct='%1.1f%%', startangle=140)
    ax.axis('equal')
    st.pyplot(fig)

    # Report Download
    df_report = pd.DataFrame(report_rows, columns=["Filename", "Detected Encoding", "Confidence", "Status"])
    report_path = os.path.join(OUTPUT_DIR, REPORT_FILE)
    df_report.to_excel(report_path, index=False)

    with open(report_path, "rb") as xls_file:
        st.download_button(
            label="📄 Download Report (.xlsx)",
            data=xls_file,
            file_name=REPORT_FILE,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # Zip Output
    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, "w") as zipf:
        for foldername, _, filenames in os.walk(OUTPUT_DIR):
            for f in filenames:
                full_path = os.path.join(foldername, f)
                arcname = os.path.relpath(full_path, OUTPUT_DIR)
                zipf.write(full_path, arcname)

    st.download_button(
        label="📦 Download All (ZIP)",
        data=zip_buffer.getvalue(),
        file_name=ZIP_NAME,
        mime="application/zip"
    )

