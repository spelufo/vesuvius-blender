import bpy
import bmesh

# Scroll 1 hardcoded for now.
jz_ranges = [
  (1, 4), (5, 9), (10, 11), (12, 12), (13, 14), (15, 21), (22, 25), (26, 29) ]
jz_ranges_ojs = [
  (8, 5), (8, 4), ( 8,  5), ( 8,  6), ( 8,  7), ( 7,  7), ( 6,  8), ( 6,  9) ]

def stitch_consecutive_half_turns(inner, outer, d=15):
  inner_name = inner.name
  outer_name = outer.name
  print(f"Running stitch_consecutive_half_turns({inner_name}, {outer_name}, d={d}) ...")
  assert {inner_name[7:10], outer_name[7:10]} == {"_h1", "_h2"}, "inner and outer must be different half turns"
  if inner_name > outer_name:
    inner, outer = outer, inner
    inner_name = inner.name
    outer_name = outer.name
  stitch_is_turn_change = inner_name[7:10] == "_h2"

  # Select inner.
  bpy.context.view_layer.objects.active = inner
  bpy.ops.object.select_all(action='DESELECT')
  inner.select_set(True)
  if not inner.vertex_groups:
    inner_vg = inner.vertex_groups.new(name=inner_name)
    for v in inner.data.vertices:
      inner_vg.add([v.index], 1.0, 'ADD')

  # Join onto outer.
  bpy.context.view_layer.objects.active = outer
  outer.select_set(True)
  outer_vg = outer.vertex_groups.new(name=outer_name)
  for v in outer.data.vertices:
    outer_vg.add([v.index], 1.0, 'ADD')

  bpy.ops.object.join()

  inner_vgi = bpy.context.object.vertex_groups[inner_name].index
  outer_vgi = bpy.context.object.vertex_groups[outer_name].index

  # Stitch vertices on the turn (or half-turn) boundary.
  bpy.ops.object.mode_set(mode='EDIT')
  mesh = bpy.context.object.data
  bpy.ops.mesh.select_mode(type='VERT')
  bpy.ops.mesh.select_all(action='DESELECT')
  bm = bmesh.from_edit_mesh(mesh)
  world_matrix = bpy.context.object.matrix_world # It is scale(1/100).
  for (jz_start, jz_end), (ojx, ojy) in zip(jz_ranges, jz_ranges_ojs):
    for vertex in bm.verts:
      # Our meshes have world_matrix that scales their coordinates by 0.01.
      # Their object space is the scan's global voxel space. No translation.
      p = vertex.co
      in_jz_range = (jz_start-1)*500 <= p.z < jz_end*500
      in_jy_range = p.y >= ojy*500 if stitch_is_turn_change else p.y < ojy*500
      in_jx_range = ojx*500 - d/2 < p.x < ojx*500 + d/2
      # The proper, more general way to do this is in blender world space,
      # but with the version above we save on the matrix multiply.
      # p = world_matrix @ vertex.co
      # in_jz_range = (jz_start-1)*5 <= p.z < jz_end*5
      # in_jy_range = p.y >= ojy*5 if stitch_is_turn_change else p.y < ojy*5
      # in_jx_range = ojx*5 - d/100/2 < p.x < ojx*5 + d/100/2
      in_vg = False # Only select vertices from the two current half turns.
      for vg in mesh.vertices[vertex.index].groups:
        if vg.group == inner_vgi or vg.group == outer_vgi:
          in_vg = True
          break
      # TODO: Select and merge the little z plane slits too, when oj steps.
      if in_jz_range and in_jy_range and in_jx_range and in_vg:
        vertex.select = True
    bpy.ops.mesh.remove_doubles(threshold=d)
    bmesh.update_edit_mesh(mesh)

  bpy.ops.object.mode_set(mode='OBJECT')
  return outer


def stitch_turns(turns):
  turns.sort(key=lambda obj: obj.name)
  inner = turns[0]
  for i in range(1, len(turns)):
    inner = stitch_consecutive_half_turns(inner, turns[i])
  return inner

def stitch_turns_selected(ctx):
  turns = [o for o in ctx.selected_objects if o.name.startswith("turn_")]
  return stitch_turns(turns)


