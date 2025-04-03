Points Inside Mesh
==================

.. image:: https://user-images.githubusercontent.com/14288520/198854766-ac4b81c7-d9ef-4377-bec1-ddb15157329f.png
  :target: https://user-images.githubusercontent.com/14288520/198854766-ac4b81c7-d9ef-4377-bec1-ddb15157329f.png

.. image:: https://user-images.githubusercontent.com/14288520/196754002-c9ab80b9-29ef-48bc-a47b-f3ea836fb09e.png
  :target: https://user-images.githubusercontent.com/14288520/196754002-c9ab80b9-29ef-48bc-a47b-f3ea836fb09e.png

.. image:: https://user-images.githubusercontent.com/14288520/196754459-e6b45887-3a06-4653-b9f5-53f8e7d2d64e.png
  :target: https://user-images.githubusercontent.com/14288520/196754459-e6b45887-3a06-4653-b9f5-53f8e7d2d64e.png

.. image:: https://user-images.githubusercontent.com/14288520/196778786-ca4b3065-8142-434e-a504-4a1c3e5ae1ae.png
  :target: https://user-images.githubusercontent.com/14288520/196778786-ca4b3065-8142-434e-a504-4a1c3e5ae1ae.png

Functionality
-------------

The node determines if points are inside a mesh. It has two modes, 2D and 3D


* In the 2D mode will determine if points are inside the polygons of the input mesh.

  * When inputting points or verts with different z coordinates the projection to the mesh will be done using the "Plane "Normal" input, for a vertical projection it should be (0,0,1) or (0,0,-1).

  * With the Limit Projection checkbox activated the points which are farther than "Max Distance" will be evaluated as out of the mesh


* In the 3D mode will determine if a list of probe points are inside an associated manifold boundary mesh (verts, faces). It analyses for each of the probe points whether it is located inside or outside of the boundary mesh.

  * It offers two algorithms *Regular* is faster, *Multisample* more precise

  * Warning. This is only a first implementation, likely it will be more correct after a few iterations.

see https://github.com/nortikin/sverchok/pull/1703

Examples of use
---------------

.. image:: https://user-images.githubusercontent.com/14288520/196766892-42718417-18cc-4388-b6f9-e4e50f311002.png
  :target: https://user-images.githubusercontent.com/14288520/196766892-42718417-18cc-4388-b6f9-e4e50f311002.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/196765846-5b94a190-7e66-42ba-ae40-4a54382e23b0.png
  :target: https://user-images.githubusercontent.com/14288520/196765846-5b94a190-7e66-42ba-ae40-4a54382e23b0.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Transform-> :doc:`Rotate </nodes/transforms/rotate_mk3>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Analyzers-> :doc:`Raycaster </nodes/analyzer/raycaster_lite>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* NEG: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/196765769-736f57f6-f212-4c27-8244-c0b4ee1f3135.gif
  :target: https://user-images.githubusercontent.com/14288520/196765769-736f57f6-f212-4c27-8244-c0b4ee1f3135.gif

---------

.. image:: https://user-images.githubusercontent.com/14288520/196770641-ada28443-0adf-4b26-ab4e-aafa0bbaaa1c.png
  :target: https://user-images.githubusercontent.com/14288520/196770641-ada28443-0adf-4b26-ab4e-aafa0bbaaa1c.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* NEG, MUL, SCALAR: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* NORMALIZE: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/196773927-d1087ccb-fb5a-4d5d-957e-743b24e9fd2c.png
  :target: https://user-images.githubusercontent.com/14288520/196773927-d1087ccb-fb5a-4d5d-957e-743b24e9fd2c.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Analyzers-> :ref:`Component Analyzer/Faces/Center <FACES_CENTER>`
* Modifiers->Modifier Change-> :doc:`Inset Faces </nodes/modifier_change/inset_faces>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/196775884-d25e9a4b-f081-4a7d-94bd-fa8d614bdb35.png
  :target: https://user-images.githubusercontent.com/14288520/196775884-d25e9a4b-f081-4a7d-94bd-fa8d614bdb35.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* ADD: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`