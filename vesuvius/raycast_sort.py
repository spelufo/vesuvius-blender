import bpy
import math, random
from collections import defaultdict
from mathutils import Vector
from .graph import *


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
		# perp_e1 = rays_dir.cross(Vector((1,1,1)))
		# perp_e2 = perp_e1.cross(rays_dir)


		objects = context.selected_objects
		sizes = {}
		targets = []
		for obj in objects:
			n_verts = len(obj.data.vertices)
			sizes[obj.name] = math.sqrt(n_verts)
			n_targets = min(n_verts, 30)
			for (i, v) in enumerate(obj.data.vertices):
				jitter = Vector((random.random(), random.random(), random.random()))
				jitter.normalize()
				jitter *= 0.05
				if n_targets > n_verts:
					targets.append(obj.matrix_world @ v.co + jitter)
				elif random.random() < n_targets/n_verts:
					targets.append(obj.matrix_world @ v.co + jitter)

		print("len(targets) ==", len(targets))

		edges = defaultdict(float)
		distances = defaultdict(float)
		depsgraph = context.evaluated_depsgraph_get()
		# targets = targets[:1]
		for i, tgt in enumerate(targets):
			print(f"target {i+1}/{len(targets)}")
			p = tgt - 10*rays_dir
			v = rays_dir
			d_total = 0.0
			obj_hit_last = None
			p_hit_last = None
			for i in range(200):
				hit, p_hit, n, _, obj, _ = context.scene.ray_cast(depsgraph, p, v)
				if not hit:
					break
				# bpy.ops.object.empty_add(location = p_hit)
				d_total += (p_hit - p).length + 0.01
				p = p_hit + 0.01 * v
				if obj in objects:
					distances[obj.name] = max(distances[obj.name], d_total)
					if obj_hit_last and obj != obj_hit_last:
						edges[(obj_hit_last.name, obj.name)] = sizes[obj_hit_last.name] * sizes[obj.name]
					obj_hit_last = obj
					p_hit_last = p_hit
		print("Done raycasting.")

		g = Graph([obj.name for obj in objects], [(v, w, m) for (v, w), m in edges.items()])
		g.vis("holes")
		ga, edges_cut = break_cycles(g)
		ga.vis("holes_dag")
		print("edges_cut", edges_cut)
		levels = sort_by_distance_with_constraints(ga, distances)

		for (i, lvl) in enumerate(levels):
			for objname in lvl:
				obj = next(obj for obj in objects if obj.name == objname)
				if objname.startswith("l"):
					objname = objname[4:]
				obj.name = f"l{i:02}_{objname}"

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
