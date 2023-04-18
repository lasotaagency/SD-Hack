import streamlit as st
from PIL import Image
import io
import numpy as np
import torch
import matplotlib.pyplot as plt
from PIL import Image, ImageOps
import timeit
import redis
from diffusers import DiffusionPipeline

from segmentation import get_lang_sam_mask, resize_image
from inpainting import generate_image, add_alpha_channel, generate_image_upscale, paint_by_example
from config import SD_API_KEY
from lang_sam import LangSAM

@st.cache(allow_output_mutation=True)
def load_langsam():
    model = LangSAM(device='cpu')
    print("SAM / LangSAM Running Locally")
    return model

clothing_types = ["sweater", "shirt", "shorts", "skirt", "pants", "jeans", "jacket", "socks", "shoes", "belt", "sunglasses", "person"]
mask_map = {}
model = load_langsam()

# Function for processing the uploaded image and generating options
def process_image(image_path):
    # Add your image processing logic here
    articles_detected = []

    resized_image_path = resize_image(image_path, './static/images/', "base.jpg")

    for text_prompt in clothing_types:
        st = timeit.default_timer()
        # mask_path = get_mask(predictor, image_path, np.array([[x,y]]))
        article, filename = get_lang_sam_mask(model, resized_image_path, text_prompt)

        if article:
            mask_map[article] = filename
            articles_detected.append(article)
        et = timeit.default_timer()
        print(f"Time taken to generate {text_prompt} mask: {et-st} seconds")
        break

    if 'person' in mask_map:
        mask = Image.open(mask_map['person'])
        bg_mask = ImageOps.invert(mask)
        bg_mask.save('./static/masks/background_mask.png')
        mask_map['background'] = './static/masks/background_mask.png'


    return articles_detected, mask_map

st.title("FabricAI DEMO")

reset_button = st.button("Reset")

if reset_button:
    st.experimental_rerun()

uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_image is not None:
    img = Image.open(uploaded_image)
    st.image(img, caption="Uploaded Image", use_column_width=True)

    options, mask_map = process_image(uploaded_image)
    selected_option = st.selectbox("Select one of the options", options)

    second_input_type = st.radio("Select second input type", ("Text", "Image"))

    second_input = None
    if second_input_type == "Text":
        second_input = st.text_input("Enter text")
    else:
        uploaded_second_image = st.file_uploader("Upload a second image", type=["jpg", "jpeg", "png"])
        if uploaded_second_image is not None:
            second_img = Image.open(uploaded_second_image)
            st.image(second_img, caption="Uploaded Second Image", use_column_width=True)
            second_input = second_img

    if second_input is not None:
        if second_input_type == "Text":
            print("SD Conditioned on Text")
            image_alpha_path = add_alpha_channel(uploaded_image, mask_map[selected_option])
            result_images = generate_image(image_alpha_path, mask_map[selected_option], second_input, api_key=SD_API_KEY)
        
        if second_input_type == "Image":
            print("SD Conditioned on Image")
            result_images = paint_by_example(uploaded_image, mask_map[selected_option], second_input)
        
        for result_img in result_images:
            st.image(result_img, use_column_width=True)