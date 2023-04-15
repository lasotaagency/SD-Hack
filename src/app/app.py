from flask import Flask, render_template, request, url_for, jsonify
import os
from segment_anything import sam_model_registry, SamPredictor
import numpy as np
import torch
import matplotlib.pyplot as plt
import cv2
import sys

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
            image.save(os.path.join(app.config["IMAGE_UPLOADS"], image.filename))
            image_url = url_for('static', filename=f'uploads/{image.filename}')
            return render_template("index.html", image_url=image_url)

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

    return jsonify({"status": "success", "generated_images": generated_image_paths})

if __name__ == "__main__":
    predictor = startup_sam()
    print("SAM Running Locally")
    app.run(debug=True)