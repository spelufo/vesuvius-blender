# Usage:
# for z in $(seq -w 13 20); do
#   tmux new -d -s "z${z}" "blender -b patches/patches_z${z}.blend --python vesuvius-blender/scripts/build_layer_patches.py"
# done

import gc, time
import bpy
import vesuvius.segmentation
import vesuvius.utils


def main():
  cell_collections = vesuvius.utils.get_cell_collections()

  t0 = time.time()
  n_collections = len(cell_collections)
  for (i, col) in enumerate(cell_collections):
    print(f"Processing cell collection {col.name} ({i}/{n_collections})...")
    t_split_start = time.time()
    n_split = vesuvius.segmentation.split_holes(bpy.context, col.objects)
    if n_split > 0:
      t_save_start = time.time()
      bpy.ops.wm.save_mainfile()
      t_split = t_save_start - t_split_start
      t_save = time.time() - t_save_start
      t = t_save + t_split
      print(f"t_split = {t_split:.2f} s. | t_save = {t_save:.2f} s. | t = {t:.2f} s.")
      t_cleanup_start = time.time()
      print(f"Cleanup")
      bpy.ops.outliner.orphans_purge()
      gc.collect()
      t_cleanup = time.time() - t_cleanup_start
      print(f"t_cleanup = {t_cleanup:.2f} s.")
    print(f"Done processing cell collection {col.name}")
  print("Done.")


if __name__ == "__main__":
  bpy.context.preferences.edit.use_global_undo = False
  try:
    main()
  finally:
    bpy.context.preferences.edit.use_global_undo = True
