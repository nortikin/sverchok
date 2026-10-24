Viewer Draw
============

.. image:: https://github.com/user-attachments/assets/a2453dee-d147-4311-8e9d-263b523e864f
  :target: https://github.com/user-attachments/assets/a2453dee-d147-4311-8e9d-263b523e864f

.. image:: https://github.com/user-attachments/assets/2ec88406-8eea-4dc0-8a13-27068e89ec8f
  :target: https://github.com/user-attachments/assets/2ec88406-8eea-4dc0-8a13-27068e89ec8f

Functionality
-------------

*aliases: vdmk5, viewer draw 5*

This node takes your geometry and displays it in the 3d view, using the gpu module and shaders. The node is intended to be a fast way to show you the result of your node tree. We've added various levels of refinements that you may find useful to better understand the virtual geometry you've created.

Mk5 does the same job as Mk4, rewritten for Blender's current drawing backends (OpenGL, Metal and Vulkan). Shaders are compiled once and the geometry is uploaded to the GPU once per update, so rotating around the viewport costs next to nothing. Old Mk4 nodes can be upgraded, their settings carry over.

Shader modes
------------

.. image:: https://user-images.githubusercontent.com/14288520/189981449-d635a6ff-1cff-44cf-b006-6ce2eee4b8bf.png
  :target: https://user-images.githubusercontent.com/14288520/189981449-d635a6ff-1cff-44cf-b006-6ce2eee4b8bf.png

**flat**

You can view your geometry as a single flat colour, this requires little to no processing before being passed onto the shader and is lightning fast. This is useful when you are working with large quantities of polygons.

**facet**

Each face is shaded by the angle between its normal and the light direction (set in the N-Panel), using the colour you set from the UI. The shading is done per pixel on the GPU, faces don't need to be split up or have normals calculated beforehand, so this mode is nearly as fast as flat. Faces are lit from both sides.

**smooth**

Like facet, but using vertex normals interpolated across each face, plus a subtle highlight. This is as close as we will get to smooth shading, at low processing cost. The vertex normals are calculated once per update.

**normals**

Colours each face by its normal direction (x, y, z mapped to r, g, b). Handy for checking the orientation of your faces. This replaces the default view of Mk4's fragment mode.

**custom**

If this interests you, you should read the node's source code, the docstring at the top explains the details. This is the more experimental part of the node. Pick a text block from bpy.data.texts, it is executed and may define:

- ``build_shader()``, returning a gpu shader (preferred)
- ``shader_info``, a ``gpu.types.GPUShaderCreateInfo``
- ``vertex_shader`` and ``fragment_shader``, GLSL strings in the old Mk4 style
- ``draw_fragment(context, shader, geom)``, optional, called after the shader is bound, use it to set your own uniforms

The shader can declare the vertex attributes ``position`` (or ``pos``), ``color`` and ``normal`` (or ``nrm``), and they are supplied automatically. ``viewProjectionMatrix`` is set for you if declared. If the shader fails to compile the node falls back to the normals view and prints the error in the console.

Face Culling
------------

Blender: https://docs.blender.org/api/current/gpu.state.html#gpu.state.face_culling_set

wiki: https://wikis.khronos.org/opengl/Face_Culling

Used only in Blender 3D Viewport. Has no influence for render or baking mesh, edges or vertices.

**None** - default. Show all faces

**Front** - hide front faces

**Back** - hide back faces

.. image:: https://github.com/user-attachments/assets/a1315dea-5b22-4d24-b671-0810add0c005
  :target: https://github.com/user-attachments/assets/a1315dea-5b22-4d24-b671-0810add0c005

Features
--------

- You can view Verts on their own, and set their size and color. Verts are drawn as round, antialiased dots. Color can be set by vertex or by object, also can generate random colors in one click.
- You can view Edges, set their color and thickness and even apply a Dashed edge style. Edges are antialiased and the thickness works on every backend (including Metal and Vulkan). Dash and gap lengths are set in pixels, so they stay the same size as you zoom. Color can be set by edge or by object, also can use vertex colors to color edges.
- You can view Faces, set their color, and infer the associated Edges. The facet and normals modes work with any faces, the smooth mode uses Faces to produce vertex normals. Color can be set by polygon or by mesh, also can use vertex colors to color faces.
- Bake the current mesh(es)
- Set the 3d cursor to the center of Mesh 1. (handy for rotating around in this virtual geometry)
- "Depth Offset" (to prevent z-fighting between edges/verts and faces). Edges and verts are pulled toward the viewer by a small fraction of their distance, so it works the same up close and far away. Set it to 0 to turn it off. This replaces Mk4's polygon offset.
- "quad tessellator" (Handle Concave Quads), this mode treats all quads as potentially irregular and tessellates them with mathutils.
- "All Triangles", enable if all incoming faces are triangles, this skips tessellation and makes the node faster.
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

Mk5 builds on the Mk4 node, which has been in development on and off since the first 2.8 releases. It should be stable, but you will find bugs, let us know. Better yet, suggest fixes (preferably not requiring dedicated hardware) :)
