import os
import numpy as np
from PIL import Image

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    skins_dir = os.path.join(base_dir, "skins")
    mask_path = os.path.join(base_dir, "skin-mask.png")
    decor_mask_path = os.path.join(base_dir, "skin-decor-mask.png")

    if not os.path.exists(skins_dir):
        print(f"Directory {skins_dir} does not exist.")
        return

    # Load masks
    try:
        mask1 = Image.open(mask_path).convert("RGBA")
        mask2 = Image.open(decor_mask_path).convert("RGBA")
    except Exception as e:
        print(f"Error loading masks: {e}")
        return

    # Convert to numpy arrays
    arr_mask1 = np.array(mask1)
    arr_mask2 = np.array(mask2)
    
    # Combined valid mask where either alpha is > 0
    # mask alpha channel is index 3
    valid_mask = (arr_mask1[:, :, 3] > 0) | (arr_mask2[:, :, 3] > 0)

    # Process skins
    processed_count = 0
    cleaned_count = 0
    
    for filename in os.listdir(skins_dir):
        if not filename.lower().endswith(".png"):
            continue
            
        filepath = os.path.join(skins_dir, filename)
        try:
            skin = Image.open(filepath).convert("RGBA")
            arr_skin = np.array(skin)
            
            # Match dimensions
            if arr_skin.shape[:2] != valid_mask.shape:
                if arr_skin.shape[:2] == (32, 64): # 64x32 skin (height 32, width 64)
                    current_valid_mask = valid_mask[:32, :]
                else:
                    print(f"Skipping {filename}: unexpected size {skin.size}")
                    continue
            else:
                current_valid_mask = valid_mask

            # Find extra pixels: skin alpha > 0 but not in valid mask
            extra_pixels = (arr_skin[:, :, 3] > 0) & (~current_valid_mask)
            
            if extra_pixels.any():
                print(f"Found extra pixels in {filename}. Cleaning...")
                # Set extra pixels to transparent
                arr_skin[extra_pixels] = [0, 0, 0, 0]
                
                # Save the cleaned skin, overwrite original
                cleaned_skin = Image.fromarray(arr_skin, "RGBA")
                cleaned_skin.save(filepath)
                cleaned_count += 1
            
            processed_count += 1
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print(f"\nDone! Processed {processed_count} skins. Cleaned extra pixels in {cleaned_count} skins.")

if __name__ == "__main__":
    main()
