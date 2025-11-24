import streamlit as st
import json
from renderer import render_visual_spec

# Streamlit app setup
st.set_page_config(page_title="Visual Journal Bot", layout="wide")

# Page title and description
st.title("Visual Journal Bot")
st.markdown("Upload your JSON file to generate a personalized visualization.")

# Mood selector (example of user interaction)
mood = st.selectbox("Select Mood", ["Positive", "Neutral", "Negative"])

# Change background based on mood
if mood == "Positive":
    st.markdown('<style>body {background-color: #FFFAF0;}</style>', unsafe_allow_html=True)
elif mood == "Negative":
    st.markdown('<style>body {background-color: #D8E3E7;}</style>', unsafe_allow_html=True)
else:
    st.markdown('<style>body {background-color: #F7F3EB;}</style>', unsafe_allow_html=True)

# File uploader for JSON data
uploaded_file = st.file_uploader("Upload your data file (JSON)", type=["json"])

if uploaded_file:
    # Read the uploaded file
    data = json.load(uploaded_file)

    # Render the visual spec (can call Observable code here if needed)
    visual_spec = render_visual_spec(data)

    # Display the generated SVG or interactive Observable visual
    st.markdown(
        f'<div style="overflow: hidden; position: relative; width: 100%;">'
        f'{visual_spec}'
        '</div>', unsafe_allow_html=True
    )
    
    # Optionally embed an ObservableHQ iframe (if using Observable directly)
    observable_url = "https://observablehq.com/@yourusername/your-notebook"
    st.markdown(f'<iframe src="{observable_url}" width="100%" height="500px" frameborder="0"></iframe>', unsafe_allow_html=True)
