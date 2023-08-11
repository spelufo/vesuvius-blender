import bpy, bmesh

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
