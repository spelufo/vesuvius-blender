import bpy, bmesh
import json

from .data import *
from .shaders import *
from .utils import *
from .segmentation import *
from .select_intersect_active import *
from .radial_views import *
from .weld_turns import *
# from . import render_engine

ADDON_ID = "vesuvius"

_current_scan = None
def get_current_scan():
	global _current_scan
	if _current_scan:
		return _current_scan
	vol_ids = []
	for mat in bpy.data.materials:
		if mat.name.startswith("vesuvius_volpkg_"):
			vol_ids.append(mat.name.removeprefix("vesuvius_volpkg_"))
	if len(vol_ids) == 0:
		return None
	for scan in SCANS.values():
		if scan.vol_id in vol_ids:
			_current_scan = scan
			return scan


def set_current_scan(scan):
	global _current_scan
	_current_scan = scan


def setup_scene(scene, preview_samples=1):
	scene.render.engine = "CYCLES"
	scene.cycles.shading_system = True
	scene.cycles.preview_samples = preview_samples


def setup_material(scan):
	material = get_or_create(bpy.data.materials, f"vesuvius_volpkg_{scan.vol_id}")
	material.use_nodes = True
	node_tree = material.node_tree
	node_tree.nodes.clear()

	script_text = get_or_create(bpy.data.texts, f"vesuvius_shader_{scan.vol_id}")
	script_text.from_string(generate_shader(scan))

	output = node_tree.nodes.new(type="ShaderNodeOutputMaterial")
	output.location = (400, 0)
	emission = node_tree.nodes.new(type="ShaderNodeEmission")
	emission.location = (200, 0)
	script = node_tree.nodes.new(type="ShaderNodeScript")
	script.location = (0, 0)
	script.script = script_text
	node_tree.links.new(script.outputs["Value"], emission.inputs["Color"])
	node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])

	return material


def reload_shader(scan):
	print("reload shader")
	# material = get_or_create(bpy.data.materials, f"vesuvius_volpkg_{scan.vol_id}")
	# node_tree = material.node_tree
	script_text = get_or_create(bpy.data.texts, f"vesuvius_shader_{scan.vol_id}")
	script_text.from_string(generate_shader(scan))


def create_axis_planes(px, py, pz, dx, dy, dz, material, name="Plane"):
	plane_xy = create_quad((px, py, pz), (px + dx, py, pz), (px + dx, py + dy, pz), (px, py + dy, pz), f"{name}__XY")
	plane_xy.data.materials.append(material)
	return plane_xy

def create_axis_quads(px, py, pz, dx, dy, dz, material, name="Plane"):
	plane_xy = create_quad((px, py, pz), (px + dx, py, pz), (px + dx, py + dy, pz), (px, py + dy, pz), f"{name}__XY")
	plane_yz = create_quad((px, py, pz), (px, py + dy, pz), (px, py + dy, pz + dz), (px, py, pz + dz), f"{name}__YZ")
	plane_zx = create_quad((px, py, pz), (px, py, pz + dz), (px + dx, py, pz + dz), (px + dx, py, pz), f"{name}__ZX")
	plane_xy.data.materials.append(material)
	plane_yz.data.materials.append(material)
	plane_zx.data.materials.append(material)
	return plane_xy, plane_yz, plane_zx


def create_scan_quads(scan, material):
	dx, dy, dz = scan.width/100, scan.height/100, scan.slices/100
	plane_xy, plane_yz, plane_zx = create_axis_quads(0, 0, 0, dx, dy, dz, material)
	plane_yz.location.x += dx/2
	plane_zx.location.y += dy/2


def cell_name(cell):
	jx0, jy0, jz0 = cell
	jx, jy, jz = jx0+1, jy0+1, jz0+1
	return f"Cell_yxz_{jy:03}_{jx:03}_{jz:03}___{jx0:02}_{jy0:02}_{jz0:02}"

def cell_from_name(objname):
	return tuple(int(x) for x in objname[-12:-4].split("_"))

def create_cell_quads(cell, material):
	name = cell_name(cell)
	create_axis_quads(5*cell[0], 5*cell[1], 5*cell[2], 5, 5, 5, material, name=name)

def create_cell_planes(cell, material):
	name = cell_name(cell)
	create_axis_planes(5*cell[0], 5*cell[1], 5*cell[2], 5, 5, 5, material, name=name)

# NOTE: Harcoded material for scroll 1.
def add_grid_cells(cells):
	material = bpy.data.materials.get(f"vesuvius_volpkg_20230205180739")
	for cell in cells:
		create_cell_planes(cell, material)

def add_segments(segments):
	scan = get_current_scan()
	assert scan is not None, "scan not found"
	segments_dir = scan.segments_dir()
	for s in segments:
		bpy.ops.wm.obj_import(
			filepath=f"{segments_dir}/{s}/{s}.obj", directory=f"{segments_dir}/{s}",
			files=[{"name":f"{s}.obj", "name":f"{s}.obj"}],
			global_scale=0.01, forward_axis='Y', up_axis='Z'
		)

class VesuviusAddScan(bpy.types.Operator):
	bl_idname = "object.vesuvius_add_scan"
	bl_label = "Vesuvius Scan"

	scan_name: bpy.props.EnumProperty(
		items=[(x,x,x) for x in SCANS],
		name="Scan",
		description="Select the scan to add",
		default="scroll_1a_791_54",
	)

	def execute(self, context):
		if not get_data_dir():
			self.report({"ERROR"}, "Vesuvius data directory not found.")
			return {"CANCELLED"}
		scan = SCANS.get(self.scan_name)
		if not scan:
			self.report({"ERROR"}, f"Scan {repr(self.scan_name)} not found.")
			return {"CANCELLED"}
		set_current_scan(scan)
		self.report({"INFO"}, f"Requested {scan.small_volume_path}.")
		download_file_start(scan, scan.small_volume_path, context)
		setup_scene(context.scene)
		material = setup_material(scan)
		create_scan_quads(scan, material)
		return {"FINISHED"}

def vesuvius_add_menu_func(self, context):
	self.layout.operator_menu_enum(VesuviusAddScan.bl_idname, "scan_name")


class VesuviusCellOperator:
	def execute(self, context):
		if not get_data_dir():
			self.report({"ERROR"}, "Vesuvius data directory not found.")
			return {"CANCELLED"}

		scan = get_current_scan()
		if not scan:
			self.report({"ERROR"}, "No current scan, add a Vesuvius Scan first.")
			return {"CANCELLED"}

		cursor_p = context.scene.cursor.location
		if not (
			0 < cursor_p.x < scan.width/100 and
			0 < cursor_p.y < scan.height/100 and
			0 < cursor_p.z < scan.slices/100):
			self.report({"ERROR"}, "Cursor out of scan bounds.")
			return {"CANCELLED"}

		cell = world_to_grid(cursor_p)
		return self.execute_with_cell(context, scan, cell)


class VesuviusAddGridCell(bpy.types.Operator, VesuviusCellOperator):
	bl_idname = "object.vesuvius_add_grid_cell"
	bl_label = "Grid cell"

	def execute_with_cell(self, context, scan, cell):
		cell_name = scan.grid_cell_name(*cell)
		self.report({"INFO"}, f"{cell_name}  {cell}.")
		material = bpy.data.materials.get(f"vesuvius_volpkg_{scan.vol_id}")
		activate_collection(cell_name)
		create_cell_quads(cell, material)
		return {"FINISHED"}

class VesuviusFocusGridCell(bpy.types.Operator, VesuviusCellOperator):
	bl_idname = "object.vesuvius_focus_grid_cell"
	bl_label = "Focus grid cell"

	def execute_with_cell(self, context, scan, cell):
		self.report({"INFO"}, cell_name(cell))
		material = bpy.data.materials.get(f"vesuvius_volpkg_{scan.vol_id}")
		s = material.node_tree.nodes["Script"]
		# s.inputs["MinJ"].default_value = cell
		# s.inputs["MaxJ"].default_value = (cell[0]+1, cell[1]+1, cell[2]+1)
		s.inputs["MinJ"].default_value = (cell[0]-1, cell[1]-1, cell[2]-1)
		s.inputs["MaxJ"].default_value = (cell[0]+2, cell[1]+2, cell[2]+2)
		return {"FINISHED"}


class VesuviusDownloadGridCells(bpy.types.Operator, VesuviusCellOperator):
	bl_idname = "object.vesuvius_download_grid_cells"
	bl_label = "Download grid cells"

	def execute_with_cell(self, context, scan, cell):
		cell_path = scan.grid_cell_path(*cell)
		download_file_start(scan, cell_path, context)
		self.report({"INFO"}, f"Cell: {cell}.")
		return {"FINISHED"}

# TODO: Dedupe all these copy-pasted import_cell* import_layer* stuff.

def import_cell_holes(ctx, scan, cell, parent_collection=None):
	col = activate_collection(scan.grid_cell_name(*cell), parent_collection=parent_collection)
	holes_dir = scan.grid_cell_holes_dir(*cell)
	for filename in os.listdir(holes_dir):
		if not filename.endswith(".stl"):
			continue
		import_stl(f"{holes_dir}/{filename}")
	return col

def import_cell_patches(ctx, scan, cell, parent_collection=None):
	col = activate_collection(scan.grid_cell_name(*cell), parent_collection=parent_collection)
	patches_dir = scan.grid_cell_patches_dir(*cell)
	for filename in os.listdir(patches_dir):
		if not filename.endswith(".stl"):
			continue
		import_stl(f"{patches_dir}/{filename}")
	return col

def import_cell_chunks(ctx, scan, cell, parent_collection=None):
	col = activate_collection(scan.grid_cell_name(*cell), parent_collection=parent_collection)
	chunks_dir = scan.grid_cell_chunks_dir(*cell)
	for filename in os.listdir(chunks_dir):
		if not filename.endswith(".stl"):
			continue
		import_stl(f"{chunks_dir}/{filename}")
	return col

class VesuviusImportCellHoles(bpy.types.Operator, VesuviusCellOperator):
	bl_idname = "object.vesuvius_import_cell_holes"
	bl_label = "Import cell holes"
	def execute_with_cell(self, context, scan, cell):
		import_cell_holes(context, scan, cell)
		return {"FINISHED"}

def layer_cells(ctx, jz):
	cells = []
	for obj in bpy.data.objects:
		if obj.name.startswith("Cell_yxz_") and obj.name.endswith(f"{jz:02d}__XY"):
			cells.append(cell_from_name(obj.name))
	return cells

def import_layer_holes(ctx, scan, jz):
	holes_col = activate_collection(f"Holes_z{jz+1:02d}")
	for cell in layer_cells(ctx, jz):
		print(f"Importing holes for cell {cell}...")
		import_cell_holes(ctx, scan, cell, parent_collection=holes_col)

class VesuviusImportLayerHoles(bpy.types.Operator, VesuviusCellOperator):
	bl_idname = "object.vesuvius_import_layer_holes"
	bl_label = "Import layer holes"
	def execute_with_cell(self, context, scan, cell):
		_, _, jz = cell
		return import_layer_holes(context, scan, jz) or {"FINISHED"}

def import_layer_patches(ctx, scan, jz):
	patches_col = activate_collection(f"Patches_z{jz+1:02d}")
	for cell in layer_cells(ctx, jz):
		print(f"Importing patches for cell {cell}...")
		import_cell_patches(ctx, scan, cell, parent_collection=patches_col)

class VesuviusImportLayerPatches(bpy.types.Operator, VesuviusCellOperator):
	bl_idname = "object.vesuvius_import_layer_patches"
	bl_label = "Import layer patches"
	def execute_with_cell(self, context, scan, cell):
		_, _, jz = cell
		import_layer_patches(context, scan, jz)
		return {"FINISHED"}

def import_layer_chunks(ctx, scan, jz):
	chunks_col = activate_collection(f"Chunks_z{jz+1:02d}")
	for cell in layer_cells(ctx, jz):
		print(f"Importing chunks for cell {cell}...")
		import_cell_chunks(ctx, scan, cell, parent_collection=chunks_col)

class VesuviusImportLayerChunks(bpy.types.Operator, VesuviusCellOperator):
	bl_idname = "object.vesuvius_import_layer_chunks"
	bl_label = "Import layer chunks"
	def execute_with_cell(self, context, scan, cell):
		_, _, jz = cell
		import_layer_chunks(context, scan, jz)
		return {"FINISHED"}


class VesuviusReloadShader(bpy.types.Operator):
	bl_idname = "object.vesuvius_reload_shader"
	bl_label = "Reload vesuvius shader"

	def execute(self, context):
		scan = get_current_scan()
		if not scan:
			self.report({"ERROR"}, "No current scan, add a Vesuvius Scan first.")
			return {"CANCELLED"}
		reload_shader(scan)
		return {"FINISHED"}


class VesuviusRaycastSort(bpy.types.Operator):
	bl_idname = "object.vesuvius_raycast_sort"
	bl_label = "Raycast sort"
	def execute(self, context):
		return raycast_sort(context) or {"FINISHED"}

class VesuviusSelectClosestByRaycast(bpy.types.Operator):
	bl_idname = "object.vesuvius_select_closest_by_raycast"
	bl_label = "Select closest by raycast"
	def execute(self, context):
		if not context.selected_objects:
			self.report({"ERROR"}, "No selected object.")
			return {"CANCELLED"}
		segment = context.selected_objects[0]
		return select_closest_by_raycast(context, segment) or {"FINISHED"}

class VesuviusHideNotDirectlySeenFrom(bpy.types.Operator):
	bl_idname = "object.vesuvius_hide_not_directly_seen_from"
	bl_label = "Hide not directly seen from"
	def execute(self, context):
		if not context.selected_objects:
			self.report({"ERROR"}, "No selected object.")
			return {"CANCELLED"}
		segment = context.selected_objects[0]
		return hide_not_directly_seen_from(context, segment) or {"FINISHED"}

class VesuviusNukeBackfaces(bpy.types.Operator):
	bl_idname = "object.vesuvius_nuke_backfaces"
	bl_label = "Nuke backfaces"
	def execute(self, context):
		return nuke_backfaces(context) or {"FINISHED"}

class VesuviusSplitHoles(bpy.types.Operator):
	bl_idname = "object.vesuvius_split_holes"
	bl_label = "Split holes"
	def execute(self, context):
		return split_holes(context) or {"FINISHED"}

class VesuviusSelectA(bpy.types.Operator):
	bl_idname = "object.vesuvius_select_a"
	bl_label = "Select A (recto)"
	def execute(self, context):
		return filter_selected_sheet_face(context, "A") or {"FINISHED"}

class VesuviusSelectB(bpy.types.Operator):
	bl_idname = "object.vesuvius_select_b"
	bl_label = "Select B (verso)"
	def execute(self, context):
		return filter_selected_sheet_face(context, "B") or {"FINISHED"}

def hide_small_objects(ctx):
	for o in ctx.selected_objects:
		if len(o.data.vertices) < 1000:
			o.hide_set(True)

class VesuviusHideSmall(bpy.types.Operator):
	bl_idname = "object.vesuvius_hide_small"
	bl_label = "Hide small objects"
	def execute(self, context):
		return hide_small_objects(context) or {"FINISHED"}

def dump_object_names(ctx):
	dump = {}
	for col in ctx.scene.collection.children:
		objects = []
		for obj in col.objects:
			objects.append(obj.name)
		for subcol in col.children_recursive:
			for obj in subcol.objects:
				objects.append(obj.name)
		dump[col.name] = objects
	with open("/home/spelufo/pro/vesuvius/stabia/logs/blender_dump.json", "w+") as f:
		json.dump(dump, f, indent=2)

class VesuviusDumpObjectNames(bpy.types.Operator):
	bl_idname = "object.vesuvius_dump_object_names"
	bl_label = "Dump object names"
	def execute(self, context):
		return dump_object_names(context) or {"FINISHED"}


class VesuviusWeldScrollTurns(bpy.types.Operator):
	bl_idname = "object.vesuvius_weld_scroll_turns"
	bl_label = "Weld scroll turns"
	def execute(self, context):
		return weld_turns_selected(context) or {"FINISHED"}

class VesuviusDeselectManifolds(bpy.types.Operator):
	bl_idname = "object.vesuvius_deselect_manifolds"
	bl_label = "Deselect Manifolds"
	def execute(self, context):
		return deselect_manifolds(context) or {"FINISHED"}

class VesuviusMeshCleanup(bpy.types.Operator):
	bl_idname = "object.vesuvius_mesh_cleanup"
	bl_label = "Mesh cleanup"
	def execute(self, context):
		return mesh_cleanup(context) or {"FINISHED"}

class VesuviusBulkExportPLY(bpy.types.Operator):
	bl_idname = "object.vesuvius_bulk_export_ply"
	bl_label = "Bulk Export PLY"
	directory: bpy.props.StringProperty(name="Export Path", description="Export Path", subtype='DIR_PATH')

	def execute(self, context):
		# TODO: Put the files in a subdir next to the blend file or prompt for where.
		objs = context.selected_objects
		bpy.ops.object.select_all(action='DESELECT')
		for obj in objs:
			obj.select_set(True)
			bpy.ops.wm.ply_export(
				filepath=f"{self.directory}/{obj.name}.ply",
				global_scale=100.0,
				forward_axis='Y',
				up_axis='Z',
				export_selected_objects=True,
				export_uv=True,
				# TODO: Decide if we want to export normals for ply.
				# Does ply have the same problem as obj? I don't think so.
				# Do we need it to export normals for anything? I don't think so.
				# export_normals=False,
				export_colors=False,
				export_materials=False,
				export_animation=False,
			)
			obj.select_set(False)
		return {"FINISHED"}

	def invoke(self, context, event):
			context.window_manager.fileselect_add(self)
			return {'RUNNING_MODAL'}

class VesuviusBulkExportOBJ(bpy.types.Operator):
	bl_idname = "object.vesuvius_bulk_export_obj"
	bl_label = "Bulk Export OBJ"
	directory: bpy.props.StringProperty(name="Export Path", description="Export Path", subtype='DIR_PATH')

	def execute(self, context):
		# TODO: Put the files in a subdir next to the blend file or prompt for where.
		objs = context.selected_objects
		bpy.ops.object.select_all(action='DESELECT')
		for obj in objs:
			obj.select_set(True)
			bpy.ops.wm.obj_export(
				filepath=f"{self.directory}/{obj.name}.obj",
				global_scale=100.0,
				forward_axis='Y',
				up_axis='Z',
				export_selected_objects=True,
				export_uv=True,
				export_normals=False, # Else blender copies each vertex for each face.
				export_colors=False,
				export_materials=False,
				export_animation=False,
			)
			obj.select_set(False)
		return {"FINISHED"}

	def invoke(self, context, event):
			context.window_manager.fileselect_add(self)
			return {'RUNNING_MODAL'}


class VesuviusCreateCoreRadialCameras(bpy.types.Operator):
	bl_idname = "object.vesuvius_create_core_radial_cameras"
	bl_label = "Create core radial cameras"
	def execute(self, context):
		return create_core_radial_cameras(context) or {"FINISHED"}


class VesuviusPreferences(bpy.types.AddonPreferences):
	bl_idname = ADDON_ID
	data_dir: bpy.props.StringProperty(
		name="Path to data directory",
		subtype="DIR_PATH",
	)

	def draw(self, context):
		self.layout.prop(self, "data_dir")


def register():
	bpy.utils.register_class(VesuviusPreferences)
	bpy.utils.register_class(VesuviusAddScan)
	bpy.types.VIEW3D_MT_add.append(vesuvius_add_menu_func)
	bpy.utils.register_class(VesuviusAddGridCell)
	bpy.utils.register_class(VesuviusFocusGridCell)
	bpy.utils.register_class(VesuviusDownloadGridCells)
	bpy.utils.register_class(VesuviusImportCellHoles)
	bpy.utils.register_class(VesuviusImportLayerHoles)
	bpy.utils.register_class(VesuviusImportLayerPatches)
	bpy.utils.register_class(VesuviusImportLayerChunks)
	bpy.utils.register_class(VesuviusReloadShader)
	bpy.utils.register_class(VesuviusRaycastSort)
	bpy.utils.register_class(VesuviusSelectClosestByRaycast)
	bpy.utils.register_class(VesuviusHideNotDirectlySeenFrom)
	bpy.utils.register_class(VesuviusNukeBackfaces)
	bpy.utils.register_class(VesuviusSplitHoles)
	bpy.utils.register_class(VesuviusSelectA)
	bpy.utils.register_class(VesuviusSelectB)
	bpy.utils.register_class(VesuviusHideSmall)
	bpy.utils.register_class(VesuviusDumpObjectNames)
	bpy.utils.register_class(VesuviusWeldScrollTurns)
	bpy.utils.register_class(VesuviusDeselectManifolds)
	bpy.utils.register_class(VesuviusMeshCleanup)
	bpy.utils.register_class(VesuviusBulkExportPLY)
	bpy.utils.register_class(VesuviusBulkExportOBJ)
	bpy.utils.register_class(VesuviusCreateCoreRadialCameras)

	bpy.utils.register_class(SelectIntersectActive)
	bpy.types.VIEW3D_MT_select_object.append(select_intersect_menu_func)

def unregister():
	bpy.utils.unregister_class(VesuviusPreferences)
	bpy.utils.unregister_class(VesuviusAddScan)
	bpy.types.VIEW3D_MT_add.remove(vesuvius_add_menu_func)
	bpy.utils.unregister_class(VesuviusAddGridCell)
	bpy.utils.unregister_class(VesuviusFocusGridCell)
	bpy.utils.unregister_class(VesuviusImportCellHoles)
	bpy.utils.unregister_class(VesuviusImportLayerHoles)
	bpy.utils.unregister_class(VesuviusImportLayerPatches)
	bpy.utils.unregister_class(VesuviusDownloadGridCells)
	bpy.utils.unregister_class(VesuviusReloadShader)
	bpy.utils.unregister_class(VesuviusRaycastSort)
	bpy.utils.unregister_class(VesuviusSelectClosestByRaycast)
	bpy.utils.unregister_class(VesuviusHideNotDirectlySeenFrom)
	bpy.utils.unregister_class(VesuviusNukeBackfaces)
	bpy.utils.unregister_class(VesuviusSplitHoles)
	bpy.utils.unregister_class(VesuviusSelectA)
	bpy.utils.unregister_class(VesuviusSelectB)
	bpy.utils.unregister_class(VesuviusHideSmall)
	bpy.utils.unregister_class(VesuviusDumpObjectNames)
	bpy.utils.unregister_class(VesuviusWeldScrollTurns)
	bpy.utils.unregister_class(VesuviusDeselectManifolds)
	bpy.utils.unregister_class(VesuviusMeshCleanup)
	bpy.utils.unregister_class(VesuviusBulkExportPLY)
	bpy.utils.unregister_class(VesuviusBulkExportOBJ)
	bpy.utils.unregister_class(VesuviusCreateCoreRadialCameras)

	bpy.utils.unregister_class(SelectIntersectActive)
	bpy.types.VIEW3D_MT_select_object.remove(select_intersect_menu_func)
