# Usage:
# for z in $(seq -w 13 20); do
#   JZ=$z blender-3.6 -b segmentation_template.blend --python scripts/build_layer_holes.py
# done

import os
import sys
import bpy
import vesuvius.vesuvius

blender_scroll_dir = "/mnt/phil/vesuvius/blender/scroll_1_54"

if __name__ == "__main__":
  scan = vesuvius.vesuvius.get_current_scan()
  assert scan, "No scan."
  jz = int(os.environ["JZ"])
  vesuvius.vesuvius.import_layer_holes(bpy.context, scan, jz-1)
  bpy.ops.wm.save_as_mainfile(filepath=f"{blender_scroll_dir}/holes/holes_z{jz:02d}.blend")
