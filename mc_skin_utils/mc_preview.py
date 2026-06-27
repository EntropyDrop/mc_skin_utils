#!/usr/bin/env python3
"""
Minecraft Skin 3D Interactive Preview Tool
A command-line tool to preview Minecraft skins interactively in 3D using PyVista.

Usage:
    mc_preview <skin_image_path>
"""

import sys
import argparse
from PIL import Image
from .ensure_skin64x64 import convert_skin_64x32_to_64x64
from .mc_voxel_texture_resolver import resolve_voxel_consistency
from .mc_render import render_skin

def main():
    parser = argparse.ArgumentParser(description="Minecraft Skin 3D Interactive Preview")
    parser.add_argument("skin_path", help="Path to the Minecraft skin PNG image")
    parser.add_argument("--bg", type=float, nargs=3, default=[240/255, 240/255, 240/255], help="Background RGB color from 0.0 to 1.0")
    parser.add_argument("--no-light", action="store_true", help="Disable realistic lighting (render flat/unlit)")
    parser.add_argument("--flat", action="store_true", help="Render secondary layer as flat planes instead of 3D voxels")
    parser.add_argument("--wireframe", action="store_true", help="Show wireframe edges")
    parser.add_argument("--output-size", type=int, nargs=2, default=[800, 800], help="Preview window size (width height)")
    
    # Optional rotations
    parser.add_argument("--rot-head", type=float, nargs=3, default=[0, 0, 0], help="Head rotation (pitch yaw roll)")
    parser.add_argument("--rot-arm-right", type=float, nargs=3, default=[0, 0, 0], help="Right arm rotation")
    parser.add_argument("--rot-arm-left", type=float, nargs=3, default=[0, 0, 0], help="Left arm rotation")
    parser.add_argument("--rot-leg-right", type=float, nargs=3, default=[0, 0, 0], help="Right leg rotation")
    parser.add_argument("--rot-leg-left", type=float, nargs=3, default=[0, 0, 0], help="Left leg rotation")

    args = parser.parse_args()

    try:
        # Load and convert skin
        skin_img = Image.open(args.skin_path).convert("RGBA")
        skin_img = convert_skin_64x32_to_64x64(skin_img)
        skin_img = resolve_voxel_consistency(skin_img)
    except Exception as e:
        print(f"Error loading skin image: {e}", file=sys.stderr)
        sys.exit(1)

    rot_args = {
        'rot_head': tuple(args.rot_head),
        'rot_arm_right': tuple(args.rot_arm_right),
        'rot_arm_left': tuple(args.rot_arm_left),
        'rot_leg_right': tuple(args.rot_leg_right),
        'rot_leg_left': tuple(args.rot_leg_left),
    }

    print(f"Opening interactive 3D preview for: {args.skin_path}")
    print("Close the window or press Q to exit.")

    # Render skin in interactive mode (off_screen = False)
    render_skin(
        skin_img,
        output_size=tuple(args.output_size),
        use_voxels=not args.flat,
        rot_args=rot_args,
        bg=args.bg,
        light=not args.no_light,
        show_wireframe=args.wireframe,
        off_screen=False
    )

if __name__ == "__main__":
    main()
