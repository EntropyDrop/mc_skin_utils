# mc_skin_utils

A collection of utilities for Minecraft skin processing, cleaning, conversion, and 3D rendering.

## Installation

You can install this package locally or directly from the source.

```bash
pip install -e .
```

Once installed, it provides several global CLI tools for Minecraft skin manipulation.

---

## Command Line Tools

### 1. mc-render
Renders a Minecraft skin in 3D using PyVista. You can use it to preview skins interactively or save them as screenshots, complete with lighting, voxel-based secondary layers, and custom poses.

**Basic Usage:**
```bash
# Render a skin interactively in a window
mc-render skin.png --interact --light
```

**Save to File:**
```bash
# Save a 600x600 screenshot to output.png
mc-render skin.png --save output.png --output-size 600 600
```

**Advanced Usage:**
You can pose the character by defining rotations for the limbs and head.
```bash
# Render with custom rotations for head and arms, and enable lighting
mc-render skin.png \
  --rot-head 10 -20 0 \
  --rot-arm-left 0 0 -45 \
  --rot-arm-right 0 0 45 \
  --interact --light
```

**Options:**
- `--interact`: Open an interactive GUI window instead of rendering off-screen.
- `--save <path>`: Save a screenshot to the specified file.
- `--flat`: Render the secondary (overlay) layer as flat planes instead of voxels.
- `--light`: Enable realistic lighting (otherwise unlit flat shading).
- `--wireframe`: Show wireframe edges on the skin geometry.
- `--rot-head`, `--rot-arm-left`, `--rot-leg-right`, etc.: Set rotation angles (pitch, yaw, roll).
- `--cam-front`: Set camera direction (e.g., `0.5 0.5 0.5`).

---

### 2. clean-skins
Automatically cleans up artifact "extra" pixels on skin images (e.g. pixels that are drawn completely outside of the standard skin layout map). It processes all `.png` files found in a `skins` folder relative to the script.

**Usage:**
```bash
# Runs the cleaning process on the `skins` folder
clean-skins
```

*Note: You must have `skins/` folder and the mask images (`skin-mask.png`, `skin-decor-mask.png`) correctly set up for this command to process the images.*

---

### 3. ensure-skin64x64
Minecraft supports two skin formats: the legacy `64x32` format (where arms and legs are mirrored) and the modern `64x64` format (which supports independent textures for left and right limbs). 

This tool takes a legacy `64x32` skin and safely converts it to the modern `64x64` format by correctly duplicating and mirroring the limb textures.

**Usage:**
```bash
# Converts the skin and saves it as <name>_64x64.png by default
ensure-skin64x64 legacy_skin.png

# Specify a custom output path
ensure-skin64x64 legacy_skin.png -o modern_skin.png
```

---

## Development

If you'd like to build the project as a `.whl` or `.tar.gz` for PyPI distribution:
```bash
pip install build
python -m build
```
