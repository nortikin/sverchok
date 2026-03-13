Hilbert Image
=============

.. image:: https://user-images.githubusercontent.com/14288520/190923031-984b0fa2-2f00-434a-8167-0ecdfc53ed2c.png
  :target: https://user-images.githubusercontent.com/14288520/190923031-984b0fa2-2f00-434a-8167-0ecdfc53ed2c.png

.. image:: https://user-images.githubusercontent.com/14288520/190923242-eebb4258-726b-44b5-bf37-b52c606698a4.png
  :target: https://user-images.githubusercontent.com/14288520/190923242-eebb4258-726b-44b5-bf37-b52c606698a4.png

Functionality
-------------

Hilbert image recreator. Based on hilbert space this node recreates image by interpolating it on pixels.

Inputs
------

- **level**
- **size**
- **sensitivity**

Parameters
----------

All parameters can be given by the node or an external input.


+-----------------+---------------+-------------------+----------------------------------------------------------+
| Param           |  Type         |   Default         |    Description                                           |
+=================+===============+===================+==========================================================+
| **RGB**         |  float        |   0.3,0.59,0.11   |    RGB map of imported image, sensitivity to each color  |
+-----------------+---------------+-------------------+----------------------------------------------------------+
| **image name**  |  string       |   None            |    enumerate popup to choose image from stack            |
+-----------------+---------------+-------------------+----------------------------------------------------------+
| **level**       |  Int          |   2               |    level of division of hilbert square                   |
+-----------------+---------------+-------------------+----------------------------------------------------------+
| **size**        |  float        |   1.0             |    scale of hilbert mesh                                 |
+-----------------+---------------+-------------------+----------------------------------------------------------+
| **sensitivity** |  float        |   1.0             |    define scale of values to react and build image       |
+-----------------+---------------+-------------------+----------------------------------------------------------+

Outputs
-------

**Vertices**, **Edges**.


Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/190923480-1134ce55-2368-4c10-8796-06f4b0fa503b.png
  :target: https://user-images.githubusercontent.com/14288520/190923480-1134ce55-2368-4c10-8796-06f4b0fa503b.png

* List->List Struct-> :doc:`List Levels </nodes/list_struct/levels>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer 2D </nodes/viz/viewer_2d>`

recreate image in hilbert
