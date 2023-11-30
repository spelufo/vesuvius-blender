import math
from .utils import *


def radial_dirs(axis, n):
  ref = Vector((1,0,0))
  ez = axis.normalized()
  ey = ez.cross(ref).normalized()
  ex = ey.cross(ez)
  dirs = []
  for i in range(n):
    a = i*math.tau/n
    dirs.append(math.cos(a)*ex + math.sin(a)*ey)
  return dirs

def find_core_point_and_tangent_for_cursor_layer(ctx):
  # TODO: Handle out of bounds and endpoints.
  core = bpy.data.objects["Core"]
  vs = core.data.vertices
  o, i = find_core_point_for_cursor_layer(ctx)
  oprev = core.matrix_world @ vs[i+1].co
  onext = core.matrix_world @ vs[i-1].co
  return o, (onext - oprev).normalized()

def create_core_radial_cameras(ctx, n=8):
  o, axis = find_core_point_and_tangent_for_cursor_layer(ctx)
  for fwd_dir in radial_dirs(axis, n):
    create_camera(o, fwd_dir, axis)
