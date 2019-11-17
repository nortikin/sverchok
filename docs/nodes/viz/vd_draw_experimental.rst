Viewer Draw MK3
===============

Functionality
-------------

*aliases: vdmk3, viewer draw 3, vd experimental*

This node takes your geometry and displays it in the 3d view, using opengl and shaders. The node is intended to be a fast way to show you the result of your node tree. We've added various levels of refinements that you may find useful to better understand the virtual geometry you've created.

Shader modes
------------

** flat ** 

You can view your geometry as a single flat colour, this requires little to no processing before being passed onto the shader and is lightning fast. This is useful when you are working with large quantities of polygons.

** facetted **

This mode calculates the face normal and angle to a light source, and uses the result to colour the face some shade of the color you set from the UI. This is not a hugely calculation intensive mode, all this data is produced once per update, and reused if you rotate around the viewport. It is only recalculated if the geometry input is changed / or the node is told to reprocess.

** smooth **

The same calculations are performed as in facetted mode, but instead of each face (triangle) being colored uniformly, each face's vertices get a color associated with the vertex normal. This is as close as we will get to smooth shading, at low processing cost.

** custom shader **

If this interests you, you should read the node's source code, and check out the development thread for examples. This is the more experimental part of the node and subject to changing eventually. At present this lets you load a VertexShader and FragmentShader from the bpy.data.texts block.

Features
--------

- You can view Verts on their own, and set their size and colour.
- You can view Edges, set their color and thickness and even apply a configurable Dashed edge style
- You can view Faces, set their color, and infer the associated Edges. The non-flat shader modes require Faces to produce enough information for normals.
- Bake the current mesh(es)
- Set the 3d cursor to the center of Mesh 1. (handy for ratating around in this virtual geometry)
- "Polygon offset" (to prevent z-fighting between edges and faces)
- "quad tessellator", this mode treats all faces as potentially irregular and uses extended mathutils 
to get the normal.
- (experimental..) the "Attribute socket" can be used to configure the viewer node from another node, in this case a dedicated Attributes node.
- can show matrices, if you only connect matrices without any other geometry.

Inputs
------

- Verts
- Edges
- Faces
- Matrix

Support
-------

it's relatively stable, it's been in development on and off for a year, since the first 2.8 releases. But, you will find bugs, let us know. Better yet, suggest fixes (preferably not requiring dedicated hardware) :)


