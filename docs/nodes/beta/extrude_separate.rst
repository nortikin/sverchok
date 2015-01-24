Extrude Separate Faces
======================

*destination after Beta: Modifier Change*

Functionality
-------------

This node applies Extrude operator to each of input faces separately. After that, resulting faces can be scaled up or down by specified factor.
It is possible to provide specific extrude and scaling factors for each face.

Inputs
------

This node has the following inputs:

- **Vertices**
- **Edges**
- **Polygons**
- **Height**. Extrude factor.
- **Scale**. Scaling factor.

Parameters
----------

This node has the following parameters:

+----------------+---------------+-------------+------------------------------------------------------+
| Parameter      | Type          | Default     | Description                                          |  
+================+===============+=============+======================================================+
| **Height**     | Float         | 0.0         | Extrude factor as a portion of face normal length.   |
|                |               |             | Default value of zero means do not extrude.          |
|                |               |             | Negative value means extrude to the opposite         |
|                |               |             | direction. This parameter can be also provided via   |
|                |               |             | corresponding input.                                 |
+----------------+---------------+-------------+------------------------------------------------------+
| **Scale**      | Float         | 1.0         | Scale factor. Default value of 1 means do not scale. |
+----------------+---------------+-------------+------------------------------------------------------+

Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**
- **Polygons**

Example of usage
----------------

Extruded faces of sphere:

.. image:: https://cloud.githubusercontent.com/assets/284644/5887778/1c180640-a405-11e4-8b21-35c7b4229d8b.png

