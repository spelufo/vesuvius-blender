# How to model a sheet

## Setup

Choose a region of the scroll and set the grid cell bounds in the material
shader. A 2^3 cells (1000^3 voxels) region is good. Download those cell tiffs
from the server. Make two planes of 10^2 blender meters positioned in at those
coordinates, assign them the vesuvius_scan material and verify they show the
cells at full definition. A black and white gradient means you are in the right
location but the tif files where not found.

<img src="images/grid_bounds.png">

Position the horizontal plane at the lower extreme of the region, offset a
little bit (e.g. 0.01m) in the z direction or it will show the low res texture.

## Initial steps

The first layer takes a bit of work:

1. Place the 3d cursor on that plane and create a new plane for the surface of the
sheet.
2. Go into Edit Mode. Delete all vertices except one. Select it, turn on snapping
to "Face project" with the magnet button in the upper toolbar. This will make the
vertices we edit lie on the horizontal reference plane.
3. Hit `E` to extrude the vertex. Repeat this all along the line where the sheet
you pick shows on the reference plane.

## For each subsequent layer

We build up the sheet one layer at a time, spaced at 0.5m (50 voxels) in z.
This [video](https://www.youtube.com/watch?v=TdPzqBzCfqw) shows the process.

1. In object mode, select the horizontal reference plane. Hit `G`, `Z`, `.5`,
`enter`, to move the plane up.
2. Select the sheet again, and go into edit mode. Hit `2` for edge mode. Select
the last layer's edges with `alt+click`. `E`, `Z`, `.5` to extrude it in z.
3. You can move it in XY to try to align as much of the vertices at once as you
can.
4. Turn on snapping and the poly build tool. Looking from below, adjust each
vertex in the reference plane until the faces that are formed show the texture
of the sheet.
5. When done with a layer, rinse and repeat.



