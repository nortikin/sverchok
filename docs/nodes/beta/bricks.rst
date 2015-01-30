Bricks Grid
===========

*destination after Beta: Generators*

Functionality
-------------

This node generates bricks-like grid, i.e. a grid each row of which is shifted with relation to another. It is also possible to specify toothing, so it will be like engaged bricks.
All parameters of bricks can be randomized with separate control over randomization of each parameter.


Inputs & Parameters
-------------------

All parameters can be given by the node or an external input.
All inputs are vectorized and they will accept single or multiple values.

+-----------------+---------------+-------------+-------------------------------------------------------------+
| Param           | Type          | Default     | Description                                                 |
+=================+===============+=============+=============================================================+
| **Unit width**  | Float         | 2.0         | Width of one unit (brick).                                  |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Unit height** | Float         | 1.0         | Height of one unit (brick).                                 |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Width**       | Float         | 10.0        | Width of overall grid.                                      |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Height**      | Float         | 10.0        | Height of overall grid.                                     |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Toothing**    | Float         | 0.0         | Bricks toothing amount. Default value of zero means no      |
|                 |               |             | toothing.                                                   |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Toothing      | Float         | 0.0         | Toothing randomization factor. Default value of zero means  |
| random**        |               |             | that all toothings will be equal. Maximal value of 1.0      |
|                 |               |             | means toothing will be random in range from zero to value   |
|                 |               |             | of ``Toothing`` parameter.                                  |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Random U**    | Float         | 0.0         | Randomization amplitude along bricks rows. Default value of |
|                 |               |             | zero means all bricks will be of same width.                |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Random V**    | Float         | 0.0         | Randomization amplitude across bricks rows. Default value   |
|                 |               |             | of zero means all grid rows will be of same height.         |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Shift**       | Float         | 0.5         | Brick rows shift factor. Default value of 0.5 means each    |
|                 |               |             | row of bricks will be shifted by half of brick width in     |
|                 |               |             | relation to previous row. Minimum value of zero means no    |
|                 |               |             | shift.                                                      |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Seed**        | Int           | 0           | Random seed.                                                |
+-----------------+---------------+-------------+-------------------------------------------------------------+

Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**
- **Polygons**

Examples of usage
-----------------

Default settings:

.. image:: https://cloud.githubusercontent.com/assets/284644/5963876/c0610f16-a811-11e4-9522-b04235965b9e.png

Using ``toothing`` parameter together with randomization, it is possible to generate something like stone wall:

.. image:: https://cloud.githubusercontent.com/assets/284644/5963875/c060de42-a811-11e4-8690-555df7cceae9.png

A honeycomb structure:

.. image:: https://cloud.githubusercontent.com/assets/284644/5963535/0b8c62f4-a80f-11e4-91be-f1406a470dbb.png

Wood floor:

.. image:: https://cloud.githubusercontent.com/assets/284644/5963877/c062022c-a811-11e4-88cc-0f24380a4324.png

An example of more complex setup:

.. image:: https://cloud.githubusercontent.com/assets/284644/5963534/0b561d5c-a80f-11e4-88a7-f5f54a277c81.png

