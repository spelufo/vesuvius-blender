import bpy
import math, random
from collections import defaultdict
from mathutils import Vector
from .graph import *

# Hole Splitting ###############################################################

# Smaller values produce a lot more sheet faces, and will probably
# worsen performance down the line. We could make this very big and
# rely more on the potential to fill in, resulting in less accuracy.
SPLIT_HOLES_MIN_POLYGONS = 24

def split_holes(ctx):
	for hole in ctx.selected_objects:
		print("Splitting hole", hole.name)
		split_hole(hole)

def split_hole(hole):
	bpy.ops.object.select_all(action='DESELECT')
	bpy.context.view_layer.objects.active = hole
	hole.select_set(True)
	bpy.ops.object.editmode_toggle()
	bpy.ops.mesh.edges_select_sharp(sharpness=0.698132)
	bpy.ops.mesh.edge_split(type='EDGE')
	bpy.ops.object.editmode_toggle()
	bpy.ops.mesh.separate(type='LOOSE')
	delete_selected_low_poly(SPLIT_HOLES_MIN_POLYGONS)

def delete_low_poly(min_polygons):
	for obj in bpy.context.selected_objects:
		if len(obj.data.polygons) >= min_polygons:
			obj.select_set(False)
	bpy.ops.object.delete(confirm=False, use_global=True)


# Hole Sorting #################################################################


# TODO: Build the graph from each sheet face without going through objects.

def raycast_sort(ctx):
		rv3d = find_view_3d(ctx)
		view_matrix = rv3d.view_matrix.inverted()
		camera_position = view_matrix.translation
		cursor_position = ctx.scene.cursor.location
		rays_dir = cursor_position - camera_position
		rays_dir.normalize()

		objects = ctx.selected_objects
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
		depsgraph = ctx.evaluated_depsgraph_get()
		for i, tgt in enumerate(targets):
			print(f"target {i+1}/{len(targets)}")
			p = tgt - 10*rays_dir
			v = rays_dir
			d_total = 0.0
			obj_hit_last = None
			p_hit_last = None
			for i in range(200):
				hit, p_hit, n, _, obj, _ = ctx.scene.ray_cast(depsgraph, p, v)
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

def find_view_3d(ctx):
	for area in ctx.screen.areas:
		if area.type == 'VIEW_3D':
			space_data = area.spaces.active
			return space_data.region_3d

