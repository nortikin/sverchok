IcoSphere Node
==============

.. image:: https://user-images.githubusercontent.com/14288520/188708444-303645fa-7260-4326-94f7-0eb251740aa1.png
  :target: https://user-images.githubusercontent.com/14288520/188708444-303645fa-7260-4326-94f7-0eb251740aa1.png

Functionality
-------------

This node creates an IcoSphere primitive. Subdivision levels 0 and 1 produce an icosahedron; subsequent levels recursively subdivide its triangular faces.

The IcoSphere MK2 node generates mesh topology directly with NumPy or optional Numba. Unlike the legacy BMesh node, **the vertex, edge and face indices may differ**. The previous node is retained as an old node so existing node trees preserve their original indexing.

.. image:: https://user-images.githubusercontent.com/14288520/191254102-557f8ade-e6a9-4473-b86d-05cda5f22096.png
  :target: https://user-images.githubusercontent.com/14288520/191254102-557f8ade-e6a9-4473-b86d-05cda5f22096.png

Inputs
------

This node has the following inputs:

- **Subdivisions** - How many times to recursively subdivide the sphere. min=0.
- **Radius** - Sphere radius. min=0.

Parameters
----------

This node has the following parameters:
  
- **Max. Subdivisions**. Maximum value available for **Subdivisions** parameter. This affects not only parameter, but also restricts values provided via input. Default maximum is 5.
- **Subdivisions**. How many times to recursively subdivide the sphere. In case this parameter is 0, the node will simply produce right icosahedron. Maximum value is restricted by **Max. Subdivisions** parameter. This parameter can be provided via node input.
- **Radius**. Sphere radius. This parameter can be provided via node input.

The N-panel (node properties sidebar) contains:

- **Implementation**. Select BMesh, NumPy or NumPy + Numba. NumPy + Numba is selected by default when Numba is installed; otherwise NumPy is selected.
- **Cache Topology**. Store a unit-radius mesh by subdivision level and backend, independent of the connected sockets. Changing only the radius or connecting another output reuses cached topology. The cache is limited to six meshes and subdivision levels up to 8.
- **Output Numpy**. Choose NumPy arrays independently for Vertices, Edges and Faces; otherwise output Python lists.
- **List Match**. Control how lists of input values are matched.

The original IcoSphere node is still available for existing files, and can be replaced manually using the node replacement menu. Because the index ordering differs, inspect any downstream nodes that rely on specific element indices before replacing it.

Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**
- **Faces**

Example of usage
----------------

Simple example:

.. image:: https://user-images.githubusercontent.com/14288520/188708570-5c9fda27-d754-4876-ad46-db798efdf798.png
  :target: https://user-images.githubusercontent.com/14288520/188708570-5c9fda27-d754-4876-ad46-db798efdf798.png

