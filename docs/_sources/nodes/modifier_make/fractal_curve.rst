Fractal Curve
=============

.. image:: https://user-images.githubusercontent.com/14288520/201398869-b97cd996-708d-45c5-8bc7-a0b712244774.png
  :target: https://user-images.githubusercontent.com/14288520/201398869-b97cd996-708d-45c5-8bc7-a0b712244774.png

Functionality
-------------

This node generates a fractal curve, by replacing each edge of input curve with a copy of that curve, several times.

.. image:: https://user-images.githubusercontent.com/14288520/201400256-9234b87a-312d-4859-b95e-c8695f73126f.png
  :target: https://user-images.githubusercontent.com/14288520/201400256-9234b87a-312d-4859-b95e-c8695f73126f.png

NB 1: Number of vertices in the output curve grows exponentially with number of iterations. 

.. image:: https://user-images.githubusercontent.com/14288520/201401867-3387e615-cdde-451a-b37f-2e181feccc01.png
  :target: https://user-images.githubusercontent.com/14288520/201401867-3387e615-cdde-451a-b37f-2e181feccc01.png

NB 2: Usually you will want to use curves, for which diameter (distance between
to most distant vertices) is less than distance from the first vertex to the
last. Otherwise, the output curve can grow very large.

.. image:: https://user-images.githubusercontent.com/14288520/201426832-5b90bb43-d6a0-472a-8aa7-be66f154dd71.png
  :target: https://user-images.githubusercontent.com/14288520/201426832-5b90bb43-d6a0-472a-8aa7-be66f154dd71.png

NB 3: Usually you will want to use curves, edges of which have nearly the same length.

Inputs
------

This node has the following inputs:

* **Iterations** - number of iterations.
* **MinLength** - minimum length of edge to substitute.
* **Vertices** - vertices of input curve. Vertices should go in the order in which they appear in the curve.

Parameters
----------

This node has the following parameters:

* **Iterations**. Number of iterations. If zero, then output curve will be
  exactly the same as input one. Default value is 3. This parameter can also be
  provided from input.
* **Min. length**. Minimum length of edge to substitute. Fractal substitution
  process will stop for specific edge if it's length became less than specified
  value. Minimal value of zero means that fractal substitution process is
  stopped only when maximum number of iterations is reached. This parameter can
  also be provided from input. Default value is 0.01.
* **Precision**. Precision of intermediate calculations (number of decimal
  digits). Default value is 8. This parameter is available only in the **N** panel.

Outputs
-------

This node has one output: **Vertices** - vertices of the output curve. Vertices
go in the order in which they appear in the curve. You may want to use **UV
Connector** node to draw edges between these vertices.

Examples of usage
-----------------

Classical example:

.. image:: https://user-images.githubusercontent.com/14288520/201405917-6ea4f7cd-3b0d-4fc7-a20b-82164649e0d3.png
  :target: https://user-images.githubusercontent.com/14288520/201405917-6ea4f7cd-3b0d-4fc7-a20b-82164649e0d3.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Analyzers-> :doc:`Bounding Box </nodes/analyzer/bbox_mk3>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Another example:

.. image:: https://user-images.githubusercontent.com/14288520/201408641-ac592164-9872-423f-9575-a0dffac8c370.png
  :target: https://user-images.githubusercontent.com/14288520/201408641-ac592164-9872-423f-9575-a0dffac8c370.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Analyzers-> :doc:`Bounding Box </nodes/analyzer/bbox_mk3>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

This node can process 3D curves as well:

.. image:: https://user-images.githubusercontent.com/284644/57985246-970a1880-7a7e-11e9-84f3-198244d92df0.png
  :target: https://user-images.githubusercontent.com/284644/57985246-970a1880-7a7e-11e9-84f3-198244d92df0.png

---------

Vectorization example:

.. image:: https://user-images.githubusercontent.com/14288520/201425422-bb60a043-84e1-4d3f-96b0-9c663356f958.png
  :target: https://user-images.githubusercontent.com/14288520/201425422-bb60a043-84e1-4d3f-96b0-9c663356f958.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`