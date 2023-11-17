import bpy
import sys

def ls(file_path):
	bpy.ops.wm.open_mainfile(filepath=file_path)
	for col in bpy.data.collections:
		print(col.name)
		for obj in col.objects:
			print(" ", obj.name)
			last_obj_name = obj.name


if __name__ == "__main__":
	if "--" not in sys.argv:
		print(f"Usage: blender-3.6 -b -P {sys.argv[0]} -- <args>")
	else:
		i = sys.argv.index("--")
		args = sys.argv[i+1:]
		ls(*args)
