import os
import sys
import argparse
from PIL import Image

def copy_mirrored_limb(img, new_img, src_x, src_y, dst_x, dst_y):
    """
    Mirror a 16x16 limb block from source (src_x, src_y) to destination (dst_x, dst_y).
    """
    # Top face
    top = img.crop((src_x + 4, src_y, src_x + 8, src_y + 4))
    new_img.paste(top.transpose(Image.FLIP_LEFT_RIGHT), (dst_x + 4, dst_y))
    
    # Bottom face
    bottom = img.crop((src_x + 8, src_y, src_x + 12, src_y + 4))
    new_img.paste(bottom.transpose(Image.FLIP_LEFT_RIGHT), (dst_x + 8, dst_y))
    
    # Front face
    front = img.crop((src_x + 4, src_y + 4, src_x + 8, src_y + 16))
    new_img.paste(front.transpose(Image.FLIP_LEFT_RIGHT), (dst_x + 4, dst_y + 4))
    
    # Back face
    back = img.crop((src_x + 12, src_y + 4, src_x + 16, src_y + 16))
    new_img.paste(back.transpose(Image.FLIP_LEFT_RIGHT), (dst_x + 12, dst_y + 4))
    
    # Right (Outer) face -> Left (Outer) face
    right_face = img.crop((src_x, src_y + 4, src_x + 4, src_y + 16))
    new_img.paste(right_face.transpose(Image.FLIP_LEFT_RIGHT), (dst_x + 8, dst_y + 4))
    
    # Left (Inner) face -> Right (Inner) face
    left_face = img.crop((src_x + 8, src_y + 4, src_x + 12, src_y + 16))
    new_img.paste(left_face.transpose(Image.FLIP_LEFT_RIGHT), (dst_x, dst_y + 4))

def convert_skin_64x32_to_64x64(img: Image.Image) -> Image.Image:
    """
    Converts a legacy 64x32 Minecraft skin to the modern 64x64 format.
    If the image is already 64x64, it returns a copy.
    """
    img = img.convert("RGBA")
    
    # Verify dimensions
    if img.size == (64, 64):
        return img.copy()
        
    if img.size != (64, 32):
        raise ValueError(f"Unsupported skin dimensions: {img.size}. Expected 64x32 legacy skin.")
        
    # Create empty 64x64 transparent canvas
    new_img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    
    # Paste old skin onto the top 32 pixels of the new canvas
    new_img.paste(img, (0, 0))
    
    # Mirror Right Leg (0, 16) to Left Leg (16, 48)
    copy_mirrored_limb(img, new_img, src_x=0, src_y=16, dst_x=16, dst_y=48)
    
    # Mirror Right Arm (40, 16) to Left Arm (32, 48)
    copy_mirrored_limb(img, new_img, src_x=40, src_y=16, dst_x=32, dst_y=48)
    
    return new_img

def main():
    parser = argparse.ArgumentParser(description="Convert legacy 64x32 Minecraft skins to modern 64x64 format.")
    parser.add_argument("input_skin", help="Path to the legacy 64x32 Minecraft skin image.")
    parser.add_argument("-o", "--output", help="Output path for the converted skin. Defaults to input_name_64x64.png.")
    args = parser.parse_args()

    if not os.path.exists(args.input_skin):
        print(f"Error: Input file '{args.input_skin}' does not exist.")
        sys.exit(1)

    output_path = args.output
    if not output_path:
        base, ext = os.path.splitext(args.input_skin)
        output_path = f"{base}_64x64{ext or '.png'}"

    try:
        print(f"[*] Loading skin: {args.input_skin}")
        img = Image.open(args.input_skin)
        
        if img.size == (64, 64):
            print(f"[*] Skin '{args.input_skin}' is already 64x64. No conversion needed.")
            if args.input_skin != output_path:
                img.save(output_path)
                print(f"[+] Saved copy to: {output_path}")
        else:
            print("[*] Converting legacy 64x32 skin to modern 64x64 format...")
            new_img = convert_skin_64x32_to_64x64(img)
            new_img.save(output_path)
            print(f"[+] Converted successfully. Modern 64x64 skin saved to: {output_path}")
    except Exception as e:
        print(f"[!] Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
