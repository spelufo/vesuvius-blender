import bpy
import bpy_types
import bmesh
from mathutils import Vector, Matrix


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

def find_core_point_for_cursor_layer(ctx):
	cz = ctx.scene.cursor.location.z
	d = 1000000
	o = None
	i = -1
	core = ctx.scene.objects["Core"]
	for i, v in enumerate(core.data.vertices):
		pv = core.matrix_world @ v.co
		v_d = abs(pv.z - cz)
		if v_d < d:
			d = v_d
			o = v.co
			oi = i
	return o, oi

def activate_collection(name, parent_collection=None):
	if isinstance(name, bpy_types.Collection):
		col = name
	elif name in bpy.data.collections:
		col = bpy.data.collections[name]
	else:
		col = bpy.data.collections.new(name)
		parent_col = parent_collection or bpy.context.scene.collection
		parent_col.children.link(col)
	bpy.context.view_layer.active_layer_collection = find_collection_layer(
		col,
		bpy.context.view_layer.layer_collection,
	)
	return col

def find_collection_layer(col, root_layer):
	layer = None
	if col.name in root_layer.children:
		return root_layer.children[col.name]
	for sub_layer in root_layer.children:
		layer = find_collection_layer(col, sub_layer)
		if layer:
			break
	return layer


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

def create_camera(p, fwd_dir, up_dir, name="Camera"):
	cam_data = bpy.data.cameras.new(name=name)
	cam_obj = bpy.data.objects.new(name=name, object_data=cam_data)
	bpy.context.collection.objects.link(cam_obj)
	ori = Matrix()
	ori[0][0:3] = fwd_dir.cross(up_dir)
	ori[1][0:3] = up_dir
	ori[2][0:3] = -fwd_dir
	ori.transpose()
	cam_obj.matrix_world = ori @ cam_obj.matrix_world
	cam_obj.location = p
