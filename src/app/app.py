from flask import Flask, render_template, request, url_for, jsonify
import os
from segment_anything import sam_model_registry, SamPredictor
import numpy as np
import torch
import matplotlib.pyplot as plt
import cv2
import sys
from PIL import Image

from segmentation import get_mask, startup_sam
from inpainting import generate_image
from config import SD_API_KEY

app = Flask(__name__)
app.config["IMAGE_UPLOADS"] = "static/uploads"

@app.route("/", methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":
        if request.files:
            image = request.files["image"]
            image_path = os.path.join(app.config["IMAGE_UPLOADS"], image.filename)
            image.save(image_path)

            resized_image_path = resize_image(image_path, app.config["IMAGE_UPLOADS"], image.filename)
            
            resized_image_url = url_for('static', filename=f'uploads/{os.path.basename(resized_image_path)}')
            return render_template("index.html", image_url=resized_image_url)
        
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit_data():
    data = request.get_json()
    image_url = data['image_url']
    text = data['text']
    x, y = data['coordinates']

    image_path = os.path.join(app.config["IMAGE_UPLOADS"], os.path.basename(image_url))
    mask_path = get_mask(predictor, image_path, np.array([[x,y]]))

    generated_image_paths = generate_image(image_path, mask_path, text, api_key=SD_API_KEY)
    print(generated_image_paths)

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

if __name__ == "__main__":
    predictor = startup_sam()
    print("SAM Running Locally")
    app.run(debug=True)