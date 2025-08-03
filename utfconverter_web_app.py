import streamlit as st
import os
import shutil
import json
import chardet
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="UTF-8 JSON Validator", layout="centered")
st.title("🤖 UTF-8 JSON Encoding Validator")

st.markdown("""
<style>
.css-1aumxhk, .css-ffhzg2 { background-color: #0f172a !important; color: #e2e8f0 !important; }
.stButton > button { background-color: #14b8a6; color: white; font-weight: bold; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

input_folder = st.text_input("📂 Enter path to JSON folder:", "")

report_data = []
corrected_folder = "corrected_json"
os.makedirs(corrected_folder, exist_ok=True)

def detect_encoding(filepath):
    with open(filepath, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def fix_encoding(filepath, output_path):
    encoding = detect_encoding(filepath)
    with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
        content = f.read()
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

def copy_file(filepath, output_path):
    shutil.copy2(filepath, output_path)

def generate_pie_chart(valid, fixed, failed):
    valid = int(valid or 0)
    fixed = int(fixed or 0)
    failed = int(failed or 0)
    total = valid + fixed + failed
    if total == 0:
        st.warning("⚠️ No files to display in pie chart.")
        return
    fig, ax = plt.subplots()
    ax.pie([valid, fixed, failed], labels=["Valid", "Fixed", "Error"], autopct='%1.1f%%', startangle=140)
    ax.axis("equal")
    st.pyplot(fig)

def process_files(folder):
    valid = 0
    fixed = 0
    failed = 0
    report_data.clear()
    for file in os.listdir(folder):
        if file.endswith(".json"):
            full_path = os.path.join(folder, file)
            output_path = os.path.join(corrected_folder, file)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                copy_file(full_path, output_path)
                status = "Valid"
                valid += 1
            except UnicodeDecodeError:
                try:
                    fix_encoding(full_path, output_path)
                    status = "Fixed"
                    fixed += 1
                except Exception:
                    status = "Error"
                    failed += 1
            except Exception:
                status = "Error"
                failed += 1

            report_data.append({"Filename": file, "Status": status})
    return valid, fixed, failed

if st.button("🚀 Run Conversion"):
    if input_folder.strip() == "":
        st.error("❌ Please enter a valid folder path.")
    elif not os.path.isdir(input_folder):
        st.error("❌ The folder path doesn't exist.")
    else:
        with st.spinner("Processing files..."):
            v, f, e = process_files(input_folder)
        st.success(f"✅ Done! Valid: {v}, Fixed: {f}, Errors: {e}")
        generate_pie_chart(v, f, e)
        st.balloons()
        st.subheader("📊 Summary Report")
        df = pd.DataFrame(report_data)
        st.dataframe(df, use_container_width=True)

        report_excel = os.path.join(corrected_folder, "utf8_report.xlsx")
        df.to_excel(report_excel, index=False)

        with open(report_excel, "rb") as file:
            st.download_button(label="📥 Download Report (.xlsx)", data=file, file_name="utf8_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
