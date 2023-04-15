from segment_anything import sam_model_registry, SamPredictor
import numpy as np
import cv2
from config import sam_checkpoint, model_type, device
from PIL import Image

def save_image_mask(mask, filename):
    """
    Save an image mask to a JPG or PNG file.

    :param mask: A 2D numpy array (image mask) containing integer values
    :param filename: The output file path, including the extension (.jpg or .png)
    """

    # Convert the numpy array to a Pillow Image object
    mask_image = Image.fromarray(mask)
    # Save the image to a file
    mask_image.save(filename)

def get_mask(predictor, image_path, input_point, filename="static/masks/mask.png"):
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