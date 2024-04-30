Mesh clustering
===============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/0ff2d512-2da9-492d-93af-00d85c2b38de
  :target: https://github.com/nortikin/sverchok/assets/14288520/0ff2d512-2da9-492d-93af-00d85c2b38de

Dependencies
------------

This node requires pyacvd_ library to work. One can install it in addon settings:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/65467755-82b9-4e71-802d-0978eb2e849d
  :target: https://github.com/nortikin/sverchok/assets/14288520/65467755-82b9-4e71-802d-0978eb2e849d

Functionality
-------------

This node takes a surface mesh and returns a uniformly meshed surface using voronoi clustering.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/fb0d011c-8550-4262-bf77-29d2012511c2
  :target: https://github.com/nortikin/sverchok/assets/14288520/fb0d011c-8550-4262-bf77-29d2012511c2

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

- **Matrixes**. Spread you source meshes by matrixes. You can use vertices of another meshes as matrixes:

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/1b110e99-ebec-4805-9e45-ba7cb49b640f
      :target: https://github.com/nortikin/sverchok/assets/14288520/1b110e99-ebec-4805-9e45-ba7cb49b640f

Parameters
----------

Triangulation.

Before clusterisation your source meshes has to be triangulated. Here are parameters for process of triangulation.

If source mesh has ngons woth different count of vertices then source mesh has to be triangulated with the next methods [**Quads mode** and **Polygons mode**].
If ngons of source mesh are equals (they can has 3,4,5 verts but for all faces) the mesh will be triangulated with pyvista method triangulate_ authomatically.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/66bedca2-c62f-4603-b42a-5b86a6a8eef6
  :target: https://github.com/nortikin/sverchok/assets/14288520/66bedca2-c62f-4603-b42a-5b86a6a8eef6

- **Quads mode**:
    - **Beauty**. Split the quads in nice triangles, slower method
    - **Fixed**. Split the quads on the 1st and 3rd vertices
    - **Fixed Alternate**. Split the quads on the 2nd and 4th vertices
    - **Shortest Diagonal**. Split the quads based on the distance between the vertices

- **Polygons mode**:
    - **Beauty**. Arrange the new triangles nicely, slower method
    - **Clip**. Split the ngons using a scanfill algorithm

If your mesh is low poly and you want to smooth it then you can use subdivide mode:

- **Subdiv mode**:
    - **Butterfly**.
    - **Loop**. Butterfly and loop subdivision perform smoothing when dividing, and may introduce artifacts into the mesh when dividing
    - **Linear**. Linear subdivision results in the fastest mesh subdivision, but it does not smooth mesh edges, but rather splits each triangle into 4 smaller triangles

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/672dc04d-4f3d-4dff-b359-1b40b98de57a
      :target: https://github.com/nortikin/sverchok/assets/14288520/672dc04d-4f3d-4dff-b359-1b40b98de57a

Outputs
-------

Clusterized mesh:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/6a203a16-e23a-4214-a674-bbe507d1c5a1
  :target: https://github.com/nortikin/sverchok/assets/14288520/6a203a16-e23a-4214-a674-bbe507d1c5a1

- **Vertices**
- **Edges**
- **Polygons**

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/6258394e-b5c6-4688-baff-dd964f599e4f
      :target: https://github.com/nortikin/sverchok/assets/14288520/6258394e-b5c6-4688-baff-dd964f599e4f

- **Centers of Polygons**
- **Normals of Polygons**

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/f62224e2-0f7e-4ecc-9478-0be93ebd56d9
      :target: https://github.com/nortikin/sverchok/assets/14288520/f62224e2-0f7e-4ecc-9478-0be93ebd56d9

Example of Usage
----------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/4140d9d7-c710-4ad7-a223-5ca62f4069f1
  :target: https://github.com/nortikin/sverchok/assets/14288520/4140d9d7-c710-4ad7-a223-5ca62f4069f1

High poly clusterizing
----------------------

Subdivide is zero.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/a25eb0d2-cccc-4086-b663-0036d60314a5
  :target: https://github.com/nortikin/sverchok/assets/14288520/a25eb0d2-cccc-4086-b663-0036d60314a5


High poly clusterizing with dual mesh
-------------------------------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/1f786c06-cde4-4227-b539-59926e1e737b
  :target: https://github.com/nortikin/sverchok/assets/14288520/1f786c06-cde4-4227-b539-59926e1e737b

example_001_

.. _pyacvd: https://github.com/pyvista/pyacvd
.. _triangulate: https://docs.pyvista.org/version/stable/api/core/_autosummary/pyvista.polydatafilters.triangulate
.. _example_001: https://github.com/nortikin/sverchok/files/15172028/RoundedCube.Juwelry.0003.blend.zip