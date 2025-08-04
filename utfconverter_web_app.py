import streamlit as st
import chardet
import pandas as pd
import os
import shutil
import io
import zipfile
from datetime import datetime
from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import RendererAgg
import threading

lock = threading.Lock()

st.set_page_config(page_title="UTF-8 JSON Encoding Fixer by Dhirthi.AI", layout="wide")
st.title("🧠 UTF-8 JSON Encoding Fixer by Dhirthi.AI")

st.markdown("""
Upload your `.json` or `.txt` files. The app will detect non-UTF-8 encoded files, fix them, and give you:
- 📊 A downloadable summary report (.xlsx)
- 📦 A ZIP of all fixed/skipped/error files
""")

uploaded_files = st.file_uploader("Upload JSON/TXT Files", type=["json", "txt"], accept_multiple_files=True)

output_dir = "output"
fixed_dir = os.path.join(output_dir, "fixed")
skipped_dir = os.path.join(output_dir, "skipped")
error_dir = os.path.join(output_dir, "error")
report_path = os.path.join(output_dir, "report.xlsx")
zip_path = os.path.join(output_dir, "utf8_fixed_output.zip")

os.makedirs(fixed_dir, exist_ok=True)
os.makedirs(skipped_dir, exist_ok=True)
os.makedirs(error_dir, exist_ok=True)

result_data = []
log_placeholder = st.empty()
log_output = ""

def detect_encoding(raw_data):
    result = chardet.detect(raw_data)
    return result['encoding']

def process_files():
    global log_output
    fixed_count = skipped_count = error_count = 0

    for file in uploaded_files:
        raw = file.read()
        file_name = file.name
        extension = os.path.splitext(file_name)[-1]
        encoding = detect_encoding(raw)
        try:
            if encoding.lower() != 'utf-8':
                decoded = raw.decode(encoding)
                with open(os.path.join(fixed_dir, file_name), "w", encoding='utf-8') as f:
                    f.write(decoded)
                fixed_count += 1
                result_data.append([file_name, encoding, "Fixed"])
                log_output += f"✔️ Fixed: {file_name} (Detected: {encoding})\n"
            else:
                with open(os.path.join(skipped_dir, file_name), "wb") as f:
                    f.write(raw)
                skipped_count += 1
                result_data.append([file_name, encoding, "Already UTF-8"])
                log_output += f"✅ Already UTF-8: {file_name}\n"
        except Exception as e:
            with open(os.path.join(error_dir, file_name), "wb") as f:
                f.write(raw)
            error_count += 1
            result_data.append([file_name, encoding or "Unknown", f"Error: {str(e)}"])
            log_output += f"❌ Error: {file_name} — {str(e)}\n"

        log_placeholder.code(log_output)

    return fixed_count, skipped_count, error_count

def generate_report():
    df = pd.DataFrame(result_data, columns=["File Name", "Detected Encoding", "Status"])
    df.to_excel(report_path, index=False)

def generate_zip():
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for folder in [fixed_dir, skipped_dir, error_dir]:
            for root, _, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, arcname=os.path.relpath(file_path, output_dir))

def generate_pie_chart(valid, fixed, errors):
    with lock:
        fig, ax = plt.subplots()
        ax.pie([valid, fixed, errors], labels=["Already UTF-8", "Fixed", "Error"], autopct='%1.1f%%', startangle=140)
        st.pyplot(fig)

if st.button("🚀 Run Encoding Fixer"):
    if not uploaded_files:
        st.warning("Please upload at least one file.")
    else:
        shutil.rmtree(output_dir, ignore_errors=True)
        os.makedirs(fixed_dir)
        os.makedirs(skipped_dir)
        os.makedirs(error_dir)

        valid, fixed, errors = process_files()
        generate_report()
        generate_zip()

        st.success("✅ Encoding fix completed!")
        st.markdown(f"**Total Files:** {len(uploaded_files)}")
        st.markdown(f"**Already UTF-8:** {valid}")
        st.markdown(f"**Fixed:** {fixed}")
        st.markdown(f"**Errors:** {errors}")

        generate_pie_chart(valid, fixed, errors)

        with open(report_path, "rb") as f:
            st.download_button("📥 Download Report (.xlsx)", f, file_name="utf8_encoding_report.xlsx")

        with open(zip_path, "rb") as z:
            st.download_button("📦 Download All Output (ZIP)", z, file_name="utf8_fixed_output.zip")
