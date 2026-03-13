Make Faces Planar
=================

.. image:: https://user-images.githubusercontent.com/14288520/199598558-cf12fd66-e331-434a-9ddc-1afb2fede49b.png
  :target: https://user-images.githubusercontent.com/14288520/199598558-cf12fd66-e331-434a-9ddc-1afb2fede49b.png

Functionality
-------------

This node adjusts the positions of mesh vertices, trying to make all it's faces
planar (flat). Obviously, this makes sense only for meshes with Quad and/or
NGon faces.

This node implements standard Blender_'s function "Make Planar Faces". Please
refer to Blender documentation for more details.

.. _Blender: https://docs.blender.org/manual/en/latest/modeling/meshes/editing/cleanup.html#make-planar-faces

.. image:: https://user-images.githubusercontent.com/14288520/199600666-7163d054-2891-41d6-819d-a925fad3715d.png
  :target: https://user-images.githubusercontent.com/14288520/199600666-7163d054-2891-41d6-819d-a925fad3715d.png

Inputs
------

This node has the following inputs:

- **Vertices**. This input is mandatory.
- **Edges**.
- **Faces**. This input is mandatory.
- **FaceMask**. The mask for faces to be considered. By default, all faces are considered.
- **Iterations**. Number of times to repeat the operation. The default value is
  1. This input can also be specified as a parameter. This input expects one
  value per input mesh.
- **Factor**. Distance to move the vertices each iteration. The default value
  is 0.5. This input can also be specified as a parameter. This input expects
  one value per input mesh.

.. image:: https://user-images.githubusercontent.com/14288520/199601915-a3f42c2b-e0f2-4466-a009-628e9df2c8bd.gif
  :target: https://user-images.githubusercontent.com/14288520/199601915-a3f42c2b-e0f2-4466-a009-628e9df2c8bd.gif

Parameters
----------

This node has no parameters.

Outputs
-------

This node has the following outputs:

- **Vertices**.
- **Edges**.
- **Faces**.

Example of Usage
----------------

Simple example:

.. image:: https://user-images.githubusercontent.com/14288520/199604392-e5b9d3be-3e52-453e-95dd-3f572033a7ac.png
  :target: https://user-images.githubusercontent.com/14288520/199604392-e5b9d3be-3e52-453e-95dd-3f572033a7ac.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Spatial-> :doc:`Convex Hull </nodes/spatial/convex_hull_mk2>`
* Modifiers->Modifier Make-> :doc:`Dual Mesh </nodes/modifier_make/dual_mesh>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/199602183-77a598dd-bdea-46a5-b58d-87bcddeea5ab.png
  :target: https://user-images.githubusercontent.com/14288520/199602183-77a598dd-bdea-46a5-b58d-87bcddeea5ab.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`