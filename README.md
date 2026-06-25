# mc_skin_utils

A collection of utilities for Minecraft skin processing and 3D rendering.

## Installation

```bash
pip install -e .
```

## Tools

### mc-render
Renders a Minecraft skin in 3D using PyVista.

```bash
mc-render skin.png --light
```

### clean-skins
Cleans up extra pixels on skins in a `skins` folder based on valid masks.

```bash
clean-skins
```
