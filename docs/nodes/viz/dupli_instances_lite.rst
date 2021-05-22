DupliVerts
===============

Functionality
-------------

This node exposes the Blender functionality of Instancing on object Vertices or Faces
to the Sverchok node tree being able to display many copies of the same object with a very
low memory impact.

The Node  has to main modes Verts and Polys.
  - In the **Verts** mode the instances will be placed at the parent vertices.
  - In the **Polys** mode the instances will be placed at the parent faces.

Parameters & Features
---------------------

+-------------------+---------------------------------------------------------------------------------------+
| Param             | Description                                                                           |
+===================+=======================================================================================+
| Show instancer    | Show instancer geometry in viewport                                                   |
| in viewport       |                                                                                       |
+-------------------+---------------------------------------------------------------------------------------+
| Show instancer    | Show instancer geometry in render                                                     |
| in render         |                                                                                       |
+-------------------+---------------------------------------------------------------------------------------+
| Show base child   | Show base child geometry in viewport                                                  |
| in viewport       |                                                                                       |
+-------------------+---------------------------------------------------------------------------------------+
| Scale Children    | Scale children instances (only in Polys mode)                                         |
+-------------------+---------------------------------------------------------------------------------------+
| Align with normal | Align Instances with vertex normal (only in Verts mode)                               |
+-------------------+---------------------------------------------------------------------------------------+
| Auto Release      | Remove children not called by this node                                               |
+-------------------+---------------------------------------------------------------------------------------+

Inputs
------

**Parent**: Instancer Object(s).

**Child**: Object(s) to instance.

**Scale**: Instances scale (value per parent).


Limitations
-----------

This node can work without being connected to any other nodes but due the logic
behind Sverchok update system the node will not work if there is not any link in
the whole node-tree

Examples
--------

Basic usage

.. image:: https://user-images.githubusercontent.com/10011941/119203629-ce5b9780-ba93-11eb-87c0-6905ee79fcc6.png
