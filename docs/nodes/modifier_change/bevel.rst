Bevel
=====

Functionality
-------------

This node applies Bevel operator to the input mesh. You can specify edges to be beveled.

Inputs
------

This node has the following inputs:

- **Vertices**
- **Edges**
- **Polygons**
- **BevelEdges / VerticesMask**.  Edges or vertices to be beveled. If this input is not connected, then by default all will be beveled. This parameter changes when ``Vertex mode`` flag is modified. 
On vertex mode it will expect a list of True/False (or 0/1) values indicating the selected vertices([[0,1,0,..]]).
Otherwise it will expect a list of Edges([[2,6],[3,4]...]).

- **Amount**. Amount to offset beveled edge.
- **Segments**. Number of segments in bevel.
- **Profile**. Profile shape.

Parameters
----------

This node has the following parameters:

+------------------+---------------+-------------+----------------------------------------------------+
| Parameter        | Type          | Default     | Description                                        |
+==================+===============+=============+====================================================+
| **Amount type**  | Offset or     | Offset      | * Offset - Amount is offset of new edges from      |
|                  |               |             |   original.                                        |
|                  | Width or      |             | * Width - Amount is width of new face.             |
|                  | Depth or      |             | * Depth - Amount is perpendicular distance from    |
|                  |               |             |   original edge to bevel face.                     |
|                  | Percent       |             | * Percent - Amount is percent of adjacent edge     |
|                  |               |             |   length.                                          |
+------------------+---------------+-------------+----------------------------------------------------+
| **Vertex mode**  | Boolean       | False       | Bevel edges or only vertex. When activated the mask|
|                  |               |             | will switch from 'Bevel Edges' to 'MaskVertices'   |
+------------------+---------------+-------------+----------------------------------------------------+
| **Amount**       | Float         | 0.0         | Amount to offset beveled edge. Exact               |
|                  |               |             | interpretation of this parameter depends on        |
|                  |               |             | ``Amount type`` parameter. Default value of zero   |
|                  |               |             | means do not bevel. This parameter can also be     |
|                  |               |             | specified via corresponding input.                 |
+------------------+---------------+-------------+----------------------------------------------------+
| **Segments**     | Int           | 1           | Number of segments in bevel. This parameter can    |
|                  |               |             | also be specified via corresponding input.         |
+------------------+---------------+-------------+----------------------------------------------------+
| **Profile**      | Float         | 0.5         | Profile shape - a float number from 0 to 1;        |
|                  |               |             | default value of 0.5 means round shape.  This      |
|                  |               |             | parameter can also be specified via corresponding  |
|                  |               |             | input.                                             |
+------------------+---------------+-------------+----------------------------------------------------+

Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**
- **Polygons**
- **NewPolys** - only bevel faces.

Examples of usage
-----------------

Beveled cube:

.. image:: https://cloud.githubusercontent.com/assets/284644/5888719/add3aebe-a42c-11e4-8da5-3321f93e1ff0.png

Only two edges of cube beveled:

.. image:: https://cloud.githubusercontent.com/assets/284644/5888718/adc718b6-a42c-11e4-80d6-7793e682f8e4.png

Another sort of cage:

.. image:: https://cloud.githubusercontent.com/assets/284644/5888727/dc332794-a42c-11e4-9007-d86610405164.png

You can work with multiple objects:

.. image:: https://cloud.githubusercontent.com/assets/5783432/18603141/322847ce-7c80-11e6-8357-6ef4673add4d.png

Vertex mode and multiple radius:

.. image:: https://user-images.githubusercontent.com/10011941/38384563-cb1bb8a6-390f-11e8-82cc-d2a978cb8d52.png