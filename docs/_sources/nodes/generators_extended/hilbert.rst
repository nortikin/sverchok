Hilbert 2D
=======================

.. image:: https://user-images.githubusercontent.com/14288520/190921280-45ba5060-cf5e-472b-b67e-e19102a5f5a5.png
  :target: https://user-images.githubusercontent.com/14288520/190921280-45ba5060-cf5e-472b-b67e-e19102a5f5a5.png

.. image:: https://user-images.githubusercontent.com/14288520/190921636-b16c3c7e-d641-4fc2-b3f5-c78aff3780ea.png
  :target: https://user-images.githubusercontent.com/14288520/190921636-b16c3c7e-d641-4fc2-b3f5-c78aff3780ea.png

Functionality
-------------

Hilbert field generator. This is a concept of dense flooding of space by continuous line that is achieved with division and special knotting. Hilbert space can be only square, because of its nature.

Inputs
------

All inputs are not vectorized and they will accept single value.
There is two inputs:

- **level**
- **size**

Parameters
----------

All parameters can be given by the node or an external input.


+-------------+---------------+-------------+------------------------------------------+
| Param       |  Type         |   Default   |    Description                           |
+=============+===============+=============+==========================================+
| **level**   |  Int          |   2         |    level of division of Hilbert square   |
+-------------+---------------+-------------+------------------------------------------+
| **size**    |  float        |   1.0       |    scale of Hilbert mesh                 |
+-------------+---------------+-------------+------------------------------------------+

Outputs
-------

**Vertices**, **Edges**.


Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/190921736-74414885-b68e-49a3-ae61-b930fd86ac7a.png
  :target: https://user-images.githubusercontent.com/14288520/190921736-74414885-b68e-49a3-ae61-b930fd86ac7a.png

* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector Interpolation </nodes/vector/interpolation_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Smooth labyrinth
