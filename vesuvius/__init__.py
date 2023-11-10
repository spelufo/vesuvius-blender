bl_info = {
	"name": "Vesuvius",
	"blender": (2, 80, 0),
	"category": "Object",
}


if "vesuvius" not in locals():
	from . import vesuvius
	from . import raycast_sort
	from . import shaders
	from . import data
	from . import utils
else:
	print("Reloading vesuvius...")
	import importlib
	importlib.reload(utils)
	importlib.reload(data)
	importlib.reload(shaders)
	importlib.reload(raycast_sort)
	importlib.reload(vesuvius)


def register():
	vesuvius.register()


def unregister():
	vesuvius.unregister()
