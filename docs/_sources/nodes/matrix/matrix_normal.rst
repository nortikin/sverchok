Matrix Normal
=============

.. image:: https://user-images.githubusercontent.com/14288520/189594017-c08d8a4b-943f-41bf-aa97-3a94802b48a8.png
  :target: https://user-images.githubusercontent.com/14288520/189594017-c08d8a4b-943f-41bf-aa97-3a94802b48a8.png

Functionality
-------------

This node calculates a Position Matrix from a location and a Normal Vector. Is useful to place meshes in custom planes (or polygons)

Inputs & Parameters
-------------------

+-------------------+--------------------------------------------------------------------------------------------------+
| Parameters        | Description                                                                                      |
+===================+==================================================================================================+
| Track             | Determine with axis should match the given normal                                                |
+-------------------+--------------------------------------------------------------------------------------------------+
| Up                | Parameter to sort the other axis                                                                 |
+-------------------+--------------------------------------------------------------------------------------------------+

On the right-click menu there is a "Flat Output" toggle. While active (as it is by default)
it will join the first level to output a regular matrix list ([M,M,..]) that can be
plugged to any other node. If it is disabled the node will keep the original structure
outputting a list of matrix lists ([[M,M,..],[M,M,..],..]).

Outputs
-------

One (or many) Transform Matrix


Examples
--------

Using the the node to place a mesh according to a base mesh vertex normals.

.. image:: https://user-images.githubusercontent.com/14288520/189552392-26211080-9e83-44e2-ac7d-f2909ed49b3d.png
  :target: https://user-images.githubusercontent.com/14288520/189552392-26211080-9e83-44e2-ac7d-f2909ed49b3d.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Analyzers-> :doc:`Component Analyzer </nodes/analyzer/component_analyzer>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`