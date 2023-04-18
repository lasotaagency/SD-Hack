import base64
import os
import requests
from PIL import Image
import numpy as np
import time
from diffusers import DiffusionPipeline
import torch

def add_alpha_channel(image_path, mask_path, transparency=0.5):
    # Open the image and mask
    image = Image.open(image_path)
    mask = Image.open(mask_path).convert('L')
#     mask = ImageOps.invert(mask)# convert to grayscale

    # Create a new RGBA image with the same size as the original image
    alpha = Image.new('RGBA', image.size, (0, 0, 0, 0))

    # Set the alpha channel values based on the mask, using the specified transparency
    alpha.putdata([(0, 0, 0, 255 - int(transparency * mask_value)) for mask_value in mask.getdata()])

    r1, g1, b1 = image.split()
    _, _, _, a2 = alpha.split()
    
    result = Image.merge('RGBA', (r1, g1, b1, a2))

    result.save("./static/masks/image_alpha.png")

    # Save the result as a PNG file
    return "./static/masks/image_alpha.png"

def generate_image(image_path, mask_path, text, api_key=None):
    if api_key is None:
        raise Exception("Missing Stability API key.")

    engine_id = "stable-diffusion-512-v2-1"
    # engine_id = "stable-inpainting-512-v2-0"
    api_host = os.getenv('API_HOST', 'https://api.stability.ai')

    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/image-to-image/masking",
        headers={
            "Accept": 'application/json',
            "Authorization": f"Bearer {api_key}"
        },
        files={
            'init_image': open(image_path, 'rb'),
            # 'mask_image': open(mask_path, 'rb'),
        },
        data={
            "mask_source": "INIT_IMAGE_ALPHA",
            "text_prompts[0][text]": text,
            "cfg_scale": 7,
            "clip_guidance_preset": "FAST_BLUE",
            "samples": 2,
            "steps": 50,
            "style_preset": "enhance",
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

def generate_image_upscale(image_path, api_key=None):
    if api_key is None:
            raise Exception("Missing Stability API key.")

    engine_id = "esrgan-v1-x2plus"
    # engine_id = "stable-inpainting-512-v2-0"
    api_host = os.getenv('API_HOST', 'https://api.stability.ai')

    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/image-to-image/upscale",
        headers={
            "Accept": "image/png",
            "Authorization": f"Bearer {api_key}"
        },
        files={
            "image": open(image_path, "rb")
        }
    )

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    with open(image_path, "wb") as f:
        f.write(response.content)

def paint_by_example(image_path, mask_path, guide_path, num_images_per_prompt=1, filename="./static/images/image_inpaint.png", device="cuda"):
    init_image = Image.open(image_path)
    mask_image = Image.open(mask_path)
    example_image = Image.open(guide_path)
    
    if device == "cuda":
        pipe = DiffusionPipeline.from_pretrained(
        "Fantasy-Studio/Paint-by-Example",
        torch_dtype=torch.float16,
        )

        pipe = pipe.to('cuda')

    else:
        pipe = DiffusionPipeline.from_pretrained(
        "Fantasy-Studio/Paint-by-Example",
        )

    images = pipe(image=init_image, mask_image=mask_image, example_image=example_image, guidance_scale=15, num_images_per_prompt=num_images_per_prompt).images
    generated_image_paths = []

    for i, image in enumerate(images):
        # Generate a unique file name using a timestamp
        timestamp = int(time.time() * 1000)
        output_path = f"./static/images/img2img_example_{i}_{timestamp}.png"

        image.save(output_path)
        generated_image_paths.append(output_path)

    return generated_image_paths
    
    image.save(filename)
    return filename