Fill Holes
==========

.. image:: https://user-images.githubusercontent.com/14288520/200031589-47edec1e-ef4f-4d45-8757-6b68aed53831.png
  :target: https://user-images.githubusercontent.com/14288520/200031589-47edec1e-ef4f-4d45-8757-6b68aed53831.png

Functionality
-------------

It fills closed countors from edges that own minimum vertices-sides with polygons. See: https://docs.blender.org/api/current/bmesh.ops.html#bmesh.ops.holes_fill

.. image:: https://user-images.githubusercontent.com/14288520/200031608-0cf94a14-1abb-4b23-a80f-ea7192c79343.png
  :target: https://user-images.githubusercontent.com/14288520/200031608-0cf94a14-1abb-4b23-a80f-ea7192c79343.png

Inputs
------

- **Vertices**
- **Edges**

Parameters
----------

+-----------------+---------------+-------------+-------------------------------------------------------------+
| Param           | Type          | Default     | Description                                                 |
+=================+===============+=============+=============================================================+
| **Sides**       | Float         | 4           | Number of sides that will be collapsed to polygon.          |
+-----------------+---------------+-------------+-------------------------------------------------------------+

Outputs
-------

- **Vertices**
- **Edges**
- **Polygons**. All faces of resulting mesh.

Examples of usage
-----------------

.. image:: https://user-images.githubusercontent.com/14288520/200034407-091dc20a-c59b-4987-b0b7-381fe8b65b22.png
  :target: https://user-images.githubusercontent.com/14288520/200034407-091dc20a-c59b-4987-b0b7-381fe8b65b22.png

* Generator->Generator Extended-> :doc:`Polygon Grid </nodes/generators_extended/polygon_grid>`
* Analyzers-> :ref:`Component Analyzer/Edges/Is Interior <EDGES_IS_INTERIOR>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* AND: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Modifiers->Modifier change-> :doc:`Disslove Mesh Elements </nodes/modifier_change/dissolve_mesh_elements>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Fill holes of formula shape, edges of initial shape + voronoi grid + fill holes

.. image:: https://user-images.githubusercontent.com/14288520/200036800-851da3fb-5297-49a6-9a33-7bce01dcaf1c.png
  :target: https://user-images.githubusercontent.com/14288520/200036800-851da3fb-5297-49a6-9a33-7bce01dcaf1c.png

* Generators-> :doc:`Formula </nodes/generator/formula_shape>`
* Spacial-> :doc:`Voronoi 2D </nodes/spatial/voronoi_2d>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/200038462-1bd0c7fc-193f-423e-b5be-753008b3bc52.gif
  :target: https://user-images.githubusercontent.com/14288520/200038462-1bd0c7fc-193f-423e-b5be-753008b3bc52.gif

