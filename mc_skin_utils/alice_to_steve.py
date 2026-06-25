from PIL import Image

def alice_to_steve(alice):
    for arm_loc, decor_offset in [((40, 16), (0,16)), ((32,48),(16,0))]:
        for (size, loc, offset_x) in [
            # Top and bottom
            ((5,4),(arm_loc[0]+4+1, arm_loc[1]), 1),# Duplicate the middle pixel once
            ((2,4),(arm_loc[0]+4+4+1, arm_loc[1]), 1),

            # Front and back
            ((9,12),(arm_loc[0]+4+1, arm_loc[1]+4), 1),
            ((2,12),(arm_loc[0]+4+4+4+1, arm_loc[1]+4), 1),
        ]:
            for x in range(loc[0]+size[0]-1, loc[0]-1, -1):
                for y in range(loc[1], loc[1]+size[1]):
                    alice.putpixel((x+offset_x, y), alice.getpixel((x, y)))
                    alice.putpixel((x+offset_x+decor_offset[0], y+decor_offset[1]), alice.getpixel((x+decor_offset[0], y+decor_offset[1])))
    return alice