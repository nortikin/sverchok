Mesh clustering
===============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/050bd959-f825-48c8-8036-790030ea5729
  :target: https://github.com/nortikin/sverchok/assets/14288520/050bd959-f825-48c8-8036-790030ea5729

Dependencies
------------

This node requires pyacvd_ library to work. One can install it in addon settings:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/65467755-82b9-4e71-802d-0978eb2e849d
  :target: https://github.com/nortikin/sverchok/assets/14288520/65467755-82b9-4e71-802d-0978eb2e849d

Functionality
-------------

This node takes a surface mesh and returns a uniformly meshed surface using voronoi clustering.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/f50b985a-45b6-482c-8b7c-1f7551a50b8f
  :target: https://github.com/nortikin/sverchok/assets/14288520/f50b985a-45b6-482c-8b7c-1f7551a50b8f

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e761653b-a88f-42e1-b222-fa243b1642a5
  :target: https://github.com/nortikin/sverchok/assets/14288520/e761653b-a88f-42e1-b222-fa243b1642a5

Inputs
------

This node has the following inputs:

- **Vertices**, **Edges**, **Faces** - Source mesh

- **Subdivide** - if source mesh is not dense enough for uniform remeshing then subdivide source mesh. A linear subdivision of the mesh. If model has high dense one can low Subdivide param to zero. For low dense mesh a value 3 is good. (min=0)

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/2d2d6e3a-747e-4be2-88e2-50e9c9b39c1e
      :target: https://github.com/nortikin/sverchok/assets/14288520/2d2d6e3a-747e-4be2-88e2-50e9c9b39c1e

- **Max itereation** - Max iteration of clusterization. (min=0)
- **Clusters** - Cluster counts. (min=4)

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/6d49a5cf-704d-4566-b56e-861a88b9d34f
      :target: https://github.com/nortikin/sverchok/assets/14288520/6d49a5cf-704d-4566-b56e-861a88b9d34f

- **Triangulate mesh polygons**. If your mesh has faces with different count of vertices then this mash has to be triangulated.

Outputs
-------

Triangulated mesh:

- **Vertices**, **Edges**, **Faces**


Example of Usage
----------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/4140d9d7-c710-4ad7-a223-5ca62f4069f1
  :target: https://github.com/nortikin/sverchok/assets/14288520/4140d9d7-c710-4ad7-a223-5ca62f4069f1

High poly clusterizing
----------------------

Subdivide is zero.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/a25eb0d2-cccc-4086-b663-0036d60314a5
  :target: https://github.com/nortikin/sverchok/assets/14288520/a25eb0d2-cccc-4086-b663-0036d60314a5


.. _pyacvd: https://github.com/pyvista/pyacvd