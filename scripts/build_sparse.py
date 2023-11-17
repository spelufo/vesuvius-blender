# This one is even quick-and-dirtier than the others. The goal was to extract the
# biggest holes from each layer into a separate file to then aggregate together
# into a single labeling.blend file, which I did. The idea being that I wanted
# to start with the biggest patches for labeling. I used patches_histogram.py to
# determine the threshold for the number of vertices used when filtering such
# that I got the N biggest first. TODO: Clean it up by mergine patches_histogram
# into this, if possible.

import gc, time, json, os
import bpy
import vesuvius.utils

blender_scroll_dir = "/mnt/phil/vesuvius/blender/scroll_1_54"

def delete_small_objects():
  bpy.ops.object.select_all(action='DESELECT')
  for obj in bpy.data.objects:
    # Batch 1 (100 biggest):
    # if len(obj.data.vertices) < 105*100:
    #   obj.select_set(True)
    # Batch 2 (100 more):
    # if len(obj.data.vertices) < 83*100 or len(obj.data.vertices) >= 105*100:
    #   obj.select_set(True)
    # Batch 3 (300 more):
    if len(obj.data.vertices) < 62*100 or len(obj.data.vertices) >= 83*100:
      obj.select_set(True)
  bpy.ops.object.delete(confirm=False, use_global=True)

def main():
  jz = int(os.environ["JZ"])
  t0 = time.time()
  delete_small_objects()
  bpy.ops.wm.save_as_mainfile(filepath=f"{blender_scroll_dir}/labels/sparse_z{jz:02d}.blend")
  t = time.time() - t0
  print(f"Done. ({t} s.)")

if __name__ == "__main__":
  bpy.context.preferences.edit.use_global_undo = False
  try:
    main()
  finally:
    bpy.context.preferences.edit.use_global_undo = True


# max_nverts/100 | n_holes with nverts > max_nverts
# 1 275580
# 2 95001
# 3 55562
# 4 40358
# 5 32068
# 6 26614
# 7 22655
# 8 19770
# 9 17505
# 10 15646
# 11 14032
# 12 12664
# 13 11469
# 14 10433
# 15 9562
# 16 8789
# 17 8110
# 18 7466
# 19 6924
# 20 6440
# 21 5991
# 22 5555
# 23 5209
# 24 4873
# 25 4565
# 26 4263
# 27 3992
# 28 3752
# 29 3527
# 30 3336
# 31 3151
# 32 2960
# 33 2780
# 34 2592
# 35 2458
# 36 2312
# 37 2168
# 38 2020
# 39 1889
# 40 1785
# 41 1678
# 42 1570
# 43 1480
# 44 1408
# 45 1328
# 46 1266
# 47 1195
# 48 1123
# 49 1068
# 50 1013
# 51 961
# 52 904
# 53 859
# 54 816
# 55 752
# 56 711
# 57 679
# 58 639
# 59 603
# 60 572
# 61 537
# 62 506
# 63 481
# 64 461
# 65 426
# 66 403
# 67 389
# 68 373
# 69 356
# 70 337
# 71 326
# 72 311
# 73 296
# 74 288
# 75 279
# 76 266
# 77 247
# 78 236
# 79 224
# 80 218
# 81 215
# 82 209
# 83 201
# 84 197
# 85 192
# 86 189
# 87 183
# 88 174
# 89 168
# 90 165
# 91 161
# 92 155
# 93 149
# 94 148
# 95 141
# 96 134
# 97 129
# 98 124
# 99 122
# 100 115
# 101 112
# 102 107
# 103 105
# 104 103
# 105 102
# 106 99
# 107 95
# 108 91
# 109 88
