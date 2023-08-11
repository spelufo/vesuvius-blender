import bpy, bmesh

from .data import *  # noqa
from .shaders import *  # noqa
from .utils import *  # noqa

ADDON_ID = "vesuvius"

def setup_scene(preferences, scene):
	scene.render.engine = "CYCLES"
	scene.cycles.shading_system = True
	scene.cycles.preview_samples = preferences.get('cycles_preview_samples', 1)


def setup_material(preferences, scan):
	material = get_or_create(bpy.data.materials, f"vesuvius_volpkg_{scan.vol_id}")
	material.use_nodes = True
	node_tree = material.node_tree
	node_tree.nodes.clear()

	script_text = get_or_create(bpy.data.texts, f"vesuvius_shader_{scan.vol_id}")
	script_text.from_string(generate_shader(preferences, scan))

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


def setup_geometry(preferences, scan, material):
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
		preferences = context.preferences
		addon_prefs = preferences.addons[ADDON_ID].preferences
		scan = SCANS[self.scan_name]
		setup_scene(addon_prefs, context.scene)
		material = setup_material(addon_prefs, scan)
		setup_geometry(addon_prefs, scan, material)
		return {"FINISHED"}


def menu_func(self, context):
	self.layout.operator_menu_enum(VesuviusAddScan.bl_idname, "scan_name")


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


def unregister():
	bpy.utils.unregister_class(VesuviusPreferences)
	bpy.utils.unregister_class(VesuviusAddScan)
	bpy.types.VIEW3D_MT_add.remove(menu_func)

