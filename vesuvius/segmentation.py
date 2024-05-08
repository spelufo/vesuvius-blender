import bpy
import bmesh
import math, random
from collections import defaultdict
from mathutils import Vector
from .graph import *
from .utils import *

# Smaller values produce a lot more sheet faces, and will probably
# worsen performance down the line. We could make this very big and
# rely more on the potential to fill in, resulting in less accuracy.
SPLIT_HOLES_MIN_POLYGONS = 50

# Hole Splitting: Nuke Backfaces Method ########################################

# TODO: I could do this offline much faster with julia, but I didn't manage to
# make the right mesh yet, the indexing seems to be off by one or sth...


def nuke_backfaces(ctx):
	o, _ = find_core_point_for_cursor_layer()
	assert o is not None, "Didn't find core vertex."
	ctx.scene.cursor.location = o

	for obj in ctx.selected_objects:
		if not obj.type == 'MESH':
			continue
		bpy.context.view_layer.objects.active = obj
		bpy.ops.object.mode_set(mode='OBJECT')
		mesh = obj.data
		bm = bmesh.new()
		bm.from_mesh(mesh)
		faces_to_delete = []
		for face in bm.faces:
			p = obj.matrix_world @ face.calc_center_median()
			direction_to_cursor = (p - o).normalized()
			face_normal = obj.matrix_world.to_3x3() @ face.normal
			if face_normal.dot(direction_to_cursor) > 0:
				faces_to_delete.append(face)
		bmesh.ops.delete(bm, geom=faces_to_delete, context='FACES')
		bm.to_mesh(mesh)
		bm.free()
		obj.data = mesh
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.object.mode_set(mode='OBJECT')

	bpy.ops.mesh.separate(type='LOOSE')
	delete_low_poly(SPLIT_HOLES_MIN_POLYGONS)


# Hole Splitting: Separate at Creases Method ###################################

# TODO: If this isn't good enough, try spectral graph partitioning.

def split_holes(ctx, holes=None):
	n_split = 0
	holes = holes or ctx.selected_objects
	for hole in holes:
		if "." in hole.name: # Hole already split.
			continue
		print("Splitting hole", hole.name)
		split_hole(hole)
		n_split += 1
	return n_split

def split_hole(hole):
	bpy.ops.object.select_all(action='DESELECT')
	bpy.context.view_layer.objects.active = hole
	hole.select_set(True)
	hole_name = hole.name
	bpy.ops.object.editmode_toggle()
	bpy.ops.mesh.edges_select_sharp(sharpness=0.698132)
	bpy.ops.mesh.edge_split(type='EDGE')
	bpy.ops.object.editmode_toggle()
	bpy.ops.mesh.separate(type='LOOSE')
	hole_sheets = delete_low_poly(SPLIT_HOLES_MIN_POLYGONS)
	for i, hole_sheet in enumerate(hole_sheets):
		hole_sheet.name = f"{hole_name}.{i:02d}"


def deselect_high_poly(min_polygons):
	high_poly = []
	for obj in bpy.context.selected_objects:
		if len(obj.data.polygons) >= min_polygons:
			high_poly.append(obj)
			obj.select_set(False)
	return high_poly

def delete_low_poly(min_polygons):
	high_poly = deselect_high_poly(min_polygons)
	bpy.ops.object.delete(confirm=False, use_global=True)
	return high_poly

# def rename_split_holes(ctx, holes=None):
# 	holes = holes or ctx.selected_objects
# 	by_name = defaultdict(list)
# 	for hole in holes:
# 		name = hole.name.rsplit(".", maxsplit=1)[0]
# 		by_name[name].append(hole)
# 	for name, holes in by_name.items():
# 		for i, hole in enumerate(holes):
# 			hole.name = f"{name}.{i:02d}"


# Hole Sorting #################################################################

# This approach is fine as a starting point and hopefully it doesn't require
# too much manual correction, but we might want to keep the graph of constraints
# around and propagate user adjustments through it.

# TODO: Rename "sheet_faces" to "patches".

def raycast_sort(ctx):
	radial_dir = radial_direction(ctx)
	sheet_faces = ctx.selected_objects
	sheet_face_0 = ctx.active_object
	print("Raycast sort from: ", ctx.active_object.name)
	print("Raycast sort direction: ", radial_dir)

	for sheet_face in sheet_faces:
		n_sheet_face = object_average_normal(sheet_face)
		sheet_face["sheet_face_direction"] = "A" if n_sheet_face.dot(radial_dir) < 0 else "B"

	edge_weights = defaultdict(lambda: 0)
	edge_distances = defaultdict(lambda: 1000)
	depsgraph = ctx.evaluated_depsgraph_get()
	for (i, sheet_face) in enumerate(sheet_faces):
		print(f"Raycasting sheet face {i}/{len(sheet_faces)}...")
		sheet_face_direction = sheet_face["sheet_face_direction"]
		for (j, v) in enumerate(sheet_face.data.vertices):
			# print(f"  vertex {i}/{len(sheet_face.data.vertices)}...")
			p = sheet_face.matrix_world @ v.co
			n = v.normal
			if sheet_face_direction == "A":
				n = -v.normal
				# p += 0.001*n
			hit, p_hit, _, _, obj_hit, _ = ctx.scene.ray_cast(depsgraph, p, n, distance=10)
			if hit and obj_hit.get("sheet_face_direction") != sheet_face_direction:
				d = (p_hit - p).length
				edge = (sheet_face.name, obj_hit.name)
				edge_weights[edge] += 1/d
				edge_distances[edge] = min(edge_distances[edge], d)
			# Same thing backwards: rationale is that small objects might be missed
			# by rays shooting at them (but not from them).
			hit, p_hit, _, _, obj_hit, _ = ctx.scene.ray_cast(depsgraph, p, -n, distance=10)
			if hit and obj_hit.get("sheet_face_direction") != sheet_face_direction:
				d = (p_hit - p).length
				edge = (obj_hit.name, sheet_face.name)
				edge_weights[edge] += 1/d
				edge_distances[edge] = min(edge_distances[edge], d)
	print("Done raycasting.")

	g_verts = [sheet_face.name for sheet_face in sheet_faces]
	g_edges = [(v, w, m) for (v, w), m in edge_weights.items()]
	g_verts_meta = {sheet_face.name: sheet_face["sheet_face_direction"] for sheet_face in sheet_faces}
	g_edges_meta = edge_distances
	g = Graph(g_verts, g_edges, verts_meta=g_verts_meta, edges_meta=g_edges_meta)
	# g.vis("holes")
	ga, edges_cut = break_cycles(g)
	# ga.vis("holes_dag")

	print("edges_cut", edges_cut)

	for i, sf_name in enumerate(topo_sorted_by_distance(ga, sheet_face_0.name)):
		print(i, sf_name)
		sf = next(sf for sf in sheet_faces if sf.name == sf_name)
		if sf_name.startswith("s"):
			sf_name = sf_name[4:]
		sf.name = f"s{i:02}_{sf_name}"


# TODO: This could be better in many ways. The main issue might be piercing
# papyrus back to front if there are high freq turns on itself so that there's
# no single radial direction that works for the whole cell. In that case we'd
# need a more local approximation. Hoping it is not needed in most cases. As
# long as the dot product of this approximation and the sheet normal is of the
# true sign we'll be fine.
# I've decided this is not a lot of work for a person to do on each cell, but
# let's make that efficient and accurate. Using the camera-cursor direction is
# one option. Another is using the two extremum objects: place the cursor on the
# last one and make the first one the active one.
def radial_direction(ctx):
	# rv3d = find_view_3d(ctx)
	# view_matrix = rv3d.view_matrix.inverted()
	# p_from = view_matrix.translation
	p_from = object_centroid(ctx.active_object)
	p_to = ctx.scene.cursor.location
	radial_dir = (p_to - p_from).normalized()
	return radial_dir

def object_centroid(obj):
	mesh = obj.data
	centroid = sum((v.co for v in mesh.vertices), Vector((0.0, 0.0, 0.0))) / len(mesh.vertices)
	return obj.matrix_world @ centroid

def object_average_normal(obj):
	mesh = obj.data
	n = sum((v.normal for v in mesh.vertices), Vector((0.0, 0.0, 0.0))) / len(mesh.vertices)
	return n.normalized()

def find_view_3d(ctx):
	for area in ctx.screen.areas:
		if area.type == 'VIEW_3D':
			space_data = area.spaces.active
			return space_data.region_3d


def filter_selected_sheet_face(ctx, face_direction="A"):
	sheet_faces = ctx.selected_objects
	for sheet_face in sheet_faces:
		if sheet_face.get("sheet_face_direction") != face_direction:
			sheet_face.select_set(False)


def select_closest_by_raycast(ctx, segment):
	bpy.ops.object.select_all(action='DESELECT')
	depsgraph = ctx.evaluated_depsgraph_get()
	for v in segment.data.vertices:
		p = segment.matrix_world @ v.co
		n = v.normal
		candidates = []
		# forward
		hit, p_hit, n_hit, _, obj_hit, _ = ctx.scene.ray_cast(depsgraph, p, n, distance=1)
		if hit and n.dot(n_hit) < 0:
			obj_hit.hide_set(True)
			hit, p_hit, n_hit, _, obj_hit, _ = ctx.scene.ray_cast(depsgraph, p, n, distance=1)
		if hit:
			candidates.append(((p_hit - p).length, obj_hit))
		# backward
		hit, p_hit, n_hit, _, obj_hit, _ = ctx.scene.ray_cast(depsgraph, p, -n, distance=1)
		if hit and n.dot(n_hit) < 0:
			obj_hit.hide_set(True)
			hit, p_hit, n_hit, _, obj_hit, _ = ctx.scene.ray_cast(depsgraph, p, -n, distance=1)
		if hit:
			candidates.append(((p_hit - p).length, obj_hit))
		d_min = 9000
		closest_obj = None
		for (d, obj) in candidates:
			if d < d_min:
				d_min = d
				closest_obj = obj
		if closest_obj:
			closest_obj.select_set(True)


def hide_not_directly_seen_from(ctx, segment):
	bpy.ops.object.select_all(action='DESELECT')
	depsgraph = ctx.evaluated_depsgraph_get()
	for v in segment.data.vertices:
		# forward
		p = segment.matrix_world @ v.co
		n = v.normal
		hit, p_hit, n_hit, _, obj_hit, _ = ctx.scene.ray_cast(depsgraph, p, n, distance=0.2)
		if hit and n.dot(n_hit) < 0:
			obj_hit.hide_set(True)
			hit, p_hit, n_hit, _, obj_hit, _ = ctx.scene.ray_cast(depsgraph, p, n, distance=0.2)
		p = p_hit + n*0.001
		for i in range(5):
			hit, p_hit, n_hit, _, obj_hit, _ = ctx.scene.ray_cast(depsgraph, p, n, distance=0.2)
			if not hit:
				break
			obj_hit.hide_set(True)
			p = p_hit + n*0.001

		# backward
		p = segment.matrix_world @ v.co
		n = -v.normal
		hit, p_hit, n_hit, _, obj_hit, _ = ctx.scene.ray_cast(depsgraph, p, n, distance=0.2)
		if hit and n.dot(n_hit) > 0:
			obj_hit.hide_set(True)
			hit, p_hit, n_hit, _, obj_hit, _ = ctx.scene.ray_cast(depsgraph, p, n, distance=0.2)
		p = p_hit + n*0.001
		for i in range(5):
			hit, p_hit, n_hit, _, obj_hit, _ = ctx.scene.ray_cast(depsgraph, p, n, distance=0.2)
			if not hit:
				break
			obj_hit.hide_set(True)
			p = p_hit + n*0.001
