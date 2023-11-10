import bpy
import math
from mathutils import Vector


class VesuviusRaycastSort(bpy.types.Operator):
	bl_idname = "object.vesuvius_raycast_sort"
	bl_label = "Raycast sort"

	def execute(self, context):
		rv3d = self.find_view_3d(context)
		scene = context.scene
		view_matrix = rv3d.view_matrix.inverted()
		camera_position = view_matrix.translation
		cursor_position = scene.cursor.location
		rays_dir = cursor_position - camera_position
		rays_dir.normalize()
		perp_e1 = rays_dir.cross(Vector((1,1,1)))
		perp_e2 = perp_e1.cross(rays_dir)
		g = {}
		for ix in range(-32, 33):
			for iy in range(-32, 33):
				p = camera_position + (5/64)*(ix*perp_e1 + iy*perp_e2)
				hit_objects = self.raycast(context, p, rays_dir)
				for i in range(1, len(hit_objects)):
					a = hit_objects[i-1]
					b = hit_objects[i]
					# add a -> b to the DAG g

		# bpy.ops.object.select_all(action='DESELECT')
		# for obj in hit_objects:
		# 	obj.select_set(True)

		return {"FINISHED"}

	def raycast(self, context, p, v, epsilon=0.001, max_hits=1000):
		hit_objects = []
		depsgraph = context.evaluated_depsgraph_get()
		for i in range(max_hits):
			result, p, n, _, obj, _ = context.scene.ray_cast(depsgraph, p, v)
			if result:
				if len(hit_objects) > 0 and hit_objects[-1] == obj:
					pass
				else:
					hit_objects.append(obj)
				p += epsilon * v
			else:
				break
		return hit_objects


	def find_view_3d(self, context):
		for area in context.screen.areas:
			if area.type == 'VIEW_3D':
				space_data = area.spaces.active
				return space_data.region_3d





# Remove inner holes... gpt:

# import bpy
# import bmesh
# from mathutils import Vector

# def is_mesh_contained(inner_obj, outer_obj):
#     # Ensure we are working with mesh objects
#     assert inner_obj.type == 'MESH' and outer_obj.type == 'MESH'
    
#     # Get the mesh data
#     bm = bmesh.new()
#     bm.from_mesh(inner_obj.data)
#     bm.transform(inner_obj.matrix_world)  # Apply transformation
    
#     # Ray casting
#     for vert in bm.verts:
#         direction = (vert.co - outer_obj.location).normalized()  # Direction from the vertex to the outer object's origin
#         result, location, normal, index = outer_obj.ray_cast(vert.co + direction * 0.0001, direction)
#         if not result:
#             return False  # If any ray doesn't hit the outer mesh, the mesh is not contained

#     return True  # All rays hit the outer mesh, the mesh is contained

# # Example usage:
# # Make sure you have two mesh objects selected, inner_obj is the potentially contained object,
# # and outer_obj is the containing object.
# selected_objects = bpy.context.selected_objects
# inner_obj = selected_objects[0]
# outer_obj = selected_objects[1]

# if is_mesh_contained(inner_obj, outer_obj):
#     print(f"{inner_obj.name} is contained within {outer_obj.name}")
# else:
#     print(f"{inner_obj.name} is NOT contained within {outer_obj.name}")
