Calculate Normals
=================

.. image:: https://user-images.githubusercontent.com/14288520/195733730-3cbd75a3-e545-4377-bc8f-7dd510e1875d.png
  :target: https://user-images.githubusercontent.com/14288520/195733730-3cbd75a3-e545-4377-bc8f-7dd510e1875d.png

Functionality
-------------

This node calculates normals for faces and edges of given mesh. Normals can be calculated even for meshes without faces, i.e. curves.

Inputs
------

This node has the following inputs:

- **Vertices**
- **Polygons**

Options
-------

Offers different calculation methods:

* Bmesh (standard Blender, slowest),
* Mean Weighted Equally (Fastest),
* Mean Weighted Based on Triangle Area
* Mean Weighted Edge Length Reciprocal
* Mean Weighted by Sine
* Mean Weighted by Sine/Edge Length
* Mean Weighted Area
* Mean Weighted Angle*Area
* Mean Weighted Sine*Area
* Mean Weighted Edge Length
* Mean Weighted 1/Edge Length
* Mean Weighted 1/sqrt(Edge Length)

Outputs
-------

This node has the following outputs:

- **Face Normals**. Normals of faces. This output will be empty if **Polygons** input is empty.
- **Vertex Normals**. Normals of vertices.

Examples of usage
-----------------

Move each face of cube along its normal:

.. image:: https://user-images.githubusercontent.com/14288520/195851228-2dd57058-e2bd-4644-9a6d-001117aade04.png
  :target: https://user-images.githubusercontent.com/14288520/195851228-2dd57058-e2bd-4644-9a6d-001117aade04.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`
* Modifiers->Modifier Change-> :doc:`Polygon Boom </nodes/modifier_change/polygons_boom>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/195851616-d5b47ede-2a96-42f1-8de2-f1283386778e.gif
  :target: https://user-images.githubusercontent.com/14288520/195851616-d5b47ede-2a96-42f1-8de2-f1283386778e.gif


TODO: NEED REPLAY
-----------------

**Next examples cannot be replayed with new node. No input edge. Need check:**

Visualization of vertex normals for bezier curve:

.. image:: https://cloud.githubusercontent.com/assets/284644/5989204/f8655fbc-a9a0-11e4-94d5-caf403d3a64a.png

Normals can be also calculated for closed curves:

.. image:: https://cloud.githubusercontent.com/assets/284644/5989202/f8632a44-a9a0-11e4-8745-19065eb13bcd.png
