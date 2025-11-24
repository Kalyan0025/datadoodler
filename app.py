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
    page_title="Data Doodler – Visual Journal",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -------------------------------
# Custom CSS - Observable-inspired design
# -------------------------------
st.markdown("""
<style>
    /* Global styles */
    * {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container with grid background */
    .stApp {
        background-color: #1a1a1a;
        background-image: 
            linear-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
        background-size: 50px 50px;
    }
    
    /* Hero section */
    .hero-section {
        text-align: center;
        padding: 60px 20px 40px 20px;
        max-width: 1200px;
        margin: 0 auto;
        position: relative;
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 300;
        color: #e5e7eb;
        margin-bottom: 1rem;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }
    
    .spiral-container {
        position: absolute;
        top: 20px;
        right: -60px;
        width: 100px;
        height: 100px;
        opacity: 0.6;
    }
    
    .spiral {
        width: 100%;
        height: 100%;
        animation: spiral-rotate 20s linear infinite;
    }
    
    @keyframes spiral-rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .hero-subtitle {
        font-size: 1.15rem;
        color: #9ca3af;
        max-width: 800px;
        margin: 0 auto 2.5rem auto;
        line-height: 1.6;
        font-weight: 300;
    }
    
    /* Data type grid */
    .data-type-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
        max-width: 1200px;
        margin: 0 auto 50px auto;
        padding: 0 20px;
    }
    
    .data-type-card {
        background: rgba(40, 40, 40, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 0;
        padding: 36px 24px;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
    }
    
    .data-type-card::before,
    .data-type-card::after {
        content: '';
        position: absolute;
        width: 6px;
        height: 6px;
        background: rgba(224, 118, 56, 0.5);
        transition: all 0.3s ease;
    }
    
    .data-type-card::before { top: -4px; left: -4px; }
    .data-type-card::after { top: -4px; right: -4px; }
    
    .data-type-card:hover {
        border-color: #E07638;
        border-width: 2px;
        transform: translateY(-2px);
        background: rgba(224, 118, 56, 0.05);
    }
    
    .data-type-card:hover::before,
    .data-type-card:hover::after {
        background: #E07638;
        width: 8px;
        height: 8px;
    }
    
    .data-type-card.selected {
        border-color: #E07638;
        border-width: 2px;
        background: rgba(224, 118, 56, 0.08);
    }
    
    .data-type-card.selected::before,
    .data-type-card.selected::after {
        background: #E07638;
        width: 8px;
        height: 8px;
    }
    
    .card-title {
        font-size: 1.3rem;
        font-weight: 400;
        color: #e5e7eb;
        margin-bottom: 12px;
        letter-spacing: -0.01em;
    }
    
    .card-description {
        font-size: 0.9rem;
        color: #9ca3af;
        line-height: 1.6;
        font-weight: 300;
    }
    
    /* Input section */
    .input-section {
        max-width: 900px;
        margin: 40px auto;
        padding: 0 20px;
    }
    
    .section-title {
        font-size: 0.75rem;
        color: #9ca3af;
        margin-bottom: 16px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 500;
    }
    
    /* Streamlit component styling */
    .stTextArea {
        position: relative !important;
    }
    
    .stTextArea::before,
    .stTextArea::after {
        content: '';
        position: absolute;
        width: 6px;
        height: 6px;
        background: rgba(224, 118, 56, 0.5);
        z-index: 10;
        pointer-events: none;
        transition: all 0.3s ease;
    }
    
    .stTextArea::before { top: -4px; left: -4px; }
    .stTextArea::after { top: -4px; right: -4px; }
    
    .stTextArea:focus-within::before,
    .stTextArea:focus-within::after {
        background: #E07638;
        width: 8px;
        height: 8px;
    }
    
    .stTextArea textarea {
        background: rgba(40, 40, 40, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 0 !important;
        color: #e5e7eb !important;
        font-size: 0.95rem !important;
        font-weight: 300 !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #E07638 !important;
        border-width: 2px !important;
        box-shadow: none !important;
        background: rgba(224, 118, 56, 0.05) !important;
    }
    
    .stTextInput {
        position: relative !important;
    }
    
    .stTextInput::before,
    .stTextInput::after {
        content: '';
        position: absolute;
        width: 6px;
        height: 6px;
        background: rgba(224, 118, 56, 0.5);
        z-index: 10;
        pointer-events: none;
        transition: all 0.3s ease;
    }
    
    .stTextInput::before { top: -4px; left: -4px; }
    .stTextInput::after { top: -4px; right: -4px; }
    
    .stTextInput:focus-within::before,
    .stTextInput:focus-within::after {
        background: #E07638;
        width: 8px;
        height: 8px;
    }
    
    .stTextInput input {
        background: rgba(40, 40, 40, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 0 !important;
        color: #e5e7eb !important;
        font-weight: 300 !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput input:focus {
        border-color: #E07638 !important;
        border-width: 2px !important;
        box-shadow: none !important;
        background: rgba(224, 118, 56, 0.05) !important;
    }
    
    /* Radio buttons */
    .stRadio > label {
        color: #9ca3af !important;
        font-weight: 400 !important;
        font-size: 0.75rem !important;
        margin-bottom: 12px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    
    .stRadio [role="radiogroup"] {
        gap: 12px !important;
        margin-bottom: 20px !important;
        display: flex !important;
    }
    
    .stRadio [role="radiogroup"] label {
        background: rgba(40, 40, 40, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 0 !important;
        padding: 10px 20px !important;
        color: #9ca3af !important;
        font-weight: 300 !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        font-size: 0.9rem !important;
    }
    
    .stRadio [role="radiogroup"] label:hover {
        border-color: #E07638 !important;
        border-width: 2px !important;
        background: rgba(224, 118, 56, 0.05) !important;
        color: #e5e7eb !important;
    }
    
    /* File uploader */
    .stFileUploader {
        margin-bottom: 20px;
        position: relative !important;
    }
    
    .stFileUploader::before,
    .stFileUploader::after {
        content: '';
        position: absolute;
        width: 6px;
        height: 6px;
        background: rgba(224, 118, 56, 0.5);
        z-index: 10;
        pointer-events: none;
        transition: all 0.3s ease;
    }
    
    .stFileUploader::before { top: -4px; left: -4px; }
    .stFileUploader::after { top: -4px; right: -4px; }
    
    .stFileUploader:hover::before,
    .stFileUploader:hover::after {
        background: #E07638;
        width: 8px;
        height: 8px;
    }
    
    .stFileUploader section {
        background: rgba(40, 40, 40, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 0 !important;
        padding: 24px !important;
    }
    
    .stFileUploader section:hover {
        border-color: #E07638 !important;
        border-width: 2px !important;
        background: rgba(224, 118, 56, 0.05) !important;
    }
    
    .stFileUploader label {
        color: #9ca3af !important;
        font-weight: 300 !important;
    }
    
    .stFileUploader button {
        background: rgba(60, 60, 60, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 0 !important;
        color: #e5e7eb !important;
        font-weight: 400 !important;
        padding: 8px 20px !important;
    }
    
    .stFileUploader button:hover {
        border-color: #E07638 !important;
        color: #E07638 !important;
    }
    
    /* Success/Info messages */
    .stSuccess {
        background: rgba(224, 118, 56, 0.1) !important;
        border: 1px solid rgba(224, 118, 56, 0.3) !important;
        border-radius: 0 !important;
        color: #E07638 !important;
        padding: 12px !important;
    }
    
    .stInfo {
        background: rgba(100, 100, 100, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 0 !important;
        color: #9ca3af !important;
    }
    
    /* Button */
    .stButton button {
        background: rgba(40, 40, 40, 0.3) !important;
        color: #e5e7eb !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 0 !important;
        padding: 12px 32px !important;
        font-weight: 400 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover {
        background: rgba(224, 118, 56, 0.08) !important;
        border-color: #E07638 !important;
        border-width: 2px !important;
        color: #E07638 !important;
    }
    
    /* Canvas section */
    .canvas-section {
        max-width: 1400px;
        margin: 50px auto;
        padding: 0 20px;
    }
    
    .canvas-title {
        font-size: 1.5rem;
        font-weight: 300;
        color: #e5e7eb;
        margin-bottom: 24px;
        text-align: center;
        letter-spacing: -0.01em;
    }
</style>
""", unsafe_allow_html=True)


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
# Data type definitions
# -------------------------------
DATA_TYPES = {
    "Dream": "Visualize your dreams with surreal, abstract patterns and flowing symbols",
    "Memory": "Transform memories into nostalgic visual narratives with timelines and motifs",
    "Daily / Weekly Routine": "Map your routines into rhythmic patterns showing habits and cycles",
    "Office / Attendance Logs": "Turn attendance data into geometric grids revealing presence patterns",
    "Emotional Journal": "Express emotions through color gradients, shapes, and intensities",
    "Other / Mixed": "Custom visualization for any type of personal data or mixed content"
}


# -------------------------------
# UI – Hero Section
# -------------------------------
st.markdown("""
<div class="hero-section">
    <div style="position: relative; display: inline-block;">
        <h1 class="hero-title">Data Doodler</h1>
        <div class="spiral-container">
            <svg class="spiral" viewBox="0 0 100 100">
                <defs>
                    <linearGradient id="spiralGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#E07638" />
                        <stop offset="100%" style="stop-color:#ff8c42" />
                    </linearGradient>
                </defs>
                <path d="M50,50 Q50,30 60,30 Q70,30 70,40 Q70,50 60,50 Q50,50 50,40 Q50,30 40,30 Q30,30 30,40 Q30,60 50,60 Q70,60 70,40 Q70,20 50,20 Q30,20 30,40 Q30,70 60,70 Q80,70 80,50 Q80,30 60,30" 
                      fill="none" stroke="url(#spiralGradient)" stroke-width="2" stroke-linecap="round" opacity="0.8"/>
            </svg>
        </div>
    </div>
    <p class="hero-subtitle">
        Transform your personal data into Dear Data-style visualizations. 
        Choose a data type, add your content, and watch as your life becomes art.
    </p>
</div>
""", unsafe_allow_html=True)


# -------------------------------
# Data Type Selection Cards
# -------------------------------
st.markdown('<div class="data-type-grid">', unsafe_allow_html=True)

# Initialize session state
if 'selected_data_type' not in st.session_state:
    st.session_state.selected_data_type = None

# Create clickable cards
for data_type, description in DATA_TYPES.items():
    selected_class = "selected" if st.session_state.selected_data_type == data_type else ""
    
    # Use HTML/JavaScript for click detection
    card_html = f"""
    <div class="data-type-card {selected_class}" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', data: '{data_type}'}}, '*')">
        <div class="card-title">{data_type}</div>
        <div class="card-description">{description}</div>
    </div>
    """
    
    # Display card and add button for functionality
    cols = st.columns([20, 1])
    with cols[0]:
        st.markdown(card_html, unsafe_allow_html=True)
    with cols[1]:
        if st.button("", key=f"select_{data_type}", help=f"Select {data_type}"):
            st.session_state.selected_data_type = data_type
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)


# Show input section only if a data type is selected
if st.session_state.selected_data_type:
    st.markdown("---")
    
    # -------------------------------
    # Input Section
    # -------------------------------
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    st.markdown(f'<p class="section-title">Add Your {st.session_state.selected_data_type} Data</p>', unsafe_allow_html=True)
    
    input_mode = st.radio(
        "Choose input method:",
        ("Type or paste text", "Upload a file"),
        horizontal=True,
        key="input_mode_radio"
    )
    
    text_input = ""
    uploaded_file = None
    
    if input_mode == "Type or paste text":
        text_input = st.text_area(
            "Your data",
            height=200,
            placeholder=f"Enter your {st.session_state.selected_data_type.lower()} data here...",
            label_visibility="collapsed",
            key="text_area_input"
        )
    else:
        st.markdown('<p style="color: #9ca3af; font-size: 0.75rem; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.05em;">Upload your data file</p>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["txt", "pdf", "docx", "doc", "csv", "xlsx"],
            label_visibility="collapsed",
            key="file_uploader_input"
        )
        
        if uploaded_file:
            st.success(f"✓ File uploaded: {uploaded_file.name}")
    
    context = st.text_input(
        "Add context (optional)",
        placeholder="e.g., 'One week of my sleep patterns' or 'My morning routine in winter'",
        label_visibility="collapsed",
        key="context_input"
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button("✨ Generate Visualization", type="primary", use_container_width=True, key="generate_btn")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # -------------------------------
    # Visualization Section
    # -------------------------------
    st.markdown('<div class="canvas-section">', unsafe_allow_html=True)
    st.markdown('<h2 class="canvas-title">Your Visual Journal</h2>', unsafe_allow_html=True)
    
    visual_container = st.container()
    
    if not generate_button:
        with visual_container:
            st.info(
                f"Your visualization will appear here once generated. Add your {st.session_state.selected_data_type.lower()} data above to begin."
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
                    with st.spinner("Creating your visual journal..."):
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
                                    data_type=st.session_state.selected_data_type,
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

                                    # 5. Responsive, centered SVG container with corners
                                    html = f"""
                                    <div style="
                                        border: 1px solid rgba(255, 255, 255, 0.15);
                                        padding: 32px;
                                        background: rgba(40, 40, 40, 0.3);
                                        border-radius: 0;
                                        width: 100%;
                                        max-width: 100%;
                                        margin: 0 auto 2rem auto;
                                        overflow: hidden;
                                        position: relative;
                                    ">
                                        <div style="position: absolute; top: -4px; left: -4px; width: 8px; height: 8px; background: #E07638;"></div>
                                        <div style="position: absolute; top: -4px; right: -4px; width: 8px; height: 8px; background: #E07638;"></div>
                                        <div style="position: absolute; bottom: -4px; left: -4px; width: 8px; height: 8px; background: #E07638;"></div>
                                        <div style="position: absolute; bottom: -4px; right: -4px; width: 8px; height: 8px; background: #E07638;"></div>
                                        <div style="width: 100%; max-width: 100%; overflow-x: auto;">
                                            {svg}
                                        </div>
                                    </div>
                                    """
                                    st.markdown(html, unsafe_allow_html=True)

                                    # 6. Download button
                                    col1, col2, col3 = st.columns([1, 2, 1])
                                    with col2:
                                        st.download_button(
                                            label="⬇️ Download SVG",
                                            data=svg,
                                            file_name="visual_journal.svg",
                                            mime="image/svg+xml",
                                            use_container_width=True
                                        )

                                    # 7. Debug / spec inspector
                                    with st.expander("🔍 View Technical Spec (JSON)"):
                                        st.code(
                                            json.dumps(visual_spec, indent=2),
                                            language="json",
                                        )

                        except Exception as e:
                            st.error("Something went wrong while generating the visual.")
                            with st.expander("Error details"):
                                st.exception(e)
    
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # Show placeholder when no data type selected
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px; color: #6b7280;">
        <p style="font-size: 1.1rem;">👆 Select a data type above to begin</p>
    </div>
    """, unsafe_allow_html=True)
