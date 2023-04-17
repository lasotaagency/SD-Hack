import base64
import os
import requests
from PIL import Image
import numpy as np
import time

def add_alpha_channel(image_path, mask_path, transparency=0.5):
    # Open the image and mask
    image = Image.open(image_path)
    mask = Image.open(mask_path).convert('L')  # convert to grayscale

    # Create a new RGBA image with the same size as the original image
    alpha = Image.new('RGBA', image.size, (0, 0, 0, 0))

    # Set the alpha channel values based on the mask, using the specified transparency
    alpha.putdata([(0, 0, 0, int(255 * (1 - transparency) * mask_value)) for mask_value in mask.getdata()])

    # Merge the original image and the alpha channel image
    result = Image.alpha_composite(image.convert('RGBA'), alpha)
    result.save("./static/masks/image_alpha.png")
    # Save the result as a PNG file
    return "./static/masks/image_alpha.png"

def generate_image(image_path, mask_path, text, api_key=None):
    if api_key is None:
        raise Exception("Missing Stability API key.")

    engine_id = "stable-diffusion-512-v2-1"
    api_host = os.getenv('API_HOST', 'https://api.stability.ai')

    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/image-to-image/masking",
        headers={
            "Accept": 'application/json',
            "Authorization": f"Bearer {api_key}"
        },
        files={
            'init_image': open(image_path, 'rb'),
            'mask_image': open(mask_path, 'rb'),
        },
        data={
            "mask_source": "MASK_IMAGE_WHITE",
            "text_prompts[0][text]": text,
            "cfg_scale": 20,
            "clip_guidance_preset": "FAST_BLUE",
            "samples": 1,
            "steps": 50,
        }
    )

    print("Recieved response from API: " + str(response.status_code))

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    data = response.json()
    generated_image_paths = []

    for i, image in enumerate(data["artifacts"]):
        # Generate a unique file name using a timestamp
        timestamp = int(time.time() * 1000)
        output_path = f"./static/images/img2img_masking_{i}_{timestamp}.png"

        with open(output_path, "wb") as f:
            f.write(base64.b64decode(image["base64"]))
        generated_image_paths.append(output_path)

    return generated_image_paths
