# Segmentation

## Vertical-radial plane subdivision method

1. Choose a cell.
2. Choose a ZR plane that cuts through the cell and make quad there.
  Easier to work with world axis aligned plane in ortho view, but might
  not be feasible in some places where the scroll tangent is near 45 degrees.
3. In edit mode use Ctrl-R scroll to subdivide the quad with horizontal edges.
4. Repeatedly:
  a. Ctrl-R to cut vertically.
  b. Adjust the new points of to lie between sheets (in the black where possible). 

Do this in order from the sides, or starting from where the separation is
clearest, until the whole quad is subdivided.

Pay attention to the bright rectangles that are the cross section of the bands
that run horizontally along the papyrus sheet. There are easy to identify and
we know they lie on the front/recto of the sheets, facing the core of the roll.

In some places, where new sheets arise or disappear you might have to add edge
loops that don't run the full vertical span of the quad. In these cases the
knife tool, or the merge by distance tool can be helpful.

