from segment_anything import sam_model_registry, SamPredictor
import numpy as np
import cv2
from config import sam_checkpoint, model_type, device
from PIL import Image

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
        if np.max(logits.numpy()) > 0.5:
            bestmask = masks[np.argmax(logits)].numpy()

            filename = f"static/masks/{text_prompt}_mask.png"
            save_image_mask(bestmask, filename)
            return text_prompt, filename 
    return None, None