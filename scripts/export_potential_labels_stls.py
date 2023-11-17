# TODO: If used again, un-hardcode (11, 7, 22).
# TODO: Rename to avoid confusion with ink labels. This are potentials labels.

import bpy
from pathlib import Path

def export_object_to_stl(obj, path):
    bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects
    bpy.context.view_layer.objects.active = obj   # Make the current object active
    obj.select_set(True)                          # Select the current object
    bpy.ops.export_mesh.stl(filepath=path, use_selection=True, global_scale=100)

data_dir = Path("/mnt/phil/vesuvius/data")
volpkg_dir = data_dir / "full-scrolls" / "Scroll1.volpkg"
labels_dir = volpkg_dir / "segmentation/cell_yxz_011_007_022/labels"

objects = list(bpy.context.selected_objects)
for obj in objects:
    export_object_to_stl(obj, f"{labels_dir}/{obj.name}.stl")
