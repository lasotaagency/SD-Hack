from flask import Flask, render_template, request, url_for, jsonify
import os
from segment_anything import sam_model_registry, SamPredictor
import numpy as np
import torch
import matplotlib.pyplot as plt
import cv2
import sys
from PIL import Image, ImageOps
import timeit
import base64
import redis

from segmentation import get_SAM_mask, startup_sam, get_lang_sam_mask
from inpainting import generate_image, add_alpha_channel
from config import SD_API_KEY
from lang_sam import LangSAM

app = Flask(__name__)
app.config["IMAGE_UPLOADS"] = "static/images"

@app.route("/", methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":
        if request.files:
            image = request.files["image"]
            image_path = os.path.join(app.config["IMAGE_UPLOADS"], image.filename)
            image.save(image_path)

            articles_detected = []

            resized_image_path = resize_image(image_path, app.config["IMAGE_UPLOADS"], image.filename)
            
            resized_image_url = url_for('static', filename=f'images/{os.path.basename(resized_image_path)}')
            for text_prompt in clothing_types:
                st = timeit.default_timer()
                # mask_path = get_mask(predictor, image_path, np.array([[x,y]]))
                article, filename = get_lang_sam_mask(model, resized_image_path, text_prompt)

                if article:
                    mask_map[article] = filename
                    articles_detected.append(article)
                et = timeit.default_timer()
                print(f"Time taken to generate {text_prompt} mask: {et-st} seconds")

            if 'person' in mask_map:
                mask = Image.open(mask_map['person'])
                bg_mask = ImageOps.invert(mask)
                bg_mask.save('./static/masks/background_mask.png')
                mask_map['background'] = './static/masks/background_mask.png'

            # for key in mask_map:
            #     r.set(key, image_file_to_base64(mask_map[key]))

            return render_template("index.html", image_url=resized_image_url, articles_detected=list(mask_map.keys()), masks=list(mask_map.values()))
        
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit_data():
    data = request.get_json()
    image_url = data['image_url']
    text = data['text']
    x, y = data['coordinates']

    print("Submitted Image url is: ", image_url)
    image_path = os.path.join(app.config["IMAGE_UPLOADS"], os.path.basename(image_url))

    st = timeit.default_timer()
    option = data['option']

    image_alpha_path = add_alpha_channel(image_path, mask_map[option])
    generated_image_paths = generate_image(image_alpha_path, mask_map[option], text, api_key=SD_API_KEY)
    et = timeit.default_timer()
    print('Time taken to generate images from API: {} seconds'.format(et-st))

    return jsonify({"status": "success", "generated_images": generated_image_paths})


def resize_image(image_path, output_folder, filename, multiple=64):
    """
    Resize an image so that its dimensions are multiples of a given number while maintaining its aspect ratio.

    :param image: A PIL Image object
    :param multiple: An integer value that dimensions must be a multiple of (default: 64)
    :return: A PIL Image object with resized dimensions
    """
    image = Image.open(image_path)
    width, height= image.size
    aspect_ratio = float(width) / float(height)

    # Calculate new dimensions
    new_height = int(height // multiple * multiple)
    new_width = int(aspect_ratio * new_height)

    # Make sure the width is also a multiple of the given number
    new_width = new_width // multiple * multiple

    filename, file_extension = os.path.splitext(filename)
    # Resize the image
    resized_image = image.resize((new_width, new_height), Image.ANTIALIAS)
    resized_image_path = os.path.join(output_folder, f"{filename}_resized{file_extension}")
    resized_image.save(resized_image_path)
    print("Resized image saved to", resized_image_path)
    return resized_image_path

# def image_file_to_base64(image_path):
#     with open(image_path, "rb") as f:
#         img_data = f.read()
#     return base64.b64encode(img_data).decode('utf-8')

if __name__ == "__main__":
    # predictor = startup_sam()
    model = LangSAM()
    clothing_types = ["sweater", "shirt", "shorts", "skirt", "pants", "jeans", "jacket", "socks", "shoes", "belt", "sunglasses", "person"]
    mask_map = {}

    # r = redis.Redis(host='localhost', port=6379, decode_responses=True)

    print("SAM / LangSAM Running Locally")
    app.run(debug=True)