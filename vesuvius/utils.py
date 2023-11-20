import bpy
import bmesh

def import_stl(filepath):
	bpy.ops.wm.stl_import(
		filepath=filepath,
		global_scale=0.01,
		forward_axis='Y',
		up_axis='Z'
	)

def get_cell_collections():
	cell_collections = []
	for col in bpy.data.collections:
		if col.name.startswith("cell_yxz_") and len(col.name) == len("cell_yxz_000_000_000"):
			cell_collections.append(col)
	return cell_collections

def collect_objects_by_cell():
	cell_prefix = "cell_yxz_"
	for obj in bpy.data.objects:
		if not obj.name.startswith(cell_prefix):
			continue
		cell_collection_name = obj.name[:len("cell_yxz_YYY_XXX_ZZZ")]
		cell_collection = activate_collection(cell_collection_name)
		if cell_collection not in obj.users_collection:
			bpy.context.collection.objects.link(obj)


def activate_collection(name):
	if name in bpy.data.collections:
		col = bpy.data.collections[name]
	else:
		col = bpy.data.collections.new(name)
		bpy.context.scene.collection.children.link(col)
	bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[col.name]
	return col


def get_or_create(collection, name):
	o = collection.get(name)
	if not o:
		o = collection.new(name=name)
	return o


def create_quad(a, b, c, d, name="Plane"):
	mesh = bpy.data.meshes.new(f"{name}Mesh")
	obj = bpy.data.objects.new(name, mesh)
	bpy.context.collection.objects.link(obj)
	bpy.context.view_layer.objects.active = obj
	obj.select_set(True)

	bm = bmesh.new()
	bm.faces.new([bm.verts.new(v) for v in (a, b, c, d)])
	bm.normal_update()
	bm.to_mesh(mesh)
	bm.free()
	mesh.update()

	return obj
