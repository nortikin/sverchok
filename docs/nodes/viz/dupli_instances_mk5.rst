Dupli Instances
===============

Functionality
-------------

This node exposes the Blender functionality of Instancing on object Vertices or Faces
to the Sverchok node tree being able to display many copies of the same object with a very
low memory impact.

The Node  has to main modes Verts and Polys.
  - In the **Verts** mode the instances will be placed at the inputted vertices.
  - In the **Polys** mode the instances will be placed with a incoming list matrices,
    being able to rotate and scale the instances.

Parameters & Features
---------------------

+-------------------+---------------------------------------------------------------------------------------+
| Param             | Description                                                                           |
+===================+=======================================================================================+
| Live              | Processing only happens if *update* is ticked                                         |
+-------------------+---------------------------------------------------------------------------------------+
| Hide View         | Hides current meshes from view                                                        |
+-------------------+---------------------------------------------------------------------------------------+
| Hide Select       | Disables the ability to select these meshes                                           |
+-------------------+---------------------------------------------------------------------------------------+
| Hide Render       | Disables the renderability of these meshes                                            |
+-------------------+---------------------------------------------------------------------------------------+
| Base Name         | Base name for Objects and Meshes made by this node                                    |
+-------------------+---------------------------------------------------------------------------------------+
| Random name       | Generates random name with random letters                                             |
+-------------------+---------------------------------------------------------------------------------------+
| Select            | Select every object in 3dview that was created by this Node                           |
+-------------------+---------------------------------------------------------------------------------------+
| Collection        | Pick collection where to put objects                                                  |
+-------------------+---------------------------------------------------------------------------------------+
| Fast mesh update  | It tries to update mesh in fast way. It can not update mesh at all in some corner     |
|                   | cases. In case you notify some glitches in the mesh disable it (N-Panel)              |
+-------------------+---------------------------------------------------------------------------------------+
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
| Auto Release      | Remove children not called by this node                                               |
+-------------------+---------------------------------------------------------------------------------------+
| Clear Location    | Clear base child location                                                             |
+-------------------+---------------------------------------------------------------------------------------+


Inputs
------

**Child**: Object(s) to instance.

**Vertices**: Location of instances.

**Matrices**: Matrices of the instances. (but scale is converted to uniform)


Limitations
-----------

It's worth mentioning that because the faces duplication relies on the area of the triangle to determine the scale, that the scale is a scalar, and therefor uniform (x,y,z are scaled equally).



Examples
--------

Setting 1.000.000 icospheres (whole node-tree update 0.069 secs)

.. image:: https://user-images.githubusercontent.com/10011941/117689137-c0fffc80-b1b9-11eb-9a00-2a57f7e49976.png
