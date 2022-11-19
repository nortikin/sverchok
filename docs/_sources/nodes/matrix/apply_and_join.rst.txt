Matrix Apply to Mesh
====================

.. image:: https://user-images.githubusercontent.com/14288520/189549058-5f162b01-31f8-4c95-a4b4-25ac884343b0.png
  :target: https://user-images.githubusercontent.com/14288520/189549058-5f162b01-31f8-4c95-a4b4-25ac884343b0.png

Functionality
-------------

Applies a Transform Matrix to a list or nested lists of vertices, edges and faces. If several matrices are provided on the input, then this node will produce several meshes.

**Note**. Unless there is further processing going on which explicitly require the duplicated topology, then letting the ``Viewer Draw`` or ``BMesh Viewer`` nodes automatically repeat the index lists for the edges and faces is slightly more efficient than use of this node.


Inputs
------

This node has the following inputs:

- **Vertices**. Represents vertices or intermediate vectors used for further vector math.
- **Edges**
- **Faces**
- **Matrices**. One or more, never empty.

Parameters
----------

This node has the following parameter:

**Join**. If set, then this node will join output meshes into one mesh, the same way as ``Mesh Join`` node does.
Otherwise, if N matrices are provided at the input, this node will produce N lists of vertices, N lists of edges and N lists of faces.

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Implementation**: 'NumPy' or 'Python'. As a general rule in this node the Numpy implementation will be faster if any input is a NumPy array or you want to get NumPy arrays from the outputs. If the surrounding nodes are using python list the performance of both implementations will depend on many factors. With a light geometry but many matrices the Python implementation will be faster, as heavier gets the input geometry and less the matrices number the NumPy implementation will start being a better choice. Also if the incoming topology of polygons is regular the NumPy implementation will increase its performance while the Python implementation will not be affected by that parameter.

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster). Available for Vertices, Edges and Polygons in the NumPy implementation

Outputs
-------

This node has the following outputs:

- **Vertices**.  Nested list of vectors / vertices, matching the number nested incoming *matrices*.
- **Edges**. Input edges list, repeated the number of incoming matrices. Empty if corresponding input is empty.
- **Faces**. Input faces list, repeated the number of incoming matrices. Empty if corresponding input is empty.

Usage of nested lists of matrices
---------------------------------

The node can handle with list of lists of matrices.
It means that each object mesh has it's own list of matrices to apply.
Applying list of matrices to a mesh creates its copies inside an object and transform its.
Usage case is when there are bunch of separate meshes which should be copied inside their objects.
In this mode and with numpy implementation mode you will get numpy output for vertices and edges anyway.

See also
--------

* Modifiers->Modifier Change-> :doc:`Mesh Join </nodes/modifier_change/mesh_join_mk2>`

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/189549063-bbbd055b-a0d5-47d4-88de-f386b494c664.png
  :target: https://user-images.githubusercontent.com/14288520/189549063-bbbd055b-a0d5-47d4-88de-f386b494c664.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/189549067-823dbfc0-0b81-4df1-a46f-5341138f630a.png
  :target: https://user-images.githubusercontent.com/14288520/189549067-823dbfc0-0b81-4df1-a46f-5341138f630a.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Random </nodes/number/random>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

**Example of usage of nested list of matrices (list of lists of matrices):**

.. image:: https://user-images.githubusercontent.com/14288520/189549070-7d976ed9-01c4-4a97-a24c-2caca93f7872.png
  :target: https://user-images.githubusercontent.com/14288520/189549070-7d976ed9-01c4-4a97-a24c-2caca93f7872.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
* Generator-> :doc:`Cricket </nodes/generator/cricket>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List->List Struct-> :doc:`List Split </nodes/list_struct/split>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Mesh Viewer </nodes/viz/mesh_viewer>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`