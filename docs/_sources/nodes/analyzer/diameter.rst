Diameter
========

.. image:: https://user-images.githubusercontent.com/14288520/195307854-bfecb75f-d3c8-41e7-8507-2ddaafbe40de.png
  :target: https://user-images.githubusercontent.com/14288520/195307854-bfecb75f-d3c8-41e7-8507-2ddaafbe40de.png

Functionality
-------------

This node calculates the diameter of input set of vertices.

It can calculate diameter in two ways:

* General diameter, i.e. maximum distance between any two vertices from input set.
* Diameter along specified direction (axis), i.e. the length of the projection
  of whole input vertices set to specified direction.

Inputs
------

This node has the following inputs:

* **Vertices** - vertices to calculate diameter of. This input is mandatory for the node to function.
* **Direction** - direction, along which diameter should be calculated. If this
  input is not connected, then the node will calculate "general diameter" of
  input vertices set.

Outputs
-------

This node has one output:

* **Diameter** - calculated diameter of vertices set.

See also
--------

* Analyzers-> :doc:`Bounding Box </nodes/analyzer/bbox_mk3>`
* Analyzers-> :doc:`Aligned Bounding Box </nodes/analyzer/bbox_aligned>`

Examples of usage
-----------------

Front View:

.. image:: https://user-images.githubusercontent.com/14288520/195307893-3e7127ca-fe56-4ee8-a2cf-da7a8cb7f4ed.png
  :target: https://user-images.githubusercontent.com/14288520/195307893-3e7127ca-fe56-4ee8-a2cf-da7a8cb7f4ed.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Analyzers-> :doc:`Distance Point Line </nodes/analyzer/distance_point_line>`
* Analyzers-> :doc:`Bounding Box </nodes/analyzer/bbox_mk3>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Vector-> :doc:`Vector Out </nodes/vector/vector_out>`
* SCALAR, NEG: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix-> :doc:`Matrix Normal </nodes/matrix/matrix_normal>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/195311232-5db18b7b-7723-4f2e-abaa-753030d3cb83.gif
  :target: https://user-images.githubusercontent.com/14288520/195311232-5db18b7b-7723-4f2e-abaa-753030d3cb83.gif

---------

Suzanne has "general diameter" of 2.73:

.. image:: https://user-images.githubusercontent.com/284644/58649984-03aad000-8327-11e9-90b8-0c39f328402a.png

---------

Diameter of Suzanne along some diagonal direction is 2.44. Here the direction
is drawn as green line, and the projection of Suzanne to that direction is
marked with red dots:

.. image:: https://user-images.githubusercontent.com/284644/58649983-03aad000-8327-11e9-852a-a75d8eb4aad4.png

