import os, sys
from pathlib import Path
import bpy
import numpy as np


data_dir = Path("/mnt/phil/vesuvius/data")
blender_scroll_dir = Path("/mnt/phil/vesuvius/blender/scroll_1_54")
volpkg_dir = data_dir / "full-scrolls" / "Scroll1.volpkg"
segments_dir = volpkg_dir / "paths"
patches_dir = blender_scroll_dir / "patches"
blender_segments_dir = blender_scroll_dir / "segments"

CELL_SIZE = 5
NSUBDIVS = 20
L = CELL_SIZE / NSUBDIVS

def main(input_file, output_file):
	assert output_file.endswith(".blend"), "output must be a path to a .blend file to create or overwrite"

	bpy.ops.wm.open_mainfile(filepath=f"{blender_scroll_dir}/scroll_1_54_base.blend")

	if input_file.endswith(".stl"):
		import_fn = bpy.ops.wm.stl_import
	elif input_file.endswith(".obj"):
		import_fn = bpy.ops.wm.obj_import
	else:
		assert False, "unsupported input file extension"

	import_fn(
		filepath=input_file,
		global_scale=0.01,
		forward_axis='Y',
		up_axis='Z'
	)

	segment_object_name = input_file.split("/")[-1][:-4]
	segment = bpy.data.objects[segment_object_name]
	segment_masks = make_segment_masks(segment)

	for jz in range(26):
		layer_patches_path = f"{patches_dir}/patches_z{jz:02d}.blend"
		if not os.path.exists(layer_patches_path):
			continue

		print(f"Loading layer {jz:02d}")
		with bpy.data.libraries.load(layer_patches_path, link=False) as (data_from, data_to):
			for objname in data_from.objects:
				j = object_cell(objname)
				if j and j in segment_masks:
					data_to.objects.append(objname)

		for obj in data_to.objects:
			if obj is not None:
				j = object_cell(obj.name)
				mask = segment_masks[j]
				touches_segment_mask = False
				for v in obj.data.vertices:
					p = obj.matrix_world @ v.co
					ix, iy, iz = mask_index(j, p)
					if mask[ix, iy, iz]:
						bpy.context.collection.objects.link(obj)
						touches_segment_mask = True
						break
				if not touches_segment_mask:
					bpy.data.meshes.remove(obj.data)

	bpy.ops.wm.save_as_mainfile(filepath=output_file)

def object_cell(objname):
	if not objname.startswith("cell_yxz_"):
		return None
	_, _, jy, jx, jz, *_ = objname.split("_")
	return (int(jx)-1, int(jy)-1, int(jz)-1)

def cell_index(p):
	return (
		int(p.x // CELL_SIZE),
		int(p.y // CELL_SIZE),
		int(p.z // CELL_SIZE))

def mask_index(j, p):
	return (
		int((p.x - j[0] * CELL_SIZE)//L),
		int((p.y - j[1] * CELL_SIZE)//L),
		int((p.z - j[2] * CELL_SIZE)//L))

def make_segment_masks(segment):
	segment_masks = {}
	for v in segment.data.vertices:
		p = segment.matrix_world @ v.co
		jp = cell_index(p)
		if jp not in segment_masks:
			segment_masks[jp] = np.zeros((NSUBDIVS, NSUBDIVS, NSUBDIVS), dtype=np.bool8)
		mask = segment_masks[jp]
		ix, iy, iz = mask_index(jp, p)
		mask[ix, iy, iz] = True
	return segment_masks


if __name__ == "__main__":
	if "--" not in sys.argv:
		print(f"Usage: blender-3.6 -b -P {sys.argv[0]} -- <args>")
		exit(1)
	else:
		i = sys.argv.index("--")
		args = sys.argv[i+1:]
		main(*args)
