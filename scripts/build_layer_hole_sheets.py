import time
import bpy
import vesuvius.segmentation

def main():
  cell_collections = []
  for col in bpy.data.collections:
    if col.name.startswith("cell_yxz_") and len(col.name) == len("cell_yxz_000_000_000"):
      cell_collections.append(col)

  t0 = time.time()
  n_collections = len(cell_collections)
  for (i, col) in enumerate(cell_collections):
    print(f"Processing cell collection {col.name} ({i}/{n_collections})...")
    vesuvius.segmentation.split_holes(bpy.context, col.objects)
    bpy.ops.wm.save_mainfile()
    t = time.time() - t0
    print(f"Done processing cell collection {col.name}")
    print(f"t = {int(t/60)} min. ~{int(t/n_collections/60)} min/collection")
  print("Done.")


if __name__ == "__main__":
  bpy.context.preferences.edit.use_global_undo = False
  try:
    main()
  finally:
    bpy.context.preferences.edit.use_global_undo = True
