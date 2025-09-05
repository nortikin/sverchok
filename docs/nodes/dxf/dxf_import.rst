DXF import
==========


Functionality
-------------
Bring polylines to dxf as inner sverchok dxf object


Inputs
------

- **Filepath** - Path to file to be imported


Outputs
-------

- **vers_e** - edge's vertices
- **edgs** - edges
- **vers_p** - polygon's vertices
- **pols** - polygons
- **vers_annot** - annotations vertices
- **edges_annot** - annotations edges
- **vers_text** - text positions
- **text** - texts
- **curves** - bezier curves
- **knots** - knots of curves

Parameters
----------

- **Import DXF** - Button to import file as Sverchok data
- **curve_type** - type of curve in Sverchok. Default Geomdl
- **scale** - overall scale of drawing. Default 1.0
- **resolution for arcs** - resolution for arcs, cicrles, ovals. Default 10


N panel
-------

None

Examples
--------

None
