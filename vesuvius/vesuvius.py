import bpy, bmesh
from pathlib import Path

from .data import *  # noqa
from .shaders import *  # noqa
from .utils import *  # noqa

ADDON_ID = "vesuvius"

_current_scan = None
def get_current_scan():
	global _current_scan
	if _current_scan:
		return _current_scan
	vol_id = ""
	for mat in bpy.data.materials:
		if mat.name.startswith("vesuvius_volpkg_"):
			vol_id = mat.name.removeprefix("vesuvius_volpkg_")
	if not vol_id:
		return None
	for scan in SCANS.values():
		if scan.vol_id == vol_id:
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


def setup_geometry(scan, material):
	dx, dy, dz = scan.width/100, scan.height/100, scan.slices/100
	plane_xy = create_quad((0, 0, 0), (dx, 0, 0), (dx, dy, 0), (0, dy, 0), "PlaneXY")
	plane_yz = create_quad((0, 0, 0), (0, dy, 0), (0, dy, dz), (0, 0, dz), "PlaneYZ")
	plane_zx = create_quad((0, 0, 0), (0, 0, dz), (dx, 0, dz), (dx, 0, 0), "PlaneZX")
	plane_xy.data.materials.append(material)
	plane_yz.data.materials.append(material)
	plane_zx.data.materials.append(material)
	plane_yz.location.x += dx/2
	plane_zx.location.y += dy/2


class VesuviusAddScan(bpy.types.Operator):
	bl_idname = "object.vesuvius_add_scan"
	bl_label = "Vesuvius Scan"

	scan_name: bpy.props.EnumProperty(
		items=[(x,x,x) for x in [
			"scroll_1_54",
			"scroll_2_54",
			"scroll_2_88",
			"fragment_1_54",
			"fragment_1_88",
			"fragment_2_54",
			"fragment_2_88",
			"fragment_3_54",
			"fragment_3_88",
		]],
		name="Scan",
		description="Select the scan to add",
		default='scroll_1_54',
	)

	def execute(self, context):
		if not get_data_dir().is_dir():
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
		setup_geometry(scan, material)
		return {"FINISHED"}


def menu_func(self, context):
	self.layout.operator_menu_enum(VesuviusAddScan.bl_idname, "scan_name")



class VesuviusDownloadGridCells(bpy.types.Operator):
	bl_idname = "object.vesuvius_download_grid_cells"
	bl_label = "Download grid cells"

	def execute(self, context):
		if not data.get_data_dir().is_dir():
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

		cell_path = scan.grid_cell_path(*cell)
		self.report({"INFO"}, f"Requested {cell_path}.")
		download_file_start(scan, cell_path, context)

		# TODO: Set the material's MinJ and MaxJ.
		self.report({"INFO"}, f"Cell: {cell}.")
		return {"FINISHED"}


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
	bpy.types.VIEW3D_MT_add.append(menu_func)
	bpy.utils.register_class(VesuviusDownloadGridCells)


def unregister():
	bpy.utils.unregister_class(VesuviusPreferences)
	bpy.utils.unregister_class(VesuviusAddScan)
	bpy.types.VIEW3D_MT_add.remove(menu_func)
	bpy.utils.unregister_class(VesuviusDownloadGridCells)

