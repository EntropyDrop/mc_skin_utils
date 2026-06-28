import os
import numpy as np
from PIL import Image

def get_base_mask():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    mask_path = os.path.join(base_dir, "skin-mask.png")
    return np.array(Image.open(mask_path).convert("RGBA"))

def is_alex(skin_img: Image.Image) -> bool:
    """
    Detects if the Minecraft skin is an Alex (slim, 3-pixel arms) model.
    Alex skins are characterized by having a transparent pixel at (47, 52)
    in the left arm area, which is opaque in the Steve model.
    """
    if skin_img.size == (64, 32):
        return False  # Legacy 64x32 skins are always Steve (4-pixel arms)
    
    if skin_img.size != (64, 64):
        return False  # Non-standard sizes default to False
        
    arr = np.array(skin_img.convert("RGBA"))
    try:
        # Check alpha channel of Left Arm pixel at col=47, row=52 (y=52, x=47)
        return bool(arr[52, 47, 3] == 0)
    except IndexError:
        return False

_detect_is_alex = is_alex

def validate_base_layer(skin_img: Image.Image, is_alex: bool = None) -> bool:
    """
    Checks if the skin's base layer (head, body, arms, legs) has any transparent pixels.
    Returns True if the base layer is completely opaque (valid), False if it has missing pixels (holes).
    Automatically adjusts validation boundaries if it detects or is told it is an Alex (slim) model.
    """
    arr_mask = get_base_mask()
    arr_skin = np.array(skin_img.convert("RGBA"))

    if arr_skin.shape[:2] != arr_mask.shape[:2]:
        if arr_skin.shape[:2] == (32, 64): # 64x32 skin
            current_base_mask = arr_mask[:32, :].copy()
        else:
            raise ValueError(f"Unexpected size {skin_img.size}")
    else:
        current_base_mask = arr_mask.copy()
        
    # Determine whether to use Alex model adjustment
    use_alex = is_alex if is_alex is not None else _detect_is_alex(skin_img)

    # If it is Alex (slim) model, adjust mask for 3-pixel arms
    if use_alex:
        # Adjust Right Arm (v: 16..31, u: 40..55)
        # Clear unused/transparent pixels in slim model arm layout
        current_base_mask[16:32, 47] = 0
        current_base_mask[16:20, 50] = 0
        current_base_mask[16:20, 51] = 0
        current_base_mask[20:32, 51] = 0
        current_base_mask[20:32, 54] = 0
        current_base_mask[20:32, 55] = 0
        
        # Adjust Left Arm (v: 48..63, u: 32..47)
        current_base_mask[48:64, 39] = 0
        current_base_mask[48:52, 42] = 0
        current_base_mask[48:52, 43] = 0
        current_base_mask[52:64, 43] = 0
        current_base_mask[52:64, 46] = 0
        current_base_mask[52:64, 47] = 0

    # Check if skin has transparent pixels (alpha == 0) where the base mask is present (alpha > 0)
    holes = (current_base_mask[:, :, 3] > 0) & (arr_skin[:, :, 3] == 0)
    return not bool(holes.any())

