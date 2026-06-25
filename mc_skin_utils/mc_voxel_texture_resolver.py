from PIL import Image, ImageChops
import numpy as np

# Compensate when decor texture is missing. When any two faces are inconsistent, follow the priority order: front, back, left, right, top, bottom

def resolve_voxel_consistency(img):
    is_slim = img.getpixel((47,52))[3] == 0
    print('is_slim', is_slim)
    for part_idx, part in enumerate([
            # head
            [
                [
                    [(8,8,8),(8,8)],#front
                    [(8,8,8),(24,8)],#back
                    [(8,8,8),(16,8)],#left
                    [(8,8,8),(0,8)],#right
                    [(8,8,8),(8,0)],#top
                    [(8,8,8),(16,0)],#bottom
                ],(32,0)
            ],

            #body
            [
                [
                    [(8,12,4),(20,20)],#front
                    [(8,12,4),(20+12,20)],#back
                    [(4,12,8),(28,20)],#left
                    [(4,12,8),(16,20)],#right
                    [(8,4,12),(20,16)],#top
                    [(8,4,12),(20+8,16)],#bottom
                ],(0,16)
            ],

            #left arm
            [
                [
                    [((3 if is_slim else 4),12,4),(32+4,52)],#front
                    [((3 if is_slim else 4),12,4),(32+12-(1 if is_slim else 0),52)],#back
                    [(4,12,4),(32+8-(1 if is_slim else 0),52)],#left
                    [(4,12,4),(32,52)],#right
                    [((3 if is_slim else 4),4,12),(32+4,48)],#top
                    [((3 if is_slim else 4),4,12),(32+8-(1 if is_slim else 0),48)],#bottom
                ],(16,0)
            ],

            #right arm
            [
                [
                    [((3 if is_slim else 4),12,4),(40+4,20)],#front
                    [((3 if is_slim else 4),12,4),(40+12-(1 if is_slim else 0),20)],#back
                    [(4,12,4),(40+8-(1 if is_slim else 0),20)],#left
                    [(4,12,4),(40,20)],#right
                    [((3 if is_slim else 4),4,12),(40+4,16)],#top
                    [((3 if is_slim else 4),4,12),(40+8-(1 if is_slim else 0),16)],#bottom
                ],(0,16)
            ],

            #left leg
            [
                [
                    [(4,12,4),(16+4,52)],#front
                    [(4,12,4),(16+12,52)],#back
                    [(4,12,4),(16+8,52)],#left
                    [(4,12,4),(16,52)],#right
                    [(4,4,12),(16+4,48)],#top
                    [(4,4,12),(16+8,48)],#bottom
                ],(-16,0)
            ],

            #right leg
            [
                [
                    [(4,12,4),(0+4,20)],#front
                    [(4,12,4),(0+12,20)],#back
                    [(4,12,4),(0+8,20)],#left
                    [(4,12,4),(0,20)],#right
                    [(4,4,12),(0+4,16)],#top
                    [(4,4,12),(0+8,16)],#bottom
                ],(0,16)
            ],
        ]):
        decor_offset = part[1]
        (x,y,z) = part[0][4][0]
        # map x,y,z -> colors
        # map x,y,z -> colors
        #colors = np.full((x, y, z, 4), -1)
        colors = np.zeros((x, y, z, 4))
        priorities = np.full((x, y, z), 99)

        # Initialize decor layer voxels
        # map x,y,z -> img x,y arr
        inverse = {}
        for idx,(size, offset) in enumerate(part[0]):
            for dx in range(size[0]):
                for dy in range(size[1]):
                    img_x = offset[0]+dx+decor_offset[0]
                    img_y = offset[1]+dy+decor_offset[1]
                    c = img.getpixel((img_x, img_y))
                    new_x = None
                    new_y = None
                    new_z = None
                    if idx == 4: # top
                        new_x, new_y, new_z = (dx, y-1-dy, z-1)
                    elif idx == 5: # bottom
                        new_x, new_y, new_z = (dx, y-1-dy, 0)
                    elif idx == 0: # front
                        new_x, new_y, new_z = (dx, 0, z-1-dy)
                    elif idx == 1: # back
                        new_x, new_y, new_z = (x-1-dx, y-1, z-1-dy)
                    elif idx == 2: # left
                        new_x, new_y, new_z = (x-1, dx, z-1-dy)
                    elif idx == 3: # right
                        new_x, new_y, new_z = (0, y-1-dx, z-1-dy)
                    if (new_x,new_y,new_z) not in inverse:
                        inverse[(new_x,new_y,new_z)] = []
                    inverse[(new_x,new_y,new_z)].append((img_x,img_y))

                    if c[3] == 0:
                        continue
                    
                    prio = 99
                    if idx == 0: prio = 0 # front
                    elif idx == 1: prio = 1 # back
                    elif idx == 4: prio = 2 # top
                    elif idx == 5: prio = 3 # bottom
                    elif idx == 2: prio = 4 # left
                    elif idx == 3: prio = 5 # right

                    if priorities[new_x, new_y, new_z] > prio:
                        colors[new_x, new_y, new_z] = c
                        priorities[new_x, new_y, new_z] = prio

        for dx in range(size[0]):
            for dy in range(size[1]):
                for dz in range(size[2]):
                    if (dx,dy,dz) in inverse:
                        if priorities[dx, dy, dz] == 99:
                            continue
                        for i in inverse[(dx,dy,dz)]:
                            existing_c = img.getpixel(i)
                            if existing_c[3] == 0:
                                img.putpixel(i, tuple(colors[dx,dy,dz].astype(int)))
    return img

def highlight_diff(img1_path, img2_path, output_path):
    # 1. Open and ensure consistent mode (usually RGB)
    img1 = Image.open(img1_path).convert('RGBA')
    img2 = Image.open(img2_path).convert('RGBA')

    arr1 = np.array(img1)
    arr2 = np.array(img2)

    # 4. Create an all-zero array to store results (fully transparent)
    height, width, _ = arr1.shape
    result_arr = np.zeros((height, width, 4), dtype=np.uint8)

    # 5. Calculate difference mask
    # This step is key. We compare if arr1 and arr2 are not equal.
    # The resulting diff_mask is a boolean array,
    # where True means at least one of the four RGBA values at the corresponding position is different.
    diff_mask = np.any(arr1 != arr2, axis=-1)

    # 6. Set result pixels
    # Where differences exist (diff_mask is True),
    # set the pixels in the result array to pure red: (R=255, G=0, B=0, A=255)
    result_arr[diff_mask] = [255, 0, 0, 255]
    
    # 7. Where pixels match (~diff_mask is True),
    # maintain the state when created in step 4: (0, 0, 0, 0) which is fully transparent.
    # No extra operation is needed here since result_arr is initialized to all zeros.

    # 8. Convert the NumPy array back to Pillow Image
    result_img = Image.fromarray(result_arr, mode='RGBA')

    # 9. Save result
    result_img.save(output_path)
