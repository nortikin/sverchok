Object ID Out MK2
==================

Functionality
-------------
This node takes any object or list of objects presented in the scene and return
mesh data of this object or objects. Take a note, that global transformations of
objects is not count, so all information will be represent as if objects were placed in
(0,0,0) location, has (1,1,1) scale and (0,0,0) rotation.

Inputs
------
**Object** - object or list of objects. If no input connected, you can choose one
object from the scene using drop-down list.

Parameters
----------
**Post modifiers** - when checked, if object has any modifiers, mesh data will be
returned with all modifiers applied.

Outputs
-------

**Vertices** - object vertices locations.

**VertexNormals** - object vertices normals.

**Edges** - object edges.

**Polygons** - object polygons.

**PolygonAreas** - areas of object polygons.

**PolygonCenters** - centers of object polygons.

**PolygonNormals** - normals of objects polygons.

**Matrices** - matrix of object. Use this output in pair with any other output
to get actual position, scale and rotation of input object.

Example of usage
----------------
