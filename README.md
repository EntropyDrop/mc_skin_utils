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

### 1. mc_skin_utils mc_render
Renders a Minecraft skin in 3D using PyVista. You can use it to preview skins interactively or save them as screenshots, complete with lighting, voxel-based secondary layers, and custom poses.

**Basic Usage:**
```bash
# Render a skin interactively in a window
mc_skin_utils mc_render skin.png --interact --light
```

**Save to File:**
```bash
# Save a 600x600 screenshot to output.png
mc_skin_utils mc_render skin.png --save output.png --output-size 600 600
```

**Advanced Usage:**
You can pose the character by defining rotations for the limbs and head.
```bash
# Render with custom rotations for head and arms, and enable lighting
mc_skin_utils mc_render skin.png \
  --rot-head 10 -20 0 \
  --rot-arm-left 0 0 -45 \
  --rot-arm-right 0 0 45 \
  --interact --light
```

**Options:**

*General & Output:*
- `skin_path` (positional): Path to the Minecraft skin image.
- `--interact`: Open an interactive GUI window instead of rendering off-screen.
- `--save <path>`: Save a screenshot to the specified file.
- `--output-size <width> <height>`: Set output image dimensions (default: `600 600`).
- `--bg <r> <g> <b>`: Set background color as RGB values from 0.0 to 1.0 (default: `0.0039 0.996 0.0039` / green).

*Rendering Styles:*
- `--flat`: Render the secondary (overlay/armor) layer as flat planes instead of full 3D voxels.
- `--ortho`: Use orthographic camera projection instead of perspective.
- `--wireframe`: Show wireframe black edges on the skin geometry.
- `--light`: Enable realistic lighting. If not set, rendering uses unlit flat texture shading.

*Lighting Configuration (Requires `--light`):*
- `--light-pos <x> <y> <z>`: Initial light position (default: `0 30 30`).
- `--light-intensity <float>`: Initial light intensity (default: `0.5`).

*Camera:*
- `--cam-front <x> <y> <z>`: Set the camera's front direction vector (default: `0.5 0.5 0.5`).

*Posing (Rotations & Positions):*
- `--rot-head <pitch> <yaw> <roll>`: Rotate the head (degrees).
- `--rot-arm-left <pitch> <yaw> <roll>`: Rotate the left arm.
- `--rot-arm-right <pitch> <yaw> <roll>`: Rotate the right arm.
- `--rot-leg-left <pitch> <yaw> <roll>`: Rotate the left leg.
- `--rot-leg-right <pitch> <yaw> <roll>`: Rotate the right leg.
- `--pos-head <x> <y> <z>`: Override head position.
- `--pos-body <x> <y> <z>`: Override body position.
- `--pos-arm-left <x> <y> <z>`: Override left arm position.
- `--pos-arm-right <x> <y> <z>`: Override right arm position.
- `--pos-leg-left <x> <y> <z>`: Override left leg position.
- `--pos-leg-right <x> <y> <z>`: Override right leg position.

---

### 2. mc_skin_utils clean_skins
Automatically cleans up artifact "extra" pixels on skin images (e.g. pixels that are drawn completely outside of the standard skin layout map). It processes all `.png` files found in a `skins` folder relative to the script.

**Usage:**
```bash
# Runs the cleaning process on the `skins` folder
mc_skin_utils clean_skins
```

*Note: You must have `skins/` folder and the mask images (`skin-mask.png`, `skin-decor-mask.png`) correctly set up for this command to process the images.*

---

### 3. mc_skin_utils ensure_skin64x64
Minecraft supports two skin formats: the legacy `64x32` format (where arms and legs are mirrored) and the modern `64x64` format (which supports independent textures for left and right limbs). 

This tool takes a legacy `64x32` skin and safely converts it to the modern `64x64` format by correctly duplicating and mirroring the limb textures.

**Usage:**
```bash
# Converts the skin and saves it as <name>_64x64.png by default
mc_skin_utils ensure_skin64x64 legacy_skin.png

# Specify a custom output path
mc_skin_utils ensure_skin64x64 legacy_skin.png -o modern_skin.png
```

---

## Development

If you'd like to build the project as a `.whl` or `.tar.gz` for PyPI distribution:
```bash
pip install build
python -m build
```

## Python API Usage

You can also import and use the core functions directly in your own Python projects.

### Rendering Skins in Python
```python
from PIL import Image
from mc_skin_utils.mc_render import render_skin
from mc_skin_utils.ensure_skin64x64 import convert_skin_64x32_to_64x64

# 1. Load the skin as a PIL Image 
skin_img = Image.open("path/to/skin.png").convert("RGBA")

# (Optional) Convert 64x32 to 64x64 if necessary
skin_img = convert_skin_64x32_to_64x64(skin_img)

# 2. Render and save the skin without opening a GUI
render_skin(
    skin_img,
    save_path="output.png",
    output_size=(800, 800),
    light=True,
    off_screen=True,
    transparent_background=True,
    cam_front=(0.5, 0.5, 0.5),
    rot_args={
        "rot_head": (10, -20, 0),
        "rot_arm_right": (0, 0, 45),
        "rot_arm_left": (0, 0, -45)
    }
)
```

### Converting Legacy Skins in Python
```python
from PIL import Image
from mc_skin_utils.ensure_skin64x64 import convert_skin_64x32_to_64x64

skin_img = Image.open("legacy_skin.png")
# Converts a legacy 64x32 skin to modern 64x64 format
modern_skin = convert_skin_64x32_to_64x64(skin_img)
modern_skin.save("modern_skin.png")
```

### Converting Slim (Alice) Skins to Classic (Steve) Skins
```python
from PIL import Image
from mc_skin_utils.alice_to_steve import alice_to_steve

# Load a slim (3-pixel arm) skin
skin_img = Image.open("slim_skin.png").convert("RGBA")

# Convert to classic (4-pixel arm) skin in-place (modifies the PIL Image)
classic_skin_img = alice_to_steve(skin_img)
classic_skin_img.save("classic_skin.png")
```

### Resolving Voxel Consistency
When skin decor textures are missing on certain faces, this function infers and fills them in using adjacent faces to ensure the 3D voxel representation has no holes.

```python
from PIL import Image
from mc_skin_utils.mc_voxel_texture_resolver import resolve_voxel_consistency

skin_img = Image.open("skin.png").convert("RGBA")
resolved_img = resolve_voxel_consistency(skin_img)
resolved_img.save("resolved_skin.png")
```


### Cleaning Extra Artifact Pixels
Remove invalid or "extra" pixels from a skin that lie outside the standard Minecraft UV layout.

```python
from PIL import Image
from mc_skin_utils.clean_skins_extra_pixels import clean_skin

skin_img = Image.open("messy_skin.png")
cleaned_skin_img = clean_skin(skin_img)
cleaned_skin_img.save("cleaned_skin.png")
```

### Detecting Skin Model (Steve vs Alex)
You can detect if a skin uses the classic Steve model (4-pixel arms) or the slim Alex model (3-pixel arms).

```python
from PIL import Image
from mc_skin_utils.validator import is_alex

skin_img = Image.open("skin.png")
is_slim = is_alex(skin_img)

if is_slim:
    print("This is an Alex (slim) skin.")
else:
    print("This is a Steve (classic) skin.")
```

### Validating Skin Base Layer Opacity
Check if the base layer (head, body, arms, legs) of a skin has any missing (transparent) pixels. Minecraft requires the base layer to be completely opaque.

By default, the validation will automatically detect the model type (Steve vs Alex). You can also explicitly pass `is_alex` if you already know the model type.

```python
from PIL import Image
from mc_skin_utils.validator import validate_base_layer

skin_img = Image.open("skin.png")

# Auto-detect model type during validation
is_valid = validate_base_layer(skin_img)

# Or explicitly pass the model type
is_valid_explicit = validate_base_layer(skin_img, is_alex=True)

if not is_valid:
    print("Warning: The skin has transparent holes in its base layer!")
```

