import bpy, bmesh
from pathlib import Path

from . import data
from .shaders import *  # noqa
from .utils import *  # noqa

ADDON_ID = "vesuvius"

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
		if not data.get_data_dir().is_dir():
			self.report({"ERROR"}, "Vesuvius data directory not found.")
			return {"CANCELLED"}
		scan = data.SCANS.get(self.scan_name)
		if not scan:
			self.report({"ERROR"}, f"Scan {repr(self.scan_name)} not found.")
			return {"CANCELLED"}
		self.report({"INFO"}, f"Requested {scan.small_volume_path}.")
		data.download_file_start(scan, scan.small_volume_path, context)
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

		obj = bpy.context.active_object

		if not bpy.context.selected_objects or not obj or obj.type != 'MESH':
			return {"CANCELLED"}

		# If there's more than one pick the last one. If the active object has a
		# vesuvius_volpkg_ material assigned, use that.
		vol_id = ""
		matname_prefix = "vesuvius_volpkg_"
		for mat in bpy.data.materials:
			if mat.name.startswith(matname_prefix):
				vol_id = mat.name.replace(matname_prefix, "")
		for mat in obj.data.materials:
			if mat.name.startswith(matname_prefix):
				vol_id = mat.name.replace(matname_prefix, "")

		scan = next(filter(lambda s: s.vol_id == vol_id, data.SCANS.values()), None)
		if not scan:
			self.report({"ERROR"}, f"Scan with vol_id '{vol_id}' not found.")
			return {"CANCELLED"}

		# TODO: It makes more sense to use the bounding box since the shader
		# already expects it to be a rectangular region.
		# TODO: Set the material's MinJ and MaxJ.

		vertices = [v.co for v in obj.data.vertices if v.select]
		vertices = vertices or [v.co for v in obj.data.vertices]
		cells = {
			(int(v.x//5), int(v.y//5), int(v.z//5))
			for v in vertices
			if  0 <= v.x < scan.width/100
			and 0 <= v.y < scan.height/100
			and 0 <= v.z < scan.slices/100
		}
		if not cells:
			self.report({"ERROR"}, f"No cells overlapping geometry.")
			return {"CANCELLED"}

		# TODO: This check is a bit lame, but for now let's prevent downloading too
		# many cells at once.
		if len(cells) > 12:
			self.report({"ERROR"}, f"Too many cells ({len(cells)}) overlapping geometry.")
			return {"CANCELLED"}

		for cell in cells:
			cell_path = scan.grid_cell_path(*cell)
			self.report({"INFO"}, f"Requested {cell_path}.")
			data.download_file_start(scan, cell_path, context)

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

