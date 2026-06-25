import os
import numpy as np
from PIL import Image

def get_base_mask():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    mask_path = os.path.join(base_dir, "skin-mask.png")
    return np.array(Image.open(mask_path).convert("RGBA"))

def validate_base_layer(skin_img: Image.Image) -> bool:
    """
    Checks if the skin's base layer (head, body, arms, legs) has any transparent pixels.
    Returns True if the base layer is completely opaque (valid), False if it has missing pixels (holes).
    """
    arr_mask = get_base_mask()
    arr_skin = np.array(skin_img.convert("RGBA"))

    if arr_skin.shape[:2] != arr_mask.shape[:2]:
        if arr_skin.shape[:2] == (32, 64): # 64x32 skin
            current_base_mask = arr_mask[:32, :]
        else:
            raise ValueError(f"Unexpected size {skin_img.size}")
    else:
        current_base_mask = arr_mask
        
    # Check if skin has transparent pixels (alpha == 0) where the base mask is present (alpha > 0)
    holes = (current_base_mask[:, :, 3] > 0) & (arr_skin[:, :, 3] == 0)
    return not bool(holes.any())
