Dupli Instancer
===============

.. image:: https://user-images.githubusercontent.com/14288520/190466323-fce556fd-e18a-4f95-83c0-ddeea53359e2.png
  :target: https://user-images.githubusercontent.com/14288520/190466323-fce556fd-e18a-4f95-83c0-ddeea53359e2.png

.. image:: https://user-images.githubusercontent.com/14288520/190466189-5ec9a354-069c-428a-9685-c9dacf071928.png
  :target: https://user-images.githubusercontent.com/14288520/190466189-5ec9a354-069c-428a-9685-c9dacf071928.png

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
| Fast mesh update  | It tries to update mesh in fast way. It can not update mesh at                        |
|                   |                                                                                       |
|                   | all in some corner cases. In case you notify some glitches in                         |
|                   |                                                                                       |
|                   | the mesh disable it (N-Panel)                                                         |
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

It's worth mentioning that because the faces duplication relies on the area of the triangle to determine the scale, that the scale is a scalar, and therefore uniform (x,y,z are scaled equally).



Examples
--------

Setting 1.000.000 icospheres (whole node-tree update 0.069 secs)

.. image:: https://user-images.githubusercontent.com/14288520/190861942-91bf400b-3db9-4966-bd04-654efa69c5d6.png
  :target: https://user-images.githubusercontent.com/14288520/190861942-91bf400b-3db9-4966-bd04-654efa69c5d6.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Viz-> :doc:`Mesh Viewer </nodes/viz/mesh_viewer>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`