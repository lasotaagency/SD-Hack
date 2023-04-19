import streamlit as st
from PIL import Image

logo = Image.open("./fabric.ai.png")

with st.sidebar:
    
    target_clothing_type = st.selectbox("Select Clothing", ["Shirt", "Pant"])
    text_prompt_input = st.text_input("Enter Text Prompt")
    image_prompt_input = st.file_uploader("Upload Image Prompt")
    submit_button = st.button("Submit")
    logo_image = st.image(logo)

uploaded_file = st.file_uploader("Upload your image")