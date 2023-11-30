# https://blender.stackexchange.com/questions/77471/can-i-select-every-object-in-the-scene-that-is-touching-the-active-object
# Doesn't seem to work too well.

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import bmesh
import time

# In this context, utility/debug function to check if bounding test are ok.
def bounds_to_mesh(obj, scene):
	name = obj.name + "_bounds"
	meshData = bpy.data.meshes.new(name)
	meshObj = bpy.data.objects.new(name, meshData)
	meshObj.matrix_world = obj.matrix_world.copy()
	meshObj.data.from_pydata(*bounds_geometry(obj))
	scene.objects.link(meshObj)
	return meshObj

# Create bounding geometry from an object.
def bounds_geometry(obj):
	verts = [Vector(co) for co in obj.bound_box]
	edges = []
	faces = [(0,1,2,3), (4,5,1,0), (7,6,5,4), (3,2,6,7), (6,2,1,5), (7,4,0,3)]
	return verts, edges, faces

def bounds_geometry_in_world(obj):
	verts, edges, faces = bounds_geometry(obj)
	return [obj.matrix_world @ v for v in verts], edges, faces

def mesh_geometry_in_world(obj):
	return [obj.matrix_world @ v.co for v in obj.data.vertices], [], [p.vertices for p in obj.data.polygons]

def bvh_from_bounds(obj):
	verts, edges, faces = bounds_geometry_in_world(obj)
	return BVHTree.FromPolygons(verts, faces)

def bvh_from_mesh(obj):
	verts, edges, faces = mesh_geometry_in_world(obj)
	return BVHTree.FromPolygons(verts, faces)

def bvh_from_mesh(obj):
	bm = bmesh.new()
	bm.from_mesh(obj.data)
	bm.transform(obj.matrix_world)
	result = BVHTree.FromBMesh(bm)
	del bm
	return result

def intersect_bvh_obj(bvh, obj, to_bvh):
	obj_bvh = to_bvh(obj)
	result = bvh.overlap(obj_bvh)
	del obj_bvh
	return result

def intersect_obj_obj(obj, others, to_bvh):
	obj_bvh = to_bvh(obj)
	result = [other for other in others if intersect_bvh_obj(obj_bvh, other, to_bvh)]
	del obj_bvh
	return result

def intersect_bounds(obj, others):
	return intersect_obj_obj(obj, others, bvh_from_bounds)

def intersect_mesh(obj, others):
	return intersect_obj_obj(obj, others, bvh_from_mesh)

def select_intersecting(obj, scene, others, intersect_bounding):
	result = intersect_bounds(obj, others)

	if intersect_bounding == False:
		#startTime = time.time()
		#for i in range(1000):
			result = intersect_mesh(obj, result)
		#print("elapsed", time.time() - startTime)

	for o in result:
		o.select_set(True)







class SelectIntersectActive(bpy.types.Operator):
	bl_idname = "object.select_intersect_active"
	bl_label = "Select intersect active"
	bl_options = {'REGISTER', 'UNDO'}

	intersect_bounding = bpy.props.BoolProperty(name="Intersect bounding", default=True)

	@classmethod 
	def poll(cls, context):
		scene = context.scene
		obj = context.active_object
		return obj and obj.type == 'MESH' and obj.mode == 'OBJECT'

	def execute(self, context):
		scene = context.scene
		obj = context.active_object

		#Keep only non selected objects (cumulative selection)
		select_intersecting(obj, scene,
			[o for o in scene.objects if o.select_get() == False and o != obj],
			self.intersect_bounding)

		return {'FINISHED'}

def select_intersect_menu_func(self, context):
	self.layout.operator(SelectIntersectActive.bl_idname)
