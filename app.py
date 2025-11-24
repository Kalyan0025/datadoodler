# app.py

import json
import textwrap

import streamlit as st

from gemini_client import GeminiClient
from data_parser import parse_input_data
from visual_spec_generator import generate_visual_spec
from renderer import render_visual_spec


# -------------------------------
# Streamlit page configuration
# -------------------------------
st.set_page_config(
    page_title="Visual Journal Bot – Data Humanism",
    layout="wide",
    initial_sidebar_state="expanded",
    initial_sidebar_state="collapsed",
)


@@ -31,7 +31,7 @@
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing. "
            "Go to Streamlit Cloud → App settings → Secrets and add:\n"
            "In Streamlit Cloud, go to • Manage app → Secrets • and add:\n"
            'GEMINI_API_KEY = "your_api_key_here"'
        )
    return GeminiClient(api_key=api_key, model_name="models/gemini-flash-latest")
@@ -52,88 +52,89 @@


# -------------------------------
# UI – Layout
# UI – Header
# -------------------------------
st.title("Your Data Humanism Visual Journal")
st.caption(
    "Turn dreams, memories, routines, logs, and messy spreadsheets into "
    "Giorgia Lupi–inspired ‘Dear Data’ visual postcards."
)

left, right = st.columns([0.45, 0.55])


# -------------------------------
# Left column – input controls
# 1. Input Section (always on top)
# -------------------------------
with left:
    st.subheader("1. Add your data")
st.subheader("1. Add your data")

    input_mode = st.radio(
        "How do you want to add data?",
        ("Type or paste text", "Upload a file"),
        horizontal=True,
    )

    text_input = ""
    uploaded_file = None

    if input_mode == "Type or paste text":
        text_input = st.text_area(
            "Write about your dream, memory, routine, or paste any text:",
            height=200,
            placeholder=(
                "Example: I had a dream about walking through a corridor full of "
                "clocks that were melting and vibrating..."
            ),
        )
    else:
        uploaded_file = st.file_uploader(
            "Upload a file (text, PDF, DOCX, CSV, XLSX):",
            type=["txt", "pdf", "docx", "doc", "csv", "xlsx"],
        )
input_mode = st.radio(
    "How do you want to add data?",
    ("Type or paste text", "Upload a file"),
    horizontal=True,
)

    data_type = st.selectbox(
        "What kind of data is this?",
        [
            "Dream",
            "Memory",
            "Daily / weekly routine",
            "Office / attendance logs",
            "Emotional journal",
            "Other / mixed",
        ],
text_input = ""
uploaded_file = None

if input_mode == "Type or paste text":
    text_input = st.text_area(
        "Write about your dream, memory, routine, or paste any text:",
        height=200,
        placeholder=(
            "Example: My weekday routine: I wake up at 7:30, check my phone, "
            "commute, attend classes, go to the gym, cook dinner, study, then sleep..."
        ),
    )

    context = st.text_input(
        "One-line description (optional, helps shape the metaphor):",
        placeholder="e.g., ‘Two weeks of my sleep + coffee habits’",
else:
    uploaded_file = st.file_uploader(
        "Upload a file (text, PDF, DOCX, CSV, XLSX):",
        type=["txt", "pdf", "docx", "doc", "csv", "xlsx"],
    )

    st.markdown("---")
    generate_button = st.button("✨ Generate Dear Data Visual", type="primary")
data_type = st.selectbox(
    "What kind of data is this?",
    [
        "Dream",
        "Memory",
        "Daily / weekly routine",
        "Office / attendance logs",
        "Emotional journal",
        "Other / mixed",
    ],
)

context = st.text_input(
    "One-line description (optional, helps shape the metaphor):",
    placeholder="e.g., ‘One week of my sleep + coffee habits’",
)

generate_button = st.button("✨ Generate Dear Data Visual", type="primary")

st.markdown("---")

# -------------------------------
# Right column – visualization
# 2. Visualization Section (always below inputs)
# -------------------------------
with right:
    st.subheader("2. Your Data Humanism Visualization")
st.subheader("2. Your Data Humanism Visualization")

    # Empty placeholder for later
    placeholder = st.empty()
visual_container = st.container()

    if generate_button:
        # Basic validation
        if not text_input and not uploaded_file:
            st.warning("Please either type/paste some text or upload a file.")
        else:
            try:
                gemini = get_gemini_client()
            except Exception as e:
if not generate_button:
    with visual_container:
        st.info(
            "Fill in your data above and click **Generate Dear Data Visual** "
            "to see your postcard here."
        )
else:
    if not text_input and not uploaded_file:
        st.warning("Please either type/paste some text or upload a file.")
    else:
        try:
            gemini = get_gemini_client()
        except Exception as e:
            with visual_container:
                st.error("Could not initialize Gemini client.")
                st.code(str(e))
            else:
        else:
            with visual_container:
                with st.spinner("Talking to Gemini and drawing your visual postcard..."):
                    try:
                        # 1. Parse raw input into text
@@ -168,9 +169,9 @@
                                except json.JSONDecodeError:
                                    st.error(
                                        "Gemini returned text that is not valid JSON. "
                                        "Enable debug below to inspect the raw output."
                                        "Check the debug panel below."
                                    )
                                    with st.expander("Raw response from Gemini"):
                                    with st.expander("Debug: Raw response from Gemini"):
                                        st.text(visual_spec)
                                    visual_spec = {}

@@ -180,18 +181,21 @@
                                # 4. Render spec → SVG
                                svg = render_visual_spec(visual_spec)

                                # 5. Show SVG inside a framed container
                                # 5. Responsive, centered SVG container
                                html = f"""
                                <div style="
                                    border: 1px solid #444;
                                    padding: 8px;
                                    padding: 16px;
                                    background-color: #111;
                                    border-radius: 10px;
                                    max-width: 980px;
                                    margin: 0 auto 1rem auto;
                                    overflow: hidden;
                                ">
                                    {svg}
                                </div>
                                """
                                placeholder.markdown(html, unsafe_allow_html=True)
                                st.markdown(html, unsafe_allow_html=True)

                                # 6. Download button
                                st.download_button(
@@ -212,9 +216,3 @@
                        st.error("Something went wrong while generating the visual.")
                        with st.expander("Error details"):
                            st.exception(e)
    else:
        # Initial help text when nothing has been generated yet
        st.write(
            "When you click **Generate Dear Data Visual**, your data will be turned "
            "into a Giorgia Lupi–inspired postcard and appear here."
        )
