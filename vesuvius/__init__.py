bl_info = {
	"name": "Vesuvius",
	"blender": (2, 80, 0),
	"category": "Object",
}

if "bpy" not in locals():
	import bpy
	from . import vesuvius
	from . import shaders
	from . import utils
else:
	import importlib
	importlib.reload(utils)
	importlib.reload(shaders)
	importlib.reload(vesuvius)


def register():
	vesuvius.register()

def unregister():
	vesuvius.unregister()
