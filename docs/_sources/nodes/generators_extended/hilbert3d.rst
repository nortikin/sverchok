Hilbert 3D
==========

.. image:: https://user-images.githubusercontent.com/14288520/190921909-a3fd72db-4f72-4d73-9989-335a5fe4c32b.png
  :target: https://user-images.githubusercontent.com/14288520/190921909-a3fd72db-4f72-4d73-9989-335a5fe4c32b.png

.. image:: https://user-images.githubusercontent.com/14288520/190922073-abf79829-35e3-4ece-a351-60e8e964ed11.png
  :target: https://user-images.githubusercontent.com/14288520/190922073-abf79829-35e3-4ece-a351-60e8e964ed11.png

Functionality
-------------

Hilbert space generator. This is a concept of dense flooding of space by continuous line that is achieved with division and special knotting. Hilbert space can be only square, because of its nature.

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

.. image:: https://user-images.githubusercontent.com/14288520/190921917-251ad090-c53a-4452-ac2a-9f9d7f40b816.png
  :target: https://user-images.githubusercontent.com/14288520/190921917-251ad090-c53a-4452-ac2a-9f9d7f40b816.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector Interpolation </nodes/vector/interpolation_mk3>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/190922164-a87b2927-23c8-4ee8-957a-c3512669f91f.gif
  :target: https://user-images.githubusercontent.com/14288520/190922164-a87b2927-23c8-4ee8-957a-c3512669f91f.gif

Smooth labyrinth
