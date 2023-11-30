import bpy
import bmesh

def partition_into_layers(mesh, zstep=10):
	for z in [50, 60, 70, 80, 90, 100, 110, 120]:
		bpy.ops.mesh.select_all(action='SELECT')
		bpy.ops.mesh.bisect(plane_co=(0, 0, z), plane_no=(0, 0, 1))
		bpy.ops.mesh.edge_split(type='EDGE')
	bpy.ops.mesh.separate(type='LOOSE')
