Extrude Separate Faces
======================

Functionality
-------------

This node applies Extrude operator to each of input faces separately. After
that, resulting faces can be scaled up or down by specified factor.
It is possible to provide specific extrude and scaling factors for each face.
As an option, transformation matrix may be provided for each face.

Inputs
------

This node has the following inputs:

- **Vertices**
- **Edges**
- **Polygons**
- **Mask**. List of boolean or integer flags. Zero means do not process face
  with corresponding index. If this input is not connected, then by default all
  faces will be processed.
- **Height**. Extrude factor.
- **Scale**. Scaling factor.
- **Matrix**. Transformation matrix. Default value is the identity matrix.
- **FaceData**. List containing an arbitrary data item for each face of input
  mesh. For example, this may be used to provide material indexes of input
  mesh faces. Optional input.

Parameters
----------

This node has the following parameters:

+-----------------+---------------+-------------+------------------------------------------------------+
| Parameter       | Type          | Default     | Description                                          |  
+=================+===============+=============+======================================================+
| **Mode**        | Enumeration   | Normal      | This defines how the transformation of faces being   |
|                 |               |             | exturded is specified. There are the following       |
|                 |               |             | modes available:                                     |
|                 |               |             |                                                      |
|                 |               |             | * **Normal**: the transformation is defined by       |
|                 |               |             |   **Height** and **Scale** inputs (see below).       |
|                 |               |             | * **Matrix**: the transformation is defined by       |
|                 |               |             |   the **Matrix** input.                              |
+-----------------+---------------+-------------+------------------------------------------------------+
| **Mask mode**   | Enumeration   | Do not      | This defines what exactly to do with faces that are  |
|                 |               | extrude     | masked out. The available modes are:                 |
|                 |               |             |                                                      |
|                 |               |             | * **Do not extrude**. Do not perform extrusion       |
|                 |               |             |   operation on such faces.                           |
|                 |               |             | * **Do not transform**. Such faces will be extruded, |
|                 |               |             |   but will not be transformed (moved or scaled away  |
|                 |               |             |   from positions of original vertices); so the new   |
|                 |               |             |   vertices will be at the same positions as original |
|                 |               |             |   ones. You may want to remove them with **Remove    |
|                 |               |             |   Doubles** node, or move them with another node.    |
|                 |               |             |                                                      |
|                 |               |             | This parameter is available in the N panel only.     |
+-----------------+---------------+-------------+------------------------------------------------------+
| **Height**      | Float         | 0.0         | Extrude factor as a portion of face normal length.   |
|                 |               |             | Default value of zero means do not extrude.          |
|                 |               |             | Negative value means extrude to the opposite         |
|                 |               |             | direction. This parameter can be also provided via   |
|                 |               |             | corresponding input. The input and parameter are     |
|                 |               |             | available only if **Mode** is set to **Normal**.     |
+-----------------+---------------+-------------+------------------------------------------------------+
| **Scale**       | Float         | 1.0         | Scale factor. Default value of 1 means do not scale. |
|                 |               |             | The input and parameter are                          |
|                 |               |             | available only if **Mode** is set to **Normal**.     |
+-----------------+---------------+-------------+------------------------------------------------------+
| **Mask Output** | Enumeration   | Out         | This defines which faces will be marked with 1 in    |
|                 |               |             | the **Mask** output. Several modes may be selected   |
|                 |               |             | together. The available modes are:                   |
|                 |               |             |                                                      |
|                 |               |             | * **Mask**. The faces which were masked out by the   |
|                 |               |             |   **Mask** input.                                    |
|                 |               |             | * **In**. Inner faces of the extrusion, i.e. the     |
|                 |               |             |   same faces that are in the **ExtrudedPolys**       |
|                 |               |             |   output.                                            |
|                 |               |             | * **Out**. Outer faces of the extrusion; these are   |
|                 |               |             |   the same as in **OtherPolys** output, excluding    |
|                 |               |             |   faces that were masked out by **Mask** input.      |
+-----------------+---------------+-------------+------------------------------------------------------+

Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**
- **Polygons**. All faces of resulting mesh.
- **ExtrudedPolys**. Only extruded faces of resulting mesh.
- **OtherPolys**. All other faces of resulting mesh.
- **Mask**. Mask for faces of the resulting mesh; which faces are selected
  depends on the **Mask Output** parameter.

Example of usage
----------------

Extruded faces of sphere, extruding factor depending on Z coordinate of face:

.. image:: https://cloud.githubusercontent.com/assets/284644/5888213/f8c4c4b8-a417-11e4-9a6d-4ee891744587.png

Sort of cage:

.. image:: https://cloud.githubusercontent.com/assets/284644/5888237/978cdc66-a418-11e4-89d4-a17d325426c0.png

An example of **Matrix** mode usage:

.. image:: https://user-images.githubusercontent.com/284644/68410475-9ab76600-01aa-11ea-8aaf-3e13298cfffe.png

Voronoi grid with each cell extruded by it's specific random matrix:

.. image:: https://user-images.githubusercontent.com/284644/68410476-9ab76600-01aa-11ea-90f6-3ab9b20cab56.png

