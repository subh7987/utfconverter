import streamlit as st
import os
import json
import chardet
import shutil
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime

# ========== CONFIG ==========
st.set_page_config(page_title="UTF-8 Encoding Fixer", layout="wide")
LOGO_PATH = "logo.ico"  # Replace with your own icon path if hosted

# ========== SESSION STATE SETUP ==========
if "log" not in st.session_state:
    st.session_state.log = []
if "report_df" not in st.session_state:
    st.session_state.report_df = pd.DataFrame()

# ========== UTILS ==========
def log(msg):
    st.session_state.log.append(msg)
    st.write(msg)

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    result = chardet.detect(raw_data)
    return result['encoding']

def is_valid_utf8(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read()
        return True
    except:
        return False

def fix_encoding(file_path, output_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    detected = chardet.detect(raw_data)
    try:
        text = raw_data.decode(detected['encoding'])
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return True
    except:
        return False

def generate_excel_report(data):
    output = BytesIO()
    df = pd.DataFrame(data)
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    return output

def generate_pie_chart(valid, fixed, failed):
    fig, ax = plt.subplots()
    ax.pie([valid, fixed, failed], labels=["Valid", "Fixed", "Error"], autopct='%1.1f%%', startangle=140)
    ax.axis('equal')
    st.pyplot(fig)

# ========== MAIN PROCESS ==========
def process_folder(folder):
    corrected_dir = os.path.join(folder, "corrected_json")
    os.makedirs(corrected_dir, exist_ok=True)

    report = []
    valid_count = 0
    fixed_count = 0
    failed_count = 0

    for file in os.listdir(folder):
        if file.endswith(".json"):
            file_path = os.path.join(folder, file)
            out_path = os.path.join(corrected_dir, file)
            encoding = detect_encoding(file_path)

            if encoding.lower() == 'utf-8' and is_valid_utf8(file_path):
                shutil.copy(file_path, out_path)
                report.append({"Filename": file, "Encoding": encoding, "Status": "Valid"})
                valid_count += 1
                log(f"✅ {file} is already UTF-8 valid.")
            else:
                if fix_encoding(file_path, out_path):
                    report.append({"Filename": file, "Encoding": encoding, "Status": "Fixed"})
                    fixed_count += 1
                    log(f"🔧 {file} re-encoded to UTF-8.")
                else:
                    report.append({"Filename": file, "Encoding": encoding, "Status": "Error"})
                    failed_count += 1
                    log(f"❌ {file} failed to re-encode.")

    st.session_state.report_df = pd.DataFrame(report)
    return valid_count, fixed_count, failed_count

# ========== GUI ==========
st.title("🤖 UTF-8 Encoding Fixer - Web App")
st.markdown("""
This app checks and fixes encoding of `.json` files to UTF-8. It generates a report and saves all checked files (fixed + valid) into a `corrected_json` folder.
""")

uploaded_folder = st.text_input("📂 Enter path to folder containing JSON files:")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🚀 Run Conversion"):
        if not uploaded_folder:
            st.warning("Please provide a folder path.")
        else:
            with st.spinner("Processing files..."):
                v, f, e = process_folder(uploaded_folder)
                st.success("Done!")
                st.metric("📁 Total JSON Files", v + f + e)
                st.metric("🛠️ Fixed Files", f)
                st.metric("❌ Failed Files", e)
                generate_pie_chart(v, f, e)
with col2:
    if st.button("📤 Download Report"):
        if not st.session_state.report_df.empty:
            xls_data = generate_excel_report(st.session_state.report_df)
            st.download_button(
                label="Download Excel Report",
                data=xls_data,
                file_name=f"utf8_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No report to download yet.")
with col3:
    if st.button("🧹 Clear Log"):
        st.session_state.log.clear()
        st.session_state.report_df = pd.DataFrame()
        st.experimental_rerun()

st.subheader("📜 Log Output")
for msg in st.session_state.log:
    st.text(msg)
