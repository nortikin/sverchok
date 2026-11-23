Hatch Pattern
=============

.. image:: https://github.com/user-attachments/assets/a00f6599-af84-4870-9d01-11c6fd8da2ca
  :target: https://github.com/user-attachments/assets/a00f6599-af84-4870-9d01-11c6fd8da2ca

Readers familiar with hatching and ``.pat`` files can skip this intro and go on to the next section.

Hatches are a classic way to use line-art to tell more about the materials in (and on) modelled structures. They are useful when a drawing has to convey clearly the build-up of materials in walls, floors, roofs and foundations. Hatches sidestep the problem of trying to render materials photorealistically when the medium is a 2D drawing. Current CAD and Revit software still use industry-standard hatch patterns inherited from the time when drawings were done by hand and photorealism was not practical.

.pat files
----------

This node reads a ``.pat`` file and fills a boundary mesh (irregular shapes, holes allowed) with the chosen hatch pattern, output as renderable ``verts + edges``. Settings let you scale the pattern and offset its origin.

The node comes with a companion web tool, `HatchTool <https://zeffii.github.io/HatchTool/>`_, that lets you quickly flip through a list of ``.pat`` files to find a suitable hatch style. Its editor also lets you modify a hatch and save it to disk. Please report any issues with HatchTool to `its own repo <https://github.com/zeffii/HatchTool>`_, not here.

How does it work?
-----------------

The node detects the plane of the boundary mesh and repeats the hatch pattern across that plane, limited to the area inside the boundary. Users familiar with Revit or AutoCAD will appreciate this, and it should help with producing drawings for manufacturing.

A few details:

- **Plane** - with *Polygons* the facing follows the winding of the largest polygon, like a Blender face normal. With only *Edges* (which carry no winding) a best-fit plane is used, facing up (else +Y, else +X).
- **Pattern origin** - the point of the plane closest to the world origin. Regions on the same plane therefore share one continuous hatch, and lines run on across neighbouring regions instead of restarting in each one.
- **Pattern axes** - on (near) horizontal planes the pattern's X follows world X. On walls and roof slopes the pattern's Y runs up the slope and X runs level.
- **Holes** - inside is decided by the even-odd rule, so a loop inside another loop is a hole; no special treatment needed.

Getting a .pat file in
----------------------

The pattern is read from a Blender text block. In the Text Editor, open a ``.pat`` file (or paste its contents), then pick that text block in the node. The dropdown below it lists every pattern in the file. Patterns are parsed once and re-parsed only when the text changes.

Inputs
------

One stream per object:

- **Vertices** - the boundary vertices.
- **Edges** - boundary given as edges. Every vertex must be shared by an even number of edges (closed boundaries); otherwise the node reports where the boundary is open.
- **Polygons** - boundary given as polygons, including polygons with holes. Polygons win when both Edges and Polygons are connected. With neither, the vertices form one loop in order.
- **Scale** - multiplies the ``.pat`` values. Default 1.0.
- **Offset X**, **Offset Y** - shift the pattern along the plane's X and Y axes.

Scale and the offsets take one value per object.

Outputs
-------

- **Vertices**, **Edges** - every dash as a separate edge, ready to view or bake.
- **Dots** - the dots of patterns that have zero-length dashes.
- **Stroke Vertices**, **Stroke Edges** - dashes that join end to end chained into polylines, one object per stroke. Handy for plotting.
- **Plane** - a matrix per object for the detected plane (pattern origin and axes).

Settings in the N-panel
-----------------------

- **Min Length** - drop dashes shorter than this (e.g. the pen width); clipping at the boundary can leave tiny slivers.
- **Order Strokes** - sort strokes nearest-first to cut pen travel when plotting. On by default.
- **Max Segments** - stop with an error rather than produce more dashes than this per region. Protects Blender from a scale that is far too small. Default 1,000,000.

Status line
-----------

Under the pattern dropdown the node reports the number of dashes, dots and objects. When the result looks wrong it says so: when nothing lands inside the region, or the lines are further apart than the region is wide, it suggests a scale. If the ``.pat`` file declares its units (e.g. mm) while Scale is 1, it points out the factor for metres.

Examples
--------

.. TODO: example screenshot here

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk5>`
