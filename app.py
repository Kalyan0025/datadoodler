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
    initial_sidebar_state="collapsed",
)


# -------------------------------
# Helpers
# -------------------------------
@st.cache_resource(show_spinner=False)
def get_gemini_client() -> GeminiClient:
    """Create a single Gemini client using Streamlit secrets."""
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing. "
            "In Streamlit Cloud, go to • Manage app → Secrets • and add:\n"
            'GEMINI_API_KEY = "your_api_key_here"'
        )
    return GeminiClient(api_key=api_key, model_name="models/gemini-flash-latest")


def build_combined_input(data_type: str, context: str, parsed_data: str) -> str:
    """Combine meta info + parsed content into a single prompt string."""
    return textwrap.dedent(
        f"""
        DATA TYPE: {data_type}
        DESCRIPTION: {context or "Not provided"}

        RAW DATA BELOW:
        ----------------
        {parsed_data}
        """
    ).strip()


# -------------------------------
# UI – Header
# -------------------------------
st.title("Your Data Humanism Visual Journal")
st.caption(
    "Turn dreams, memories, routines, logs, and messy spreadsheets into "
    "Giorgia Lupi–inspired ‘Dear Data’ visual postcards."
)

# -------------------------------
# 1. Input Section (always on top)
# -------------------------------
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
            "Example: My weekday routine: I wake up at 7:30, check my phone, "
            "commute, attend classes, go to the gym, cook dinner, study, then sleep..."
        ),
    )
else:
    uploaded_file = st.file_uploader(
        "Upload a file (text, PDF, DOCX, CSV, XLSX):",
        type=["txt", "pdf", "docx", "doc", "csv", "xlsx"],
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
)

context = st.text_input(
    "One-line description (optional, helps shape the metaphor):",
    placeholder="e.g., ‘One week of my sleep + coffee habits’",
)

generate_button = st.button("✨ Generate Dear Data Visual", type="primary")

st.markdown("---")

# -------------------------------
# 2. Visualization Section (always below inputs)
# -------------------------------
st.subheader("2. Your Data Humanism Visualization")

visual_container = st.container()

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
            with visual_container:
                with st.spinner("Talking to Gemini and drawing your visual postcard..."):
                    try:
                        # 1. Parse raw input into text
                        parsed_data = parse_input_data(
                            text_input=text_input,
                            uploaded_file=uploaded_file,
                        )

                        if not parsed_data.strip():
                            st.error(
                                "I couldn't extract any readable text from your input. "
                                "Try typing some text or using a simpler file."
                            )
                        else:
                            # 2. Build combined input for model
                            combined_input = build_combined_input(
                                data_type=data_type,
                                context=context,
                                parsed_data=parsed_data,
                            )

                            # 3. Ask Gemini to design a visual spec (JSON-like)
                            visual_spec = generate_visual_spec(
                                input_data=combined_input,
                                gemini=gemini,
                            )

                            # visual_spec might be dict or JSON string
                            if isinstance(visual_spec, str):
                                try:
                                    visual_spec = json.loads(visual_spec)
                                except json.JSONDecodeError:
                                    st.error(
                                        "Gemini returned text that is not valid JSON. "
                                        "Check the debug panel below."
                                    )
                                    with st.expander("Debug: Raw response from Gemini"):
                                        st.text(visual_spec)
                                    visual_spec = {}

                            if not isinstance(visual_spec, dict):
                                st.error("Visual spec is not a valid JSON object.")
                            else:
                                # 4. Render spec → SVG
                                svg = render_visual_spec(visual_spec)

                                # 5. Responsive, centered SVG container
                                html = f"""
                                <div style="
                                    border: 1px solid #444;
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
                                st.markdown(html, unsafe_allow_html=True)

                                # 6. Download button
                                st.download_button(
                                    label="⬇️ Download SVG postcard",
                                    data=svg,
                                    file_name="visual_journal.svg",
                                    mime="image/svg+xml",
                                )

                                # 7. Debug / spec inspector
                                with st.expander("Debug: Visual spec JSON"):
                                    st.code(
                                        json.dumps(visual_spec, indent=2),
                                        language="json",
                                    )

                    except Exception as e:
                        st.error("Something went wrong while generating the visual.")
                        with st.expander("Error details"):
                            st.exception(e)
