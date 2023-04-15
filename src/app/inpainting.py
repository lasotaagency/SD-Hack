import base64
import os
import requests

def generate_image(image_path, mask_path, text, api_key=None):
    if api_key is None:
        raise Exception("Missing Stability API key.")

    engine_id = "stable-inpainting-512-v2-0"
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
            "cfg_scale": 7,
            "clip_guidance_preset": "FAST_BLUE",
            "samples": 1,
            "steps": 30,
        }
    )

    print("Recieved response from API: " + str(response.status_code))

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    data = response.json()
    generated_image_paths = []

    for i, image in enumerate(data["artifacts"]):
        output_path = f"./static/diffusion_outputs/img2img_masking_{i}.png"
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(image["base64"]))
        generated_image_paths.append(output_path)

    return generated_image_paths
