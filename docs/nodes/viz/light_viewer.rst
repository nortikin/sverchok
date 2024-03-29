Light viewer
============

.. image:: https://user-images.githubusercontent.com/28003269/91758075-74066800-ebe0-11ea-8df0-c787037fb664.png

.. image:: https://user-images.githubusercontent.com/14288520/190479510-08d34c94-418c-4cd1-b53a-d7286be80531.png
  :target: https://user-images.githubusercontent.com/14288520/190479510-08d34c94-418c-4cd1-b53a-d7286be80531.png

This node offers a nodification of the currently implemented lamps in Blender. It should be self explanatory.
- you can pass it multiple vectors and it will generate an individual lamp for each
- if you want unique colors per lamp, then feed it the output of a Colour Out node (with a list-split before hand)

Category
--------

Viz -> Light viewer


Inputs
------

- Origins - list of matrices where to place generated lights
- Size - size of for some type of lights
- Strength - energy of a light
- Color - color of a light
- Size X - size along X axis for rectangle and ellipse shapes
- Size Y - size along Y axis for rectangle and ellipse shapes
- Spot size - size of a lamp of spot type
- Spot blend - sharpness of light for spot type

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
| Type              | Type of light                                                                         |
+-------------------+---------------------------------------------------------------------------------------+
| Shape             | Shape of light for area type                                                          |
+-------------------+---------------------------------------------------------------------------------------+
| Cast shadow       | Show shadows (N panel)                                                                |
+-------------------+---------------------------------------------------------------------------------------+
| Show cone         | Show cone for spot light (N panel)                                                    |
+-------------------+---------------------------------------------------------------------------------------+

*Note: Some features are placed in the `N-Panel` / `Properties Panel`.*

Outputs
-------

- Objects


Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/190483867-25a738be-f4e4-4604-9487-225ed5299d84.png
  :target: https://user-images.githubusercontent.com/14288520/190483867-25a738be-f4e4-4604-9487-225ed5299d84.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Matrix-> :doc:`Matrix Normal </nodes/matrix/matrix_normal>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* List->List Struct-> :doc:`List Split </nodes/list_struct/split>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`