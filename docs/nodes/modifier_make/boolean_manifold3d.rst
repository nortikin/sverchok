Manifold Boolean
================

.. TODO: node screenshot here

Functionality
-------------

This node performs boolean operations (Intersect, Union, Difference) on two meshes using the external `manifold3d <https://github.com/elalish/manifold>`_ library. Manifold is fast and robust: it guarantees a manifold result whenever the inputs are manifold, and it does not create Blender objects or modifiers to do its work. Blender's own *Manifold* boolean solver is built on the same library.

It lives alongside the :doc:`Boolean Internal </nodes/modifier_make/boolean_internal>` node rather than replacing it, and is offered as the less fragile option.

Dependencies
------------

The node needs the ``manifold3d`` Python package. Without it the node shows **manifold3d not found!** and outputs empty lists. To install it, run this in Blender's Python console and then restart Blender::

    from sverchok.utils.pip_utils import install_package
    install_package("manifold3d")

Inputs
------

- **Verts A**, **Polys A** - the first mesh.
- **Verts B**, **Polys B** - the second mesh.
- **Verts Nested**, **Polys Nested** - a list of meshes, only shown when *Accumulate Nested* is on (the A and B sockets are hidden then).

Polygons may be triangles, quads or n-gons, including concave ones; they are triangulated before the boolean. Lists of objects are matched by repeating the last item of the shorter list, as in most Sverchok nodes.

Parameters
----------

- **Intersect / Union / Difference** - the boolean operation. Difference is ``A - B``.
- **Accumulate Nested** - boolean the first two meshes of the nested input, then apply the same operation between that result and each following mesh, one by one.
- **Only Final Result** - (only with *Accumulate Nested*) output just the last result. When off, the result of every step is output, which is handy for seeing how the shape builds up.
- **Allow Ngons** - Manifold returns triangles only. With this on, adjacent faces that are (nearly) coplanar are merged back into n-gons. On by default.
- **Angle Limit** - (only with *Allow Ngons*) the largest angle, in degrees, between two face normals for the faces to still count as coplanar. Default 0.1, range 0 - 5.
- **Track Origins** - fill the *Face Origins* and *Cut Edges* outputs. Off by default.

Outputs
-------

- **Vertices**
- **Polygons**
- **Face Origins** - one integer per polygon: ``0`` when the face came from mesh A, ``1`` when it came from mesh B, ``-1`` if it couldn't be traced. Useful for giving the two parts different materials or colours, or for selecting just the faces left behind by the cutter. Empty unless *Track Origins* is on.
- **Cut Edges** - the edges along which faces from A meet faces from B, that is the intersection curves of the boolean. Use them with *Vertices* to bevel or highlight the seam. Empty unless *Track Origins* is on.

With *Track Origins* and *Allow Ngons* both on, only faces with the same origin are merged, so *Face Origins* stays correct and the cut edges are kept.

Input requirements
------------------

Manifold is strict about what it accepts, and this is what makes it reliable.

- Each input mesh must be closed (watertight) and manifold: every edge shared by exactly two faces, no holes, no loose geometry.
- Face normals should point outward.
- A mesh that does not qualify is turned into an *empty* manifold, so the result is empty or just the other mesh. If that happens, check the input; a **Merge by Distance** node before this one often fixes meshes with duplicate vertices along their seams.

Unlike :doc:`CSG Boolean MK2 </nodes/modifier_make/csg_booleanMK2>`, coplanar faces and touching or overlapping surfaces between A and B are handled cleanly.

Vertex positions are passed to Manifold in single precision (32-bit float). This is fine at ordinary scene scales, but very large coordinates with very small details may lose some accuracy.

Examples
--------

.. TODO: example screenshot here

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk5>`

Alternatives
------------

- :doc:`Boolean Internal </nodes/modifier_make/boolean_internal>` - uses Blender's own Boolean modifier.
- :doc:`CSG Boolean MK2 </nodes/modifier_make/csg_booleanMK2>` - pure Python, no dependencies, slower and fussier about input.
- :doc:`Solid Boolean </nodes/solid/solid_boolean>` - for FreeCAD solids.
