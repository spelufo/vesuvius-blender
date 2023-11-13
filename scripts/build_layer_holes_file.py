# Run with:
# JZ=22 blender-3.6 -b segmentation_template.blend --python scripts/build_layer_holes_file.py
# It will make a file holes_z{JZ}.blend with that layer's holes, starting from
# segmentation_template.blend. 


import os
import sys
import bpy
import vesuvius.vesuvius

if __name__ == "__main__":
  scan = vesuvius.vesuvius.get_current_scan()
  assert scan, "No scan."
  jz = int(os.environ["JZ"])
  vesuvius.vesuvius.import_layer_holes(bpy.context, scan, jz-1)
  bpy.ops.wm.save_as_mainfile(filepath=f"/mnt/phil/vesuvius/blender/scroll_1_54/holes_z{jz}.blend")
