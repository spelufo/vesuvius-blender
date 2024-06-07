import gc
import bpy
import bmesh

# Scroll 1 hardcoded for now.
jz_ranges = [
  (1, 4), (5, 9), (10, 11), (12, 12), (13, 14), (15, 21), (22, 25), (26, 29) ]
jz_ranges_ojs = [
  (8, 5), (8, 4), ( 8,  5), ( 8,  6), ( 8,  7), ( 7,  7), ( 6,  8), ( 6,  9) ]

def next_half_turn_name(inner_name):
  turns, turn, half = inner_name.split("_")
  if half == "h1":
    return f"{turns}_{turn}_h2"
  elif half == "h2":
    next_turn = int(turn)+1
    return f"{turns}_{next_turn:02d}_h1"
  else:
    assert False, f"bad half turn name {inner_name}"

def weld_consecutive_half_turns(ctx, inner_object, outer_object, d=2):
  inner_object_name = inner_object.name
  outer_object_name = outer_object.name
  if inner_object_name > outer_object_name:
    inner_object, outer_object = outer_object, inner_object
    inner_object_name = inner_object.name
    outer_object_name = outer_object.name

  # Create half turn vertex groups or ensure the right ones exist and join objs.
  # Welding joins inner_object into outer_object, so a welded object is named
  # after it's last half turn.
  inner_name = inner_object_name
  outer_name = next_half_turn_name(inner_name)
  ctx.view_layer.objects.active = inner_object
  if inner_name not in inner_object.vertex_groups:
    assert len(inner_object.vertex_groups) == 0, "bad inner object vertex groups"
    inner_vg = inner_object.vertex_groups.new(name=inner_name)
    inner_vg.add([v.index for v in inner_object.data.vertices], 1.0, 'ADD')
  ctx.view_layer.objects.active = outer_object
  if outer_name not in outer_object.vertex_groups:
    assert len(outer_object.vertex_groups) == 0, "bad outer object vertex groups"
    outer_vg = outer_object.vertex_groups.new(name=outer_name)
    outer_vg.add([v.index for v in outer_object.data.vertices], 1.0, 'ADD')

  bpy.ops.object.select_all(action='DESELECT')
  inner_object.select_set(True)
  outer_object.select_set(True)
  bpy.ops.object.join()
  merged_object = ctx.active_object
  ctx.view_layer.objects.active = merged_object

  # Weld vertices on the turn (or half-turn) boundary.
  mesh = ctx.object.data
  weld_is_turn_change = inner_name[7:10] == "_h2"
  weld_name = f"weld_{inner_name}_{outer_name}"
  weld_vg = merged_object.vertex_groups.new(name=weld_name)
  inner_vg = ctx.object.vertex_groups[inner_name]
  outer_vg = ctx.object.vertex_groups[outer_name]
  inner_vgi = inner_vg.index
  outer_vgi = outer_vg.index
  weld_verts = []
  for vertex in merged_object.data.vertices:
    ojs_prev = None
    for (jz_start, jz_end), (ojx, ojy) in zip(jz_ranges, jz_ranges_ojs):
      # Only select vertices from the two current half turns.
      in_vg = False
      for vg in mesh.vertices[vertex.index].groups:
        if vg.group == inner_vgi or vg.group == outer_vgi:
          in_vg = True
          break
      if not in_vg:
        continue
      # A more general way to do this is in blender world space, but with the
      # object space version below we save on the matrix multiply. We would do
      # `p = world_matrix @ vertex.co` and change 500 -> 5, etc.
      p = vertex.co
      in_jz_range = (jz_start-1)*500 <= p.z < jz_end*500
      in_jy_range = p.y >= ojy*500 if weld_is_turn_change else p.y < ojy*500
      in_jx_range = ojx*500 - d/2 < p.x < ojx*500 + d/2
      # Select the vertices on the jzs half turn boundary (vertical sections).
      if in_jz_range and in_jy_range and in_jx_range and in_vg:
        weld_verts.append(vertex.index)
      # Select the vertices in between jz groups on the half turn boundary (horizontal sections).
      if ojs_prev is not None:
        pojx, pojy = ojs_prev
        mojy = (pojy+ojy)/2
        in_jz_range = (jz_start-1)*500 - d/2 < p.z < (jz_start-1)*500 + d/2
        in_jy_range = p.y >= mojy*500 if weld_is_turn_change else p.y < mojy*500
        in_jx_range = min(pojx, ojx)*500 <= p.x < max(pojx, ojx)*500
        if in_jz_range and in_jy_range and in_jx_range and in_vg:
          weld_verts.append(vertex.index)
      ojs_prev = (ojx, ojy)
  weld_vg.add(weld_verts, 1.0, 'ADD')
  weld_mod = merged_object.modifiers.new(name="Weld", type='WELD')
  weld_mod.merge_threshold = d
  weld_mod.vertex_group = weld_name
  weld_mod.mode = 'ALL'
  bpy.ops.object.mode_set(mode='OBJECT')
  bpy.ops.object.modifier_apply(modifier=weld_mod.name)
  return merged_object, 'FINISHED'

def weld_turns(ctx, turns):
  status = 'FINISHED'
  if len(turns) == 0:
    return {status}
  turns.sort(key=lambda obj: obj.name)
  inner_object = turns[0]
  for i in range(1, len(turns)):
    inner_object, status = weld_consecutive_half_turns(ctx, inner_object, turns[i])
    if status != 'FINISHED':
      break
  bpy.ops.object.mode_set(mode='EDIT')
  bpy.ops.mesh.select_mode(type="VERT")
  # remove_vertices_until_manifold(ctx)
  # Save a few keystrokes: select non-manifold just so we can quickly go back
  # into edit mode and check if there are any left.
  bpy.ops.mesh.select_non_manifold(extend=False, use_boundary=False)
  bpy.ops.object.mode_set(mode='OBJECT')
  return {status}

def weld_turns_selected(ctx):
  turns = [o for o in ctx.selected_objects if o.name.startswith("turn_")]
  return weld_turns(ctx, turns)

# Mesh Cleanup

def deselect_manifolds(ctx):
  objs = ctx.selected_objects
  non_manifolds = []
  for obj in objs:
    print(f"Checking {obj.name}...")
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    ctx.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_non_manifold(extend=False, use_boundary=False)
    if obj.data.total_vert_sel > 0:
      non_manifolds.append(obj)
    bpy.ops.object.mode_set(mode='OBJECT')
  bpy.ops.object.select_all(action='DESELECT')
  for obj in objs:
    if obj in non_manifolds:
      obj.select_set(True)
      ctx.view_layer.objects.active = obj

def mesh_cleanup(ctx):
  objs = ctx.selected_objects
  for obj in objs:
    print(f"Cleaning {obj.name}...")
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    ctx.view_layer.objects.active = obj
    mesh_cleanup_object(ctx, obj)

def mesh_cleanup_object(ctx, obj):
  bpy.ops.object.mode_set(mode='EDIT')
  remove_vertices_until_manifold(ctx, obj)
  clip_ear_triangles(ctx, obj)
  bpy.ops.mesh.select_non_manifold(extend=False, use_boundary=True)
  bpy.ops.mesh.fill_holes(sides=1000)
  bpy.ops.mesh.quads_convert_to_tris()
  bpy.ops.object.mode_set(mode='OBJECT')

def remove_vertices_until_manifold(ctx, obj, max_iter=100):
  for i in range(max_iter):
    bpy.ops.mesh.select_non_manifold(use_boundary=False, extend=False)
    if obj.data.total_vert_sel == 0:
      break
    if i == max_iter-1 and obj.data.total_vert_sel > 0:
      assert False, "max_iter reached with non-manifold vertices"
    bpy.ops.mesh.delete(type='VERT')

def clip_ear_triangles(ctx, obj):
  bpy.ops.mesh.select_mode(type="VERT")
  bm = bmesh.from_edit_mesh(obj.data)
  for v in bm.verts:
    if v.is_boundary and len(v.link_edges) == 2:
      e1, e2 = v.link_edges
      if e1.is_boundary and e2.is_boundary:
        if len(set(e1.link_faces) & set(e2.link_faces)) == 1:
          if len(e1.link_faces[0].edges) == 3:
            v.select = True
  bm.select_flush(True)
  bpy.ops.mesh.delete(type='VERT')
