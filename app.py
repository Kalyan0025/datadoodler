import streamlit as st
import base64

from gemini_client import GeminiClient
from data_parser import parse_input
from visual_spec_generator import generate_visual_spec
from renderer import render_svg_from_spec


# -----------------------------
# Streamlit Page Config
# -----------------------------
st.set_page_config(
    page_title="Visual Journal Bot",
    page_icon="✨",
    layout="wide"
)

st.title("✨ Visual Journal Bot — Data Humanism / Giorgia Lupi Style")


# -----------------------------
# Gemini Client
# -----------------------------
gemini = GeminiClient(api_key=st.secrets["GEMINI_API_KEY"])


# -----------------------------
# User Input Area
# -----------------------------
st.subheader("Upload or Enter Your Data")

data_source = st.radio(
    "Choose input type:",
    ["Text", "Upload File (PDF, CSV, DOCX, XLSX)"]
)

raw_text = ""
uploaded_file = None

if data_source == "Text":
    raw_text = st.text_area("Enter your memory / dream / routine / logs:")
else:
    uploaded_file = st.file_uploader(
        "Upload a file",
        type=["pdf", "txt", "csv", "xlsx", "docx"]
    )

data_type = st.selectbox(
    "What type of data is this?",
    [
        "Dream",
        "Memory",
        "Daily Routine",
        "Weekly Routine",
        "Office / Attendance Data",
        "Activity Log",
        "Creative / Story",
        "Mixed / Let AI Detect"
    ]
)


# -----------------------------
# Generate Button
# -----------------------------
if st.button("Generate Visualization ✨"):
    if raw_text.strip() == "" and uploaded_file is None:
        st.error("Please enter text or upload a file.")
        st.stop()

    st.info("Processing your data... This may take a few seconds.")

    # -----------------------------
    # Parse input into inputData JSON
    # -----------------------------
    input_data = parse_input(
        raw_text=raw_text,
        uploaded_file=uploaded_file,
        data_type=data_type,
        gemini=gemini
    )

    st.success("Data parsed successfully.")

    # -----------------------------
    # Generate Visual Spec via Gemini
    # -----------------------------
    st.info("Generating Data Humanism visual specification (JSON)...")

    visual_spec = generate_visual_spec(
        input_data=input_data,
        gemini=gemini
    )

    st.success("Visual spec created.")

    # -----------------------------
    # Render SVG
    # -----------------------------
    st.info("Rendering SVG visualization...")

    svg_output = render_svg_from_spec(visual_spec)

    st.success("Visualization complete.")

    # -----------------------------
    # Show SVG
    # -----------------------------
    st.subheader("Your Data Humanism Visualization")

    st.markdown(
        f"<div style='border:1px solid #ddd; padding:10px'>{svg_output}</div>",
        unsafe_allow_html=True
    )

    # -----------------------------
    # Download Button
    # -----------------------------
    svg_bytes = svg_output.encode("utf-8")
    b64 = base64.b64encode(svg_bytes).decode()

    st.download_button(
        "Download SVG",
        data=svg_bytes,
        file_name="visual_journal.svg",
        mime="image/svg+xml"
    )
