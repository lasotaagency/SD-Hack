from segment_anything import sam_model_registry, SamPredictor
import numpy as np
import cv2
from config import sam_checkpoint, model_type, device
from PIL import Image
import torch
import os

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

def save_image_mask(mask, filename):
    """
    Save an image mask to a JPG or PNG file.

    :param mask: A 2D numpy array (image mask) containing boolean values
    :param filename: The output file path, including the extension (.jpg or .png)
    """

    # Convert the numpy array to a Pillow Image object
    mask_image = Image.fromarray(mask)
    # Save the image to a file
    mask_image.save(filename)

def get_SAM_mask(predictor, image_path, input_point, filename="static/masks/custom_mask.png"):
    image = cv2.imread(image_path)
    predictor.set_image(image)
    input_label = np.array([1])

    masks, scores, logits = predictor.predict(
    point_coords=input_point,
    point_labels=input_label,
    multimask_output=True,
    )

    bestmask = masks[np.argmax(scores)]

    save_image_mask(bestmask, filename)
    return filename

def startup_sam():
    sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
    sam.to(device=device)

    predictor = SamPredictor(sam)
    return predictor

def get_lang_sam_mask(model, image_path, text_prompt):
    image_pil = Image.open(image_path)
    masks, boxes, phrases, logits = model.predict(image_pil, text_prompt)

    if len(logits) > 0:
        # Initialize an empty mask with the same dimensions as the input masks
        aggregated_mask = np.zeros_like(masks[0].numpy(), dtype=bool)
        # Iterate over logits and masks, and update the aggregated_mask using a position-wise OR operation when logits >= 0.5
        for logit, mask in zip(logits, masks):
            if logit >= 0.5:
                aggregated_mask = np.logical_or(aggregated_mask, mask.numpy())

        # Calculate the number of masks with logits >= 0.5
        count = torch.sum(logits >= 0.5).item()
        print(f"Found {count} masks for {text_prompt}")

        if count > 0:
            filename = f"static/masks/{text_prompt}_mask.png"
            save_image_mask(aggregated_mask, filename)
            return text_prompt, filename, boxes[0].detach().cpu().tolist()

    return None, None, None