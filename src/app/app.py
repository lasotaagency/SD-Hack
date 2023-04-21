from flask import Flask, render_template, request, url_for, jsonify, session
from flask_cors import CORS
from flask_session import Session
import os
from segment_anything import sam_model_registry, SamPredictor
import numpy as np
import torch
import matplotlib.pyplot as plt
from PIL import Image, ImageOps
import timeit
import redis
from diffusers import DiffusionPipeline
import gc

from segmentation import get_lang_sam_mask
from inpainting import generate_image, add_alpha_channel, generate_image_upscale, paint_by_example
from config import SD_API_KEY
from lang_sam import LangSAM

app = Flask(__name__)
app.secret_key = 'T\xaf\x89\xcb\x8b\xd2\xbf{\x8a\xe0S\x12\xce6B2Gc\xc6f\x01o\xd0c'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.config["IMAGE_UPLOADS"] = "static/images"
cors = CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

@app.route("/", methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":
        if request.files:
            image = request.files["image"]
            image_path = os.path.join(app.config["IMAGE_UPLOADS"], image.filename)
            image.save(image_path)

            articles_detected = []
            bbox_list = []

            resized_image_path = resize_image(image_path, app.config["IMAGE_UPLOADS"], image.filename)
            
            resized_image_url = url_for('static', filename=f'images/{os.path.basename(resized_image_path)}')
            for text_prompt in clothing_types:
                st = timeit.default_timer()
                # mask_path = get_mask(predictor, image_path, np.array([[x,y]]))
                article, filename, bbox = get_lang_sam_mask(model, resized_image_path, text_prompt)
                bbox_list.append({"name": article, "coordinates": bbox})

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

            session['image_url'] = resized_image_url
            # model = 0
            return render_template("index.html", image_url=resized_image_url, articles_detected=articles_detected, segments_data=bbox_list)
        
    return render_template("index.html")

@app.route("/upload_image", methods=["POST"])
def upload_image_from_client():
    if request.method == "POST":
        if request.files:
            # if 'model' not in app.config:
                # app.config['model'] = load_lang_sam()

            image = request.files["file"]
            image_path = os.path.join(app.config["IMAGE_UPLOADS"], image.filename)
            image.save(image_path)

            articles_detected = []
            bbox_list = []

            resized_image_path = resize_image(image_path, app.config["IMAGE_UPLOADS"], image.filename)

            resized_image_url = url_for('static', filename=f'images/{os.path.basename(resized_image_path)}')
            for text_prompt in clothing_types:
                st = timeit.default_timer()
                article, filename, bbox = get_lang_sam_mask(model, resized_image_path, text_prompt)
                bbox_list.append({"name": article, "coordinates": bbox})

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

            session['image_url'] = resized_image_url
            print(session)

            response = jsonify({"status": "success", "image_url": resized_image_url, "articles_detected": articles_detected, "segments_data": bbox_list})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response


@app.route("/upload_additional_image", methods=["POST"])
def upload_additional_image():
    if request.method == "POST":
        if request.files:
            image = request.files["additional_image"]
            image_path = os.path.join(app.config["IMAGE_UPLOADS"], image.filename)
            image.save(image_path)
            print("saving 2nd condition image")
            image_url = url_for("static", filename=os.path.join("images", image.filename))

            return jsonify({"status": "success", "image_url": image_url})

    return jsonify({"status": "error", "message": "Invalid request"})


@app.route("/submit", methods=["POST"])
def submit_data():
    data = request.get_json()
    image_url = data['image_url']
    # image_url = session['image_url']
    # x, y = data['coordinates']
    print('started generating images')
    model = None
    gc.collect()
    torch.cuda.empty_cache()

    if data['condition_type'] == "text":
        print("Started Text Conditioning")
        image_path = os.path.join(app.config["IMAGE_UPLOADS"], os.path.basename(image_url))

        st = timeit.default_timer()
        option = data['option']

        image_alpha_path = add_alpha_channel(image_path, mask_map[option])
        generated_image_paths = generate_image(image_alpha_path, mask_map[option], data["condition_data"], api_key=SD_API_KEY)

        et = timeit.default_timer()
        print('Time taken to generate images from API: {} seconds'.format(et-st))

    else:
        print("Started Image Conditioning")
        image_cond = data['condition_data']
        image_cond_path = os.path.join(app.config["IMAGE_UPLOADS"], os.path.basename(image_cond))
        st = timeit.default_timer()
        option = data['option']
        resized_image_path = os.path.join(app.config["IMAGE_UPLOADS"], os.path.basename(image_url))
        generated_image_paths = paint_by_example(resized_image_path, mask_map[option], image_cond_path, 2)
        et = timeit.default_timer()
        print('Time taken to generate inpainted from diffuser: {} seconds'.format(et-st))

    print(generated_image_paths)
    response = jsonify({"status": "success", "generated_images": generated_image_paths})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route("/set_main_image", methods=["POST"])
def set_main_image():
    session['image_url'] = request.get_json()['image_url']
    return jsonify({"status": "success"})

def resize_image(image_path, output_folder, filename, multiple=64, min_pixels=262144, max_pixels=640000):
    """
    Resize an image so that its dimensions are multiples of a given number while maintaining its aspect ratio.
    The total number of pixels in the resized image will be less than max_pixels.

    :param image_path: Path to the input image
    :param output_folder: Folder to save the resized image
    :param filename: Name of the output file
    :param multiple: An integer value that dimensions must be a multiple of (default: 64)
    :param max_pixels: Maximum number of pixels in the resized image (default: 1048576)
    :return: A path to the resized image
    """
    image = Image.open(image_path)
    image = image.convert('RGB')
    width, height = image.size
    aspect_ratio = float(width) / float(height)

    # Calculate new dimensions
    new_height = int(height // multiple * multiple)
    new_width = int(aspect_ratio * new_height)

    # Make sure the width is also a multiple of the given number
    new_width = new_width // multiple * multiple

    # Check if the resized image has more pixels than max_pixels
    while new_width * new_height > max_pixels:
        new_height = new_height - multiple
        new_width = int(aspect_ratio * new_height)
        new_width = new_width // multiple * multiple

      # Check if the resized image has fewer pixels than min_pixels
    while new_width * new_height < min_pixels:
        new_height = new_height + multiple
        new_width = int(aspect_ratio * new_height)
        new_width = new_width // multiple * multiple

    filename, file_extension = os.path.splitext(filename)
    # Resize the image
    resized_image = image.resize((new_width, new_height), Image.ANTIALIAS)
    resized_image_path = os.path.join(output_folder, f"{filename}_resized{file_extension}")
    resized_image.save(resized_image_path)
    print("Resized image saved to", resized_image_path)
    return resized_image_path

def load_lang_sam(device='cuda'):
    model = LangSAM(device=device)
    print("SAM / LangSAM Running Locally")

    return model

if __name__ == "__main__":
    # predictor = startup_sam()
    model = load_lang_sam()
    mask_map = {}
    clothing_types = ["sweater", "shirt", "shorts", "skirt", "pants", "jeans", "jacket", "shoes", "belt", "sunglasses", "person"]

    # pipe = DiffusionPipeline.from_pretrained(
    # "Fantasy-Studio/Paint-by-Example",
    # torch_dtype=torch.float16,
    # )

    # pipe = pipe.to(device)
    # print("Inpainting Pipe Running Locally")
    # r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    app.run(debug=True, reloader_type='stat')