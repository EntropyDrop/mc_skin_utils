#!/usr/bin/env python3
"""
Minecraft Skin 3D Renderer (PyVista Version)
A tool to render Minecraft skins in 3D using PyVista.

Usage:
    python mc_render.py <skin_image_path>
    
Example:
    python mc_render.py skin.png
"""

import argparse
import numpy as np
from PIL import Image
import pyvista as pv
from .mc_voxel_texture_resolver import resolve_voxel_consistency


def get_uv_face(skin: np.ndarray, u: int, v: int, w: int, h: int, flip_h: bool = False, flip_v: bool = False) -> np.ndarray:
    """Extract a face texture from the skin."""
    # Slicing in numpy is [row, col] -> [y, x]
    face = skin[v:v+h, u:u+w].copy()
    if flip_h:
        face = np.fliplr(face)
    if flip_v:
        face = np.flipud(face)
    return face

def create_textured_box(
    position: tuple,
    size: tuple,
    uv_coords: dict,
    skin: np.ndarray,
    tex_size: tuple = None
) -> pv.PolyData:
    x, y, z = position
    w, h, d = size
    hw, hh, hd = w/2, h/2, d/2
    
    if tex_size is None:
        tex_w, tex_h, tex_d = int(w), int(h), int(d)
    else:
        tex_w, tex_h, tex_d = int(tex_size[0]), int(tex_size[1]), int(tex_size[2])

    faces_list = []

    # Helper function: construct a single face
    def build_face(name, p_width, p_height, res_x, res_y):
        if name not in uv_coords:
            return None
            
        uv_data = uv_coords[name]
        u, v = uv_data[0], uv_data[1]
        flip_h = not(uv_data[2] if len(uv_data) > 2 else False)
        flip_v = not(uv_data[3] if len(uv_data) > 3 else False)
        
        # 1. Extract texture
        face_tex = get_uv_face(skin, u, v, res_x, res_y, flip_h, flip_v)
        
        # 2. Critical fix: PyVista's Plane builds grids (cells) from bottom-left by default,
        # whereas image data starts from top-left. Image data must be flipped vertically to match UV.
        face_tex = np.flipud(face_tex)

        # 3. Special fix: The back face will be horizontally mirrored after 3D rotation of 180 degrees,
        # so it needs to be flipped horizontally beforehand on the texture data.
        if name == 'back' or name =='front':
            face_tex = np.fliplr(face_tex)
            
        # 4. Create base plane (default in XY plane, center at 0,0,0, normal +Z)
        plane = pv.Plane(center=(0,0,0), direction=(0,0,1), 
                         i_size=p_width, j_size=p_height,
                         i_resolution=res_x, j_resolution=res_y)
        
        # 5. Assign colors
        colors = face_tex.reshape(-1, 4)
        plane.cell_data["RGBA"] = colors.astype(np.uint8)
        
        # Filter out transparent cells (alpha < 10) to avoid occlusion/depth-writing issues
        non_transparent_indices = np.where(colors[:, 3] >= 10)[0]
        if len(non_transparent_indices) == 0:
            return None
        plane = plane.extract_cells(non_transparent_indices)
        
        # 6. Move and rotate the plane to the correct position
        # Note: rotate operation modifies points in place
        if name == 'front': # +Z
            plane.translate((0, 0, hd), inplace=True)
            
        elif name == 'back': # -Z (Rotate 180 degrees to face back)
            plane.rotate_y(180, inplace=True)
            plane.translate((0, 0, -hd), inplace=True)
            
        elif name == 'left': # +X (Rotate right 90 degrees from Front)
            plane.rotate_y(-90, inplace=True)
            plane.translate((hw, 0, 0), inplace=True)
            
        elif name == 'right': # -X (Rotate left 90 degrees from Front)
            plane.rotate_y(90, inplace=True)
            plane.translate((-hw, 0, 0), inplace=True)
            
        elif name == 'top': # +Y (Rotate up 90 degrees from Front)
            plane.rotate_x(-90, inplace=True)
            plane.translate((0, hh, 0), inplace=True)
            
        elif name == 'bottom': # -Y (Rotate down 90 degrees from Front)
            plane.rotate_x(90, inplace=True)
            plane.translate((0, -hh, 0), inplace=True)

        # 7. Apply overall offset (move to the center position of the body part)
        plane.translate((x, y, z), inplace=True)
        
        return plane

    # Define each face (width, height, texture width, texture height)
    # Front (res: w * h)
    p = build_face('front', w, h, tex_w, tex_h)
    if p: faces_list.append(p)
    
    # Back (res: w * h)
    p = build_face('back', w, h, tex_w, tex_h)
    if p: faces_list.append(p)

    # Right (res: d * h) - side width is d
    p = build_face('right', d, h, tex_d, tex_h)
    if p: faces_list.append(p)

    # Left (res: d * h)
    p = build_face('left', d, h, tex_d, tex_h)
    if p: faces_list.append(p)
    
    # Top (res: w * d) - top face height is d
    p = build_face('top', w, d, tex_w, tex_d)
    if p: faces_list.append(p)

    # Bottom (res: w * d)
    p = build_face('bottom', w, d, tex_w, tex_d)
    if p: faces_list.append(p)

    if not faces_list:
        return None

    # Merge all faces into one Mesh
    mesh = faces_list[0]
    for i in range(1, len(faces_list)):
        mesh = mesh.merge(faces_list[i])
        
    return mesh

def create_voxel_box(
    position: tuple,
    size: tuple,
    uv_coords: dict,
    skin: np.ndarray,
    tex_size: tuple = None,
    hl: bool = False,
    hl_direction: tuple = (0,0,-1),
    hl_depth: int = 3,
) -> pv.PolyData:
    """
    Create a voxelized box. 
    Optimization: Create a PointCloud of centers and Glyph a single Cube.
    """
    x, y, z = position
    w, h, d = size
    hw, hh, hd = w/2, h/2, d/2
    
    if tex_size is None:
        tex_w, tex_h, tex_d = int(w), int(h), int(d)
    else:
        tex_w, tex_h, tex_d = int(tex_size[0]), int(tex_size[1]), int(tex_size[2])

    vx = w / tex_w
    vy = h / tex_h
    vz = d / tex_d

    voxel_centers = []
    voxel_colors = []
    voxel_centers_hl = []
    voxel_colors_hl = []

    faces = [
        ('front', tex_w, tex_h), ('back', tex_w, tex_h),
        ('right', tex_d, tex_h), ('left', tex_d, tex_h),
        ('top', tex_w, tex_d),   ('bottom', tex_w, tex_d),
    ]

    # Map to dedup voxels at corners
    # Key: (ix, iy, iz), Value: list of colors
    voxel_map = {}
    voxel_map_hl = {}

    exists = {}
    face_textures = {}
    for face_name, face_tw, face_th in faces:
        if face_name not in uv_coords:
            continue
        
        uv_data = uv_coords[face_name]
        u, v = uv_data[0], uv_data[1]
        flip_h = uv_data[2] if len(uv_data) > 2 else False
        flip_v = uv_data[3] if len(uv_data) > 3 else False

        if face_name == 'top':
            flip_h = False
            flip_v = True
        if face_name == 'bottom':
            flip_h = False
            flip_v = False
        
        face_tex = get_uv_face(skin, u, v, face_tw, face_th, flip_h, flip_v)
        face_textures[face_name] = face_tex

        for py in range(face_th):
            for px in range(face_tw):
                alpha = face_tex[py, px, 3]
                if alpha < 10: # Threshold for transparency
                    continue
                
                # Coordinate mapping
                ix, iy, iz = 0, 0, 0
                if face_name == 'front':
                    ix, iy, iz = px, py, tex_d - 1
                elif face_name == 'back':
                    ix, iy, iz = (tex_w - 1) - px, py, 0
                elif face_name == 'right':
                    ix, iy, iz = 0, py, px
                elif face_name == 'left':
                    ix, iy, iz = tex_w - 1, py, (tex_d - 1) - px
                elif face_name == 'top':
                    ix, iy, iz = px, tex_h - 1, (tex_d - 1) - py
                elif face_name == 'bottom':
                    ix, iy, iz = px, 0, py
                key = (ix, iy, iz)
                exists[key] = True
    for face_name, face_tw, face_th in faces:
        if face_name not in uv_coords:
            continue
        
        face_tex = face_textures[face_name]

        for py in range(face_th):
            for px in range(face_tw):
                alpha = face_tex[py, px, 3]
                if alpha < 10: # Threshold for transparency
                    continue
                
                color = face_tex[py, px, :] # RGBA
                
                # Coordinate mapping
                ix, iy, iz = 0, 0, 0
                if face_name == 'front':
                    ix, iy, iz = px, py, tex_d - 1
                elif face_name == 'back':
                    ix, iy, iz = (tex_w - 1) - px, py, 0
                elif face_name == 'right':
                    ix, iy, iz = 0, py, px
                elif face_name == 'left':
                    ix, iy, iz = tex_w - 1, py, (tex_d - 1) - px
                elif face_name == 'top':
                    ix, iy, iz = px, tex_h - 1, (tex_d - 1) - py
                elif face_name == 'bottom':
                    ix, iy, iz = px, 0, py
                
                hl_filter = ix
                key = (ix, iy, iz)
                if hl:
                    direction = 1
                    if hl_direction == (1,0,0) or hl_direction == (-1,0,0):
                        hl_filter = ix
                        direction = hl_direction[0]
                    elif hl_direction == (0,1,0) or hl_direction == (0,-1,0):
                        hl_filter = iy
                        direction = hl_direction[1]
                    elif hl_direction == (0,0,1) or hl_direction == (0,0,-1):
                        hl_filter = iz
                        direction = hl_direction[2]
                    if direction == 1:
                        if hl_filter < hl_depth:
                            continue
                    else:
                        if hl_filter > hl_depth:
                            continue
                    prev = tuple(np.array((ix, iy, iz))-np.array(hl_direction))
                    # Ignore voxels occluded by the core
                    if prev[0] >0 and prev[0] < tex_w-1 and prev[1] >0 and prev[1] < tex_h-1 and prev[2] > 0 and prev[2] < tex_d-1:
                        continue
                    # Ignore occluded voxels
                    if hl_filter == hl_depth and prev in exists:
                        continue

                    if hl_filter == hl_depth:
                        if key not in voxel_map_hl:
                            voxel_map_hl[key] = {}
                        voxel_map_hl[key][face_name] = color
                        continue
                    else:
                        color = [0,0,0,20]
                if key not in voxel_map:
                    voxel_map[key] = {}
                voxel_map[key][face_name] = color

    if not voxel_map and not voxel_map_hl:
        return None

    for (ix, iy, iz), face_dict in voxel_map_hl.items():
        # Get fallback color from available faces
        all_colors = list(face_dict.values())
        any_color = all_colors[0] if all_colors else [0,0,0,0]
        
        # Calculate world position # Grid origin is (x-hw, y-hh, z-hd)
        cx = (x - hw) + (ix + 0.5) * vx
        cy = (y - hh) + (iy + 0.5) * vy
        cz = (z - hd) + (iz + 0.5) * vz
        
        voxel_centers_hl.append([cx, cy, cz])
        voxel_colors_hl.append(any_color)

    face_planes = {
        'front':  pv.Plane(center=(0,0,vz/2), direction=(0,0,1), i_size=vx, j_size=vy, i_resolution=1, j_resolution=1),
        'back':   pv.Plane(center=(0,0,-vz/2), direction=(0,0,-1), i_size=vx, j_size=vy, i_resolution=1, j_resolution=1),
        'left':   pv.Plane(center=(vx/2,0,0), direction=(1,0,0), i_size=vz, j_size=vy, i_resolution=1, j_resolution=1),
        'right':  pv.Plane(center=(-vx/2,0,0), direction=(-1,0,0), i_size=vz, j_size=vy, i_resolution=1, j_resolution=1),
        'top':    pv.Plane(center=(0,vy/2,0), direction=(0,1,0), i_size=vx, j_size=vz, i_resolution=1, j_resolution=1),
        'bottom': pv.Plane(center=(0,-vy/2,0), direction=(0,-1,0), i_size=vx, j_size=vz, i_resolution=1, j_resolution=1),
    }

    face_centers_map = {f: [] for f in face_planes.keys()}
    face_colors_map = {f: [] for f in face_planes.keys()}

    for (ix, iy, iz), face_dict in voxel_map.items():
        # Any available color to use as fallback if face is missing
        all_colors = list(face_dict.values())
        any_color = all_colors[0] if all_colors else [0,0,0,0]
        
        # Calculate world position # Grid origin is (x-hw, y-hh, z-hd)
        cx = (x - hw) + (ix + 0.5) * vx
        cy = (y - hh) + (iy + 0.5) * vy
        cz = (z - hd) + (iz + 0.5) * vz
        
        for f in face_planes.keys():
            color = face_dict.get(f, any_color)
            face_centers_map[f].append([cx, cy, cz])
            face_colors_map[f].append(color)

    mesh = None
    for f in face_planes.keys():
        if not face_centers_map[f]:
            continue
        cloud = pv.PolyData(np.array(face_centers_map[f]))
        cloud.point_data["RGBA"] = np.array(face_colors_map[f]).astype(np.uint8)
        f_mesh = cloud.glyph(geom=face_planes[f], scale=False, orient=False)
        if mesh is None:
            mesh = f_mesh
        else:
            mesh = mesh.merge(f_mesh, merge_points=False)

    if hl and voxel_centers_hl:
        cloud_hl = pv.PolyData(np.array(voxel_centers_hl))
        cloud_hl.point_data["RGBA"] = np.array(voxel_colors_hl).astype(np.uint8)
        if hl_direction == (0,1,0) or hl_direction == (0,-1,0):
            plane = pv.Plane(center=(0,0,0), direction=(0,1,0), 
                             i_size=vx, j_size=vz,
                             i_resolution=1, j_resolution=1)
        elif hl_direction == (1,0,0) or hl_direction == (-1,0,0):
            plane = pv.Plane(center=(0,0,0), direction=(1,0,0), 
                             i_size=vx, j_size=vz,
                             i_resolution=1, j_resolution=1)
        elif hl_direction == (0,0,1) or hl_direction == (0,0,-1):
            plane = pv.Plane(center=(0,0,0), direction=(0,0,1), 
                             i_size=vx, j_size=vz,
                             i_resolution=1, j_resolution=1)
        mesh_hl = cloud_hl.glyph(geom=plane, scale=False, orient=False)
        return mesh_hl.merge(mesh, merge_points=False) if mesh is not None else mesh_hl
    
    return mesh

def build_minecraft_model(
    skin: np.ndarray, 
    core_display: list = [],
    decor_display: list = [],
    hl: bool = False,
    hl_direction: tuple = (0,0,-1),
    hl_depth: int = 3,
    use_voxels: bool = True,
    rot_head: tuple = (0, 0, 0),
    rot_arm_right: tuple = (0, 0, 0),
    rot_arm_left: tuple = (0, 0, 0),
    rot_leg_right: tuple = (0, 0, 0),
    rot_leg_left: tuple = (0, 0, 0),
    pos_args: dict = None
) -> list:
    """Build the model components."""
    scale = 1.0
    limbs_offset = 0.0

    is_slim = skin[52, 47, 3] == 0

    default_positions = {
        'head': (0, 28 * scale, 0),
        'body': (0, 18 * scale, 0),
        'right_arm': (-6 * scale - limbs_offset, 18 * scale - 1, 0),
        'left_arm': (6 * scale + limbs_offset, 18 * scale - 1, 0),
        'right_leg': (-2 * scale - limbs_offset, 6 * scale, 0),
        'left_leg': (2 * scale + limbs_offset, 6 * scale, 0),
    }

    pos_args = pos_args or {}
    positions = {part: pos_args.get(part, def_pos) for part, def_pos in default_positions.items()}

    pivots = {
        'head': (0, 24 * scale, 0),
        'right_arm': (-6 * scale, 24 * scale, 0),
        'left_arm': (6 * scale, 24 * scale, 0),
        'right_leg': (-2 * scale, 12 * scale, 0),
        'left_leg': (2 * scale, 12 * scale, 0),
    }

    # Adjust pivots based on position override
    for part in pivots:
        if part in pos_args:
            offset = np.array(pos_args[part]) - np.array(default_positions[part])
            pivots[part] = tuple(np.array(pivots[part]) + offset)

    def apply_rotation(mesh, angles, pivot):
        if not angles or all(a == 0 for a in angles):
            return
        
        # PyVista rotations are simple. 
        # Translate to origin relative to pivot -> Rotate -> Translate back
        px, py, pz = pivot
        mesh.translate((-px, -py, -pz), inplace=True)
        
        # Order: x (pitch), y (yaw), z (roll)
        if angles[0] != 0: mesh.rotate_x(angles[0], inplace=True)
        if angles[1] != 0: mesh.rotate_y(angles[1], inplace=True)
        if angles[2] != 0: mesh.rotate_z(angles[2], inplace=True)
        
        mesh.translate((px, py, pz), inplace=True)

    uv_flip = {
        'front': (False, True), 'back': (False, True),
        'right': (False, True), 'left': (False, True),
        'top': (True, True),   'bottom': (True, False),
    }

    # --- Head ---
    head_uv = {
        'front': (8, 8, *uv_flip['front']), 'back': (24, 8, *uv_flip['back']),
        'right': (0, 8, *uv_flip['right']), 'left': (16, 8, *uv_flip['left']),
        'top': (8, 0, *uv_flip['top']),     'bottom': (16, 0, *uv_flip['bottom']),
    }
    head_mesh = create_textured_box(positions['head'], (8 * scale, 8 * scale, 8 * scale), head_uv, skin)
    if head_mesh:
        apply_rotation(head_mesh, rot_head, pivots['head'])

    # --- Hat ---
    overlay_offset = 0.5 * scale
    hat_uv = {
        'front': (40, 8, *uv_flip['front']), 'back': (56, 8, *uv_flip['back']),
        'right': (32, 8, *uv_flip['right']), 'left': (48, 8, *uv_flip['left']),
        'top': (40, 0, *uv_flip['top']), 'bottom': (48, 0, *uv_flip['bottom']),
    }
    hat_args = {
        'position': positions['head'],
        'size': (8 * scale + overlay_offset * 2, 8 * scale + overlay_offset * 2, 8 * scale + overlay_offset * 2),
        'uv_coords': hat_uv, 'skin': skin, 'tex_size': (8, 8, 8)
    }
    hat_mesh = create_voxel_box(hl = hl and "head" in decor_display, hl_direction = hl_direction, hl_depth = hl_depth,**hat_args) if use_voxels else create_textured_box(**hat_args)
    if hat_mesh:
        apply_rotation(hat_mesh, rot_head, pivots['head'])

    # --- Body ---
    body_uv = {
        'front': (20, 20, *uv_flip['front']), 'back': (32-(1 if is_slim else 0), 20, *uv_flip['back']),
        'right': (16, 20, *uv_flip['right']), 'left': (28-(1 if is_slim else 0), 20, *uv_flip['left']),
        'top': (20, 16, *uv_flip['top']),     'bottom': (28-(1 if is_slim else 0), 16, *uv_flip['bottom']),
    }
    body_mesh = create_textured_box(positions['body'], (8 * scale, 12 * scale, 4 * scale), body_uv, skin)

    # --- Arms & Legs ---
    
    # Right Arm
    r_arm_uv = {
        'front': (44, 20, *uv_flip['front']), 'back': (52-(1 if is_slim else 0), 20, *uv_flip['back']),
        'right': (40, 20, *uv_flip['right']), 'left': (48-(1 if is_slim else 0), 20, *uv_flip['left']),
        'top': (44, 16, *uv_flip['top']),     'bottom': (48-(1 if is_slim else 0), 16, *uv_flip['bottom']),
    }
    r_arm_mesh = create_textured_box(positions['right_arm'], ((3 if is_slim else 4)*scale, 12*scale, 4*scale), r_arm_uv, skin)
    if r_arm_mesh:
        apply_rotation(r_arm_mesh, rot_arm_right, pivots['right_arm'])

    # Left Arm
    l_arm_uv = {
        'front': (36, 52, *uv_flip['front']), 'back': (44-(1 if is_slim else 0), 52, *uv_flip['back']),
        'right': (32, 52, *uv_flip['right']), 'left': (40-(1 if is_slim else 0), 52, *uv_flip['left']),
        'top': (36, 48, *uv_flip['top']),     'bottom': (40-(1 if is_slim else 0), 48, *uv_flip['bottom']),
    }
    l_arm_mesh = create_textured_box(positions['left_arm'], ((3 if is_slim else 4)*scale, 12*scale, 4*scale), l_arm_uv, skin)
    if l_arm_mesh:
        apply_rotation(l_arm_mesh, rot_arm_left, pivots['left_arm'])

    # Right Leg
    r_leg_uv = {
        'front': (4, 20, *uv_flip['front']), 'back': (12, 20, *uv_flip['back']),
        'right': (0, 20, *uv_flip['right']), 'left': (8, 20, *uv_flip['left']),
        'top': (4, 16, *uv_flip['top']),     'bottom': (8, 16, *uv_flip['bottom']),
    }
    r_leg_mesh = create_textured_box(positions['right_leg'], (4*scale, 12*scale, 4*scale), r_leg_uv, skin)
    if r_leg_mesh:
        apply_rotation(r_leg_mesh, rot_leg_right, pivots['right_leg'])

    # Left Leg
    l_leg_uv = {
        'front': (20, 52, *uv_flip['front']), 'back': (28, 52, *uv_flip['back']),
        'right': (16, 52, *uv_flip['right']), 'left': (24, 52, *uv_flip['left']),
        'top': (20, 48, *uv_flip['top']),     'bottom': (24, 48, *uv_flip['bottom']),
    }
    l_leg_mesh = create_textured_box(positions['left_leg'], (4*scale, 12*scale, 4*scale), l_leg_uv, skin)
    if l_leg_mesh:
        apply_rotation(l_leg_mesh, rot_leg_left, pivots['left_leg'])


    # --- Overlays ---
    decor_offset = 0.5
    
    # Jacket
    jacket_uv = {
        'front': (20, 36, *uv_flip['front']), 'back': (32, 36, *uv_flip['back']),
        'right': (16, 36, *uv_flip['right']), 'left': (28, 36, *uv_flip['left']),
        'top': (20, 32, *uv_flip['top']),   'bottom': (28, 32, *uv_flip['bottom']),
    }
    jacket_args = {
        'position': positions['body'],
        'size': (8*scale+decor_offset, 12*scale+decor_offset, 4*scale+decor_offset),
        'uv_coords': jacket_uv, 'skin': skin, 'tex_size': (8, 12, 4)
    }
    jacket_mesh = create_voxel_box(hl = hl and "body" in decor_display, hl_direction = hl_direction, hl_depth = hl_depth,**jacket_args) if use_voxels else create_textured_box(**jacket_args)

    # Sleeves & Pants (Similar logic to Arms/Legs)
    # Right Sleeve
    rs_uv = {'front':(44,36,*uv_flip['front']),'back':(52-(1 if is_slim else 0),36,*uv_flip['back']),'right':(40,36,*uv_flip['right']),'left':(48-(1 if is_slim else 0),36,*uv_flip['left']),'top':(44,32,*uv_flip['top']),'bottom':(48-(1 if is_slim else 0),32,*uv_flip['bottom'])}
    rs_args = {'position':positions['right_arm'],'size':((3 if is_slim else 4)*scale+decor_offset,12*scale+decor_offset,4*scale+decor_offset),'uv_coords':rs_uv,'skin':skin,'tex_size':((3 if is_slim else 4),12,4)}
    rs_mesh = create_voxel_box(hl = hl and "right_arm" in decor_display, hl_direction = hl_direction, hl_depth = hl_depth,**rs_args) if use_voxels else create_textured_box(**rs_args)
    if rs_mesh: apply_rotation(rs_mesh, rot_arm_right, pivots['right_arm']);

    # Left Sleeve
    ls_uv = {'front':(52,52,*uv_flip['front']),'back':(60-(1 if is_slim else 0),52,*uv_flip['back']),'right':(48,52,*uv_flip['right']),'left':(56-(1 if is_slim else 0),52,*uv_flip['left']),'top':(52,48,*uv_flip['top']),'bottom':(56-(1 if is_slim else 0),48,*uv_flip['bottom'])}
    ls_args = {'position':positions['left_arm'],'size':((3 if is_slim else 4)*scale+decor_offset,12*scale+decor_offset,4*scale+decor_offset),'uv_coords':ls_uv,'skin':skin,'tex_size':((3 if is_slim else 4),12,4)}
    ls_mesh = create_voxel_box(hl = hl and "left_arm" in decor_display, hl_direction = hl_direction, hl_depth = hl_depth,**ls_args) if use_voxels else create_textured_box(**ls_args)
    if ls_mesh: apply_rotation(ls_mesh, rot_arm_left, pivots['left_arm']);

    # Right Pants
    rp_uv = {'front':(4,36,*uv_flip['front']),'back':(12,36,*uv_flip['back']),'right':(0,36,*uv_flip['right']),'left':(8,36,*uv_flip['left']),'top':(4,32,*uv_flip['top']),'bottom':(8,32,False,True)}
    rp_args = {'position':positions['right_leg'],'size':(4*scale+decor_offset,12*scale+decor_offset,4*scale+decor_offset),'uv_coords':rp_uv,'skin':skin,'tex_size':(4,12,4)}
    rp_mesh = create_voxel_box(hl = hl and "right_leg" in decor_display, hl_direction = hl_direction, hl_depth = hl_depth,**rp_args) if use_voxels else create_textured_box(**rp_args)
    if rp_mesh: apply_rotation(rp_mesh, rot_leg_right, pivots['right_leg']);

    # Left Pants
    lp_uv = {'front':(4,52,*uv_flip['front']),'back':(12,52,*uv_flip['back']),'right':(0,52,*uv_flip['right']),'left':(8,52,*uv_flip['left']),'top':(4,48,*uv_flip['top']),'bottom':(8,48,*uv_flip['bottom'])}
    lp_args = {'position':positions['left_leg'],'size':(4*scale+decor_offset,12*scale+decor_offset,4*scale+decor_offset),'uv_coords':lp_uv,'skin':skin,'tex_size':(4,12,4)}
    lp_mesh = create_voxel_box(hl = hl and "left_leg" in decor_display, hl_direction = hl_direction, hl_depth = hl_depth,**lp_args) if use_voxels else create_textured_box(**lp_args)
    if lp_mesh: apply_rotation(lp_mesh, rot_leg_left, pivots['left_leg']); 

    return head_mesh, body_mesh, l_arm_mesh,r_arm_mesh,  l_leg_mesh,r_leg_mesh,  hat_mesh, jacket_mesh, ls_mesh, rs_mesh, lp_mesh, rp_mesh

def render_skin(
    skin: Image.Image, 
    output_size: tuple=(300,300),
    cam_front: tuple = (0.5, 0.5, 0.5),
    use_voxels: bool = True, 
    ortho: bool = False,
    rot_args: dict = None,
    pos_args: dict = None,
    save_path: str = None,
    bg: list = [1, 1, 1],
    light = False,
    core_display = ["head","body","right_arm","left_arm","right_leg","left_leg"],
    decor_display = ["head","body","right_arm","left_arm","right_leg","left_leg"],
    zoom = 0.25,
    look_at_y = 12,
    light_pos: tuple = (0, 30, 30),
    light_intensity: float = 0.5,
    core_opacity: float = 1.0,
    decore_opacity: float = 1.0,
    transparent_background: bool = False,
    hl: bool = False,
    hl_direction: tuple = (0, 1, 0),
    hl_depth: int = 0,
    show_wireframe: bool = False,
    off_screen: bool = True,
):
    skin_arr = np.array(skin.convert("RGBA"))
    if rot_args is None: rot_args = {}
    
    # Build models
    head, body, l_arm, r_arm, l_leg, r_leg, hat, jacket, ls, rs, lp, rp = build_minecraft_model(skin_arr, hl=hl,hl_direction=hl_direction,hl_depth=hl_depth, core_display=core_display, decor_display=decor_display, use_voxels=use_voxels, pos_args=pos_args, **rot_args)
    
    # Initialize Plotter
    plotter = pv.Plotter(off_screen=off_screen, window_size=output_size)
    plotter.background_color = bg
    
    mesh_kwargs = {
        "scalars": "RGBA", "rgb": True, "show_scalar_bar": False, 
        "smooth_shading": False, "lighting": light, 
        "show_edges": show_wireframe
    }
    if show_wireframe:
        mesh_kwargs["edge_color"] = "black"

    if "head" in core_display:
        plotter.add_mesh(head, opacity=core_opacity, **mesh_kwargs)
    if "head" in decor_display and hat:
        plotter.add_mesh(hat, opacity=decore_opacity, **mesh_kwargs)
    if "body" in core_display:
        plotter.add_mesh(body, opacity=core_opacity, **mesh_kwargs)
    if "body" in decor_display and jacket:
        plotter.add_mesh(jacket, opacity=decore_opacity, **mesh_kwargs)
    if "right_arm" in core_display:
        plotter.add_mesh(r_arm, opacity=core_opacity, **mesh_kwargs)
    if "right_arm" in decor_display and rs:
        plotter.add_mesh(rs, opacity=decore_opacity, **mesh_kwargs)
    if "left_arm" in core_display:
        plotter.add_mesh(l_arm, opacity=core_opacity, **mesh_kwargs)
    if "left_arm" in decor_display and ls:
        plotter.add_mesh(ls, opacity=decore_opacity, **mesh_kwargs)
    if "right_leg" in core_display:
        plotter.add_mesh(r_leg, opacity=core_opacity, **mesh_kwargs)
    if "right_leg" in decor_display and rp:
        plotter.add_mesh(rp, opacity=decore_opacity, **mesh_kwargs)
    if "left_leg" in core_display:
        plotter.add_mesh(l_leg, opacity=core_opacity, **mesh_kwargs)
    if "left_leg" in decor_display and lp:
        plotter.add_mesh(lp, opacity=decore_opacity, **mesh_kwargs)
        
    # Camera setup
    plotter.camera.position = (cam_front[0] * 70, cam_front[1] * 70 + 20, cam_front[2] * 70)
    plotter.camera.focal_point = (0, look_at_y, 0)
    plotter.camera.up = (0, 1, 0)
    plotter.camera.zoom(.14/zoom)
    
    if ortho:
        plotter.enable_parallel_projection()
    
    if light:
        # --- Interactive Light Setup ---
        # Mutable state for the light (use list so closures can modify)
        light_state = {
            'pos': list(light_pos),
            'intensity': light_intensity,
            'step': 5.0,          # position step per keypress
            'int_step': 0.05,     # intensity step per keypress
        }

        key_light = pv.Light(
            position=light_state['pos'],
            focal_point=(0, 12, 0),
            intensity=light_state['intensity'],
            color='white'
        )
        plotter.add_light(key_light)
        plotter.add_light(pv.Light(
            position=(-light_state['pos'][0], -light_state['pos'][1], -light_state['pos'][2]),
            focal_point=(0, 12, 0),
            intensity=light_state['intensity'],
            color='white'
        )
)

        interact = not off_screen
        if interact:
            # HUD text actor to display light info
            hud_text = f"Light: pos=({light_state['pos'][0]:.0f}, {light_state['pos'][1]:.0f}, {light_state['pos'][2]:.0f})  intensity={light_state['intensity']:.2f}"
            text_actor = plotter.add_text(
                hud_text, position='lower_left', font_size=9,
                color='yellow', name='light_hud'
            )

        def _update_light_hud():
            """Refresh the HUD text and re-render."""
            pos = light_state['pos']
            key_light.position = tuple(pos)
            key_light.intensity = light_state['intensity']
            new_text = f"Light: pos=({pos[0]:.0f}, {pos[1]:.0f}, {pos[2]:.0f})  intensity={light_state['intensity']:.2f}"
            plotter.add_text(
                new_text, position='lower_left', font_size=9,
                color='yellow', name='light_hud'
            )
            plotter.render()

        # --- Key bindings ---
        # W/S : move light in Z (forward / backward)
        def _light_forward():
            light_state['pos'][2] += light_state['step']
            _update_light_hud()
        def _light_backward():
            light_state['pos'][2] -= light_state['step']
            _update_light_hud()

        # A/D : move light in X (left / right)
        def _light_left():
            light_state['pos'][0] -= light_state['step']
            _update_light_hud()
        def _light_right():
            light_state['pos'][0] += light_state['step']
            _update_light_hud()

        # Q/E : move light in Y (up / down)
        def _light_up():
            light_state['pos'][1] += light_state['step']
            _update_light_hud()
        def _light_down():
            light_state['pos'][1] -= light_state['step']
            _update_light_hud()

        # R/F : increase / decrease intensity
        def _light_brighter():
            light_state['intensity'] = min(5.0, light_state['intensity'] + light_state['int_step'])
            _update_light_hud()
        def _light_dimmer():
            light_state['intensity'] = max(0.0, light_state['intensity'] - light_state['int_step'])
            _update_light_hud()

        # P : print current state to console
        def _light_print():
            pos = light_state['pos']
            print(f"[Light] position=({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}), intensity={light_state['intensity']:.2f}")

        if interact:
            plotter.add_key_event('w', _light_forward)
            plotter.add_key_event('s', _light_backward)
            plotter.add_key_event('a', _light_left)
            plotter.add_key_event('d', _light_right)
            plotter.add_key_event('q', _light_up)
            plotter.add_key_event('e', _light_down)
            plotter.add_key_event('r', _light_brighter)
            plotter.add_key_event('f', _light_dimmer)
            plotter.add_key_event('p', _light_print)
            

    else:
        # Flat lighting for pure texture look
        plotter.disable_anti_aliasing()
    
    if save_path:
        plotter.screenshot(save_path, transparent_background=transparent_background)
        plotter.close()
        plotter.deep_clean()
        import gc; gc.collect()
        return None
    else:
        # If off_screen, return the image data
        if off_screen:
            img = plotter.screenshot(None, transparent_background=transparent_background)
            plotter.close()
            plotter.deep_clean()
            import gc; gc.collect()
            return img
        plotter.show(title="Minecraft Skin Renderer (PyVista)")
        return None

def main():
    parser = argparse.ArgumentParser(description="Minecraft Skin 3D Renderer (PyVista)")
    parser.add_argument("skin_path", help="Path to the Minecraft skin image")
    parser.add_argument("--cam-front", type=float, nargs=3, default=[0.5, 0.5, 0.5], help="Camera front direction (x y z)")
    parser.add_argument("--flat", action="store_true", help="Render second layer as flat planes instead of voxels")
    parser.add_argument("--light", action="store_true", help="Enable lighting (default is flat/unlit)")
    parser.add_argument("--ortho", action="store_true", help="Use orthographic projection")
    parser.add_argument("--wireframe", action="store_true", help="Overlay wireframe on the texture")
    parser.add_argument("--output-size", type=int, nargs=2, default=[600, 600], help="Output size (width height)")
    
    parser.add_argument("--rot-head", type=float, nargs=3, default=[0, 0, 0], help="Head rotation (pitch yaw roll)")
    parser.add_argument("--rot-arm-right", type=float, nargs=3, default=[0, 0, 0], help="Right arm rotation")
    parser.add_argument("--rot-arm-left", type=float, nargs=3, default=[0, 0, 0], help="Left arm rotation")
    parser.add_argument("--rot-leg-right", type=float, nargs=3, default=[0, 0, 0], help="Right leg rotation")
    parser.add_argument("--rot-leg-left", type=float, nargs=3, default=[0, 0, 0], help="Left leg rotation")
    
    parser.add_argument("--pos-head", type=float, nargs=3, help="Head position")
    parser.add_argument("--pos-body", type=float, nargs=3, help="Body position")
    parser.add_argument("--pos-arm-right", type=float, nargs=3, help="Right arm position")
    parser.add_argument("--pos-arm-left", type=float, nargs=3, help="Left arm position")
    parser.add_argument("--pos-leg-right", type=float, nargs=3, help="Right leg position")
    parser.add_argument("--pos-leg-left", type=float, nargs=3, help="Left leg position")
    
    parser.add_argument("--save", type=str, help="Save screenshot to file")
    parser.add_argument("--bg", type=float, nargs=3, default=[1/255, 254/255, 1/255], help="Background color (r g b)")
    parser.add_argument("--light-pos", type=float, nargs=3, default=[0, 30, 30], help="Initial light position (x y z)")
    parser.add_argument("--light-intensity", type=float, default=0.5, help="Initial light intensity")
    parser.add_argument("--interact", action="store_true", help="Interactive mode (opens GUI window)")

    args = parser.parse_args()
    
    rot_args = {
        'rot_head': tuple(args.rot_head),
        'rot_arm_right': tuple(args.rot_arm_right),
        'rot_arm_left': tuple(args.rot_arm_left),
        'rot_leg_right': tuple(args.rot_leg_right),
        'rot_leg_left': tuple(args.rot_leg_left),
    }
    
    pos_args = {}
    if args.pos_head: pos_args['head'] = tuple(args.pos_head)
    if args.pos_body: pos_args['body'] = tuple(args.pos_body)
    if args.pos_arm_right: pos_args['right_arm'] = tuple(args.pos_arm_right)
    if args.pos_arm_left: pos_args['left_arm'] = tuple(args.pos_arm_left)
    if args.pos_leg_right: pos_args['right_leg'] = tuple(args.pos_leg_right)
    if args.pos_leg_left: pos_args['left_leg'] = tuple(args.pos_leg_left)
    
    from .ensure_skin64x64 import convert_skin_64x32_to_64x64
    
    skin_img = Image.open(args.skin_path).convert("RGBA")
    skin_img = convert_skin_64x32_to_64x64(skin_img)
    skin_img = resolve_voxel_consistency(skin_img)

    render_skin(
        skin_img, 
        cam_front=args.cam_front, 
        output_size=args.output_size, 
        use_voxels=not args.flat, 
        ortho=args.ortho, 
        rot_args=rot_args, 
        pos_args=pos_args, 
        save_path=args.save, 
        bg=args.bg, 
        light=args.light,
        light_pos=tuple(args.light_pos),
        light_intensity=args.light_intensity,
        show_wireframe=args.wireframe,
        off_screen=not args.interact
    )

if __name__ == "__main__":
    main()