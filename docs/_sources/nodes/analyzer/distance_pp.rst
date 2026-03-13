Distance
========

.. image:: https://user-images.githubusercontent.com/14288520/195398378-5cc69e7d-4078-4f9d-aaaf-6a88f79d2c62.png
  :target: https://user-images.githubusercontent.com/14288520/195398378-5cc69e7d-4078-4f9d-aaaf-6a88f79d2c62.png

Functionality
-------------

Finds distance from point to point, from matrix to matrix or between many points and one opposite.

Inputs
------

**vertices1** and **matrix1** and **vertices2** and **matrix2**.

Parameters
----------

+---------------+-----------+----------------------------------------------------------------------------+
| Name          | Type      | Description                                                                |
+===============+===========+============================================================================+
| **CrossOver** | Boolean   | for every point finds all opposite points, not one other, but many.        |
+---------------+-----------+----------------------------------------------------------------------------+

Outputs
-------

**distances** in format [[12,13,14,15]]

Example of usage
----------------

Example cross over is Off:

.. image:: https://user-images.githubusercontent.com/14288520/195401922-d6507d35-591d-4073-8ab6-d6a4f6511567.png
  :target: https://user-images.githubusercontent.com/14288520/195401922-d6507d35-591d-4073-8ab6-d6a4f6511567.png

Example Cross Over is On:

TODO: https://github.com/nortikin/sverchok/issues/4705