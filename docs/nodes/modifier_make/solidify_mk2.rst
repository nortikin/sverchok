Solidify
========

Extrudes a mesh along its normal. Used usually to get a thick mesh from a planar mesh.

Inputs
------


**Vertices**: Mesh Vertices (mandatory)

**Edges**: Mesh Edges (optional, if you want to output edges makes the algorithm faster)

**Polygons**: Mesh Polygons (mandatory)

**Thickness**: Distance to extrude

**Offset**: Relative offset from original mesh

Options
-------

**Even**: adjust thickness in sharp corners to have a even thickness.

**Implementation**: Algorithm used to compute.
  - Sverchok: Faster all with more options
  - Blender: Old method, left because it may differ in some corner cases

Outputs
-------

**Vertices**, **Edges**, **Polygons**: Modified mesh

**New Pols**: New opposite polygons (in the same order as the originals)

**Rim Pols**: Side Polygons created in the boundaries of the mesh

**Pols Group**: Outputs a list to mask polygons from the modified mesh,
  0 = Original Polygon
  1 = New Polygon
  2 = Rim Polygon

**New Verts Mask**: To split old vertices form new vertices


Examples
--------

Using variable thickness:

.. image:: https://user-images.githubusercontent.com/10011941/105902112-80bbaa80-601e-11eb-902b-5bd3797f257d.png


Splitting Data: New Vertices in white, Old vertices in black, New Polys in grey, Rim Polys in white...

.. image:: https://user-images.githubusercontent.com/10011941/106249827-1fa8f800-6213-11eb-9e77-770f12d65e03.png
