import gc, time, json, os
import bpy
import vesuvius.utils

def main():
  collections = vesuvius.utils.get_cell_collections()
  vert_count_histogram = [0 for _ in range(500)]
  vert_count_histograms_per_cell = {}
  t0 = time.time()
  n_collections = len(collections)
  for (i, col) in enumerate(collections):
    cell_vert_count_histogram = [0 for _ in range(500)]
    vert_count_histograms_per_cell[col.name] = cell_vert_count_histogram
    for obj in col.objects:
      vert_count_histogram[len(obj.data.vertices) // 100] += 1
      cell_vert_count_histogram[len(obj.data.vertices) // 100] += 1
  result = {
    "vert_count_histogram": vert_count_histogram,
    "vert_count_histograms_per_cell": vert_count_histograms_per_cell,
  }

  jz = int(os.environ.get("JZ", "0"))
  with open(f"vert_count_histograms_{jz:02d}.json", "w+") as f:
    json.dump(result, f)
  t = time.time() - t0
  print(f"Done. ({t} s.)")

if __name__ == "__main__":
  bpy.context.preferences.edit.use_global_undo = False
  try:
    main()
  finally:
    bpy.context.preferences.edit.use_global_undo = True

