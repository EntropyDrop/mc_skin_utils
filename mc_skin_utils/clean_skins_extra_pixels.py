import os
import numpy as np
from PIL import Image

def get_masks():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    mask_path = os.path.join(base_dir, "skin-mask.png")
    decor_mask_path = os.path.join(base_dir, "skin-decor-mask.png")
    mask1 = Image.open(mask_path).convert("RGBA")
    mask2 = Image.open(decor_mask_path).convert("RGBA")
    return np.array(mask1), np.array(mask2)

def clean_skin(skin_img: Image.Image) -> Image.Image:
    """
    Takes a PIL Image of a Minecraft skin and removes any 'extra' pixels 
    that fall outside the standard skin UV mapping.
    """
    arr_mask1, arr_mask2 = get_masks()
    valid_mask = (arr_mask1[:, :, 3] > 0) | (arr_mask2[:, :, 3] > 0)
    arr_skin = np.array(skin_img.convert("RGBA"))

    if arr_skin.shape[:2] != valid_mask.shape:
        if arr_skin.shape[:2] == (32, 64): # 64x32 skin
            current_valid_mask = valid_mask[:32, :]
        else:
            raise ValueError(f"Unexpected size {skin_img.size}")
    else:
        current_valid_mask = valid_mask
        
    extra_pixels = (arr_skin[:, :, 3] > 0) & (~current_valid_mask)
    if extra_pixels.any():
        arr_skin[extra_pixels] = [0, 0, 0, 0]
        
    return Image.fromarray(arr_skin, "RGBA")


def main(skins_dir=None):
    if skins_dir is None:
        skins_dir = os.path.join(os.getcwd(), "skins")

    if not os.path.exists(skins_dir):
        print(f"Directory {skins_dir} does not exist.")
        return

    processed_count = 0
    cleaned_count = 0
    
    for filename in os.listdir(skins_dir):
        if not filename.lower().endswith(".png"):
            continue
            
        filepath = os.path.join(skins_dir, filename)
        try:
            skin = Image.open(filepath)
            
            # Simple check to see if we changed anything
            arr_before = np.array(skin.convert("RGBA"))
            
            cleaned = clean_skin(skin)
            arr_after = np.array(cleaned)
            
            if np.any(arr_before != arr_after):
                print(f"Found extra pixels in {filename}. Cleaning...")
                cleaned.save(filepath)
                cleaned_count += 1
            
            processed_count += 1
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print(f"\nDone! Processed {processed_count} skins. Cleaned extra pixels in {cleaned_count} skins.")

if __name__ == "__main__":
    main()
