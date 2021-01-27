Segment generator
=================

.. image:: https://user-images.githubusercontent.com/28003269/72606242-ac01b900-3937-11ea-9cb5-1e7b67c00bca.png

Functionality
-------------

The node creates segments between two given points. Also number of subdivisions can be set.

Category
--------

Generators -> Segment

Inputs
------

- **A** - 1 vertices
- **B** - 2 vertices
- **Num cuts** - number of line subdivision

Outputs
-------

- **Verts** - coordinates of line(s)
- **Edges** - just edges

Parameters
----------

+---------------+---------------+--------------+---------------------------------------------------------+
| Param         | Type          | Default      | Description                                             |
+===============+===============+==============+=========================================================+
| **Cute modes**| Enum          | "Cuts"       | **Cuts** - cut line evenly                              | 
|               |               |              | **Steps** - cut line proportionally by given steps      |
+---------------+---------------+--------------+---------------------------------------------------------+
| **Split to    | Boolean       |              |                                                         |
| objects**     | (N panel)     | True         | Each line will be put to separate object any way        |
+---------------+---------------+--------------+---------------------------------------------------------+
| **Numpy       | Boolean       | False        | Convert vertices to Numpy array                         |
| output**      | (N panel)     |              |                                                         |
+---------------+---------------+--------------+---------------------------------------------------------+

Example of usage
----------------


.. image:: https://user-images.githubusercontent.com/28003269/72215874-bdf7ec00-3532-11ea-9e50-41234fe02862.png
  :alt: LineDemo4.PNG

The AB mode will output a divided segment for each vector pair, the step can be used to change the proportions of the divisions


.. image:: https://user-images.githubusercontent.com/28003269/72215940-b5ec7c00-3533-11ea-92e5-e3965487a8c1.png
  :alt: LineDemo5.PNG

Advanced example using the node to create a paraboloid grid