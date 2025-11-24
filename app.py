import streamlit as st
from renderer import render_visual_spec
import random

# Streamlit app setup
st.set_page_config(page_title="Visual Journal Bot", layout="wide")

# Page title and description
st.title("Visual Journal Bot")
st.markdown("Upload or type your natural language data, and get a visual representation based on data humanism.")

# Mood selector for visual mood representation (can be expanded based on input data)
mood = st.selectbox("Select Mood", ["Positive", "Neutral", "Negative"])

# Change background color based on mood
if mood == "Positive":
    st.markdown('<style>body {background-color: #FFFAF0;}</style>', unsafe_allow_html=True)
elif mood == "Negative":
    st.markdown('<style>body {background-color: #D8E3E7;}</style>', unsafe_allow_html=True)
else:
    st.markdown('<style>body {background-color: #F7F3EB;}</style>', unsafe_allow_html=True)

# Input box for raw natural language data
raw_data = st.text_area("Enter your natural language data here:")

# Process the data to extract key information
if raw_data:
    # Sample processing of raw data (expand with NLP models)
    # For now, just extracting keywords (in reality, you may use NLP tools like SpaCy or NLTK)
    mood_keywords = ["happy", "sad", "neutral", "excited", "angry", "calm"]
    mood_value = "Neutral"  # Default mood

    for mood_word in mood_keywords:
        if mood_word in raw_data.lower():
            mood_value = mood_word.capitalize()
            break

    # Simulate some extracted data (replace with actual NLP)
    extracted_data = {
        "mood": mood_value,
        "hours_worked": random.randint(4, 12),  # Randomly simulating hours worked
        "energy": random.choice(["Low", "Medium", "High"]),  # Randomly simulating energy levels
    }

    # Log the extracted data (for debugging)
    st.write(f"Extracted Data: {extracted_data}")

    # Generate the visual spec from the extracted data
    visual_spec = render_visual_spec(extracted_data)

    # Display the generated SVG or interactive Observable visual
    st.markdown(
        f'<div style="overflow: hidden; position: relative; width: 100%;">'
        f'{visual_spec}'
        '</div>', unsafe_allow_html=True
    )
else:
    st.warning("Please enter your natural language data to visualize.")
