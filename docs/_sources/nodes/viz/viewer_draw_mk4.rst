Viewer Draw
============

.. image:: https://user-images.githubusercontent.com/14288520/189978461-92a31395-6702-4623-8904-952b96f4d8d3.png
  :target: https://user-images.githubusercontent.com/14288520/189978461-92a31395-6702-4623-8904-952b96f4d8d3.png

.. image:: https://user-images.githubusercontent.com/14288520/201473680-b993c305-99b4-4eea-8af4-93baf8a7329b.png
  :target: https://user-images.githubusercontent.com/14288520/201473680-b993c305-99b4-4eea-8af4-93baf8a7329b.png

Functionality
-------------

*aliases: vdmk4, viewer draw 4*

This node takes your geometry and displays it in the 3d view, using opengl and shaders. The node is intended to be a fast way to show you the result of your node tree. We've added various levels of refinements that you may find useful to better understand the virtual geometry you've created.

Shader modes
------------

.. image:: https://user-images.githubusercontent.com/14288520/189981449-d635a6ff-1cff-44cf-b006-6ce2eee4b8bf.png
  :target: https://user-images.githubusercontent.com/14288520/189981449-d635a6ff-1cff-44cf-b006-6ce2eee4b8bf.png

**flat**

You can view your geometry as a single flat colour, this requires little to no processing before being passed onto the shader and is lightning fast. This is useful when you are working with large quantities of polygons.

**facetted**

This mode calculates the face normal and angle to a light source, and uses the result to colour the face some shade of the color you set from the UI. This is not a hugely calculation intensive mode, all this data is produced once per update, and reused if you rotate around the viewport. It is only recalculated if the geometry input is changed / or the node is told to reprocess.

**smooth**

The same calculations are performed as in facetted mode, but instead of each face (triangle) being colored uniformly, each face's vertices get a color associated with the vertex normal. This is as close as we will get to smooth shading, at low processing cost.

**custom shader**

If this interests you, you should read the node's source code, and check out the development thread for examples. This is the more experimental part of the node and subject to changing eventually. At present this lets you load a VertexShader and FragmentShader from the bpy.data.texts block.

Features
--------

- You can view Verts on their own, and set their size and color. Color can be set by vertex or by object, also can generate random colors in one click.
- You can view Edges, set their color and thickness and even apply a configurable Dashed edge style. Color can be set by edge or by object, also can use vertex colors to color edges.
- You can view Faces, set their color, and infer the associated Edges. The non-flat shader modes require Faces to produce enough information for normals. Color can be set by polygon or by mesh, also can use vertex colors to color edges.
- Bake the current mesh(es)
- Set the 3d cursor to the center of Mesh 1. (handy for rotating around in this virtual geometry)
- "Polygon offset" (to prevent z-fighting between edges and faces), on by default.
- "quad tessellator", this mode treats all faces as potentially irregular and uses extended mathutils to get the normal.
- can show matrices if you only connect matrices without any other geometry. Size can be defined in the N-Panel or in the right click menu
- alpha channel, the color socket is rgba.
  - multiple simultaneous viewers mixing opaque geometry may show render artifacts. 
- (experimental..) the "Attribute socket" can be used to configure the viewer node from another node, in this case a dedicated Attributes node.

.. image:: https://user-images.githubusercontent.com/14288520/189983532-9bdaf0ed-0534-4221-af20-d334c1e34ae5.png
  :target: https://user-images.githubusercontent.com/14288520/189983532-9bdaf0ed-0534-4221-af20-d334c1e34ae5.png

Inputs
------

- Vertices
- Edges
- Faces
- Matrix
- Vertices color
- Edges color
- Faces color
- attrs: Attributes socket

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/189978522-5ed5ab57-3746-4816-ad37-b7b452d3c044.png
  :target: https://user-images.githubusercontent.com/14288520/189978522-5ed5ab57-3746-4816-ad37-b7b452d3c044.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/189978588-76ec34b1-885b-44de-bf37-5adb77d2627d.png
  :target: https://user-images.githubusercontent.com/14288520/189978588-76ec34b1-885b-44de-bf37-5adb77d2627d.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/189979120-63ecdaa7-2883-44a4-88b7-8fbe2a2f84fb.png
  :target: https://user-images.githubusercontent.com/14288520/189979120-63ecdaa7-2883-44a4-88b7-8fbe2a2f84fb.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`

---------

Extra params:

.. image:: https://user-images.githubusercontent.com/14288520/189985713-e3f503fb-3d54-482f-bb16-648660eed55f.gif
  :target: https://user-images.githubusercontent.com/14288520/189985713-e3f503fb-3d54-482f-bb16-648660eed55f.gif

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Analyzers-> :doc:`Component Analyzer </nodes/analyzer/component_analyzer>`

Support
-------

it's relatively stable, it's been in development on and off for a year, since the first 2.8 releases. But, you will find bugs, let us know. Better yet, suggest fixes (preferably not requiring dedicated hardware) :)
