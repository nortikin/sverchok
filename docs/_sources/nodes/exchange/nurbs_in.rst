NURBS Input
===========

.. image:: https://github.com/user-attachments/assets/07f09b8e-1434-4e5f-a7ce-5372c1a87aeb
  :target: https://github.com/user-attachments/assets/07f09b8e-1434-4e5f-a7ce-5372c1a87aeb

Dependencies
------------

This node can optionally use Geomdl_ library.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/

Functionality
-------------

This node allows to bring NURBS_ Curve and / or Surface objects from Blender's scene into Sverchok.

.. _NURBS: https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline

Additional description see :doc:`Get Objects Data </nodes/scene/get_objects_data>`.

If objects has red color then they cannot be used as NURBS (Mesh, Nurbs, Empty, Lamp and other). If collection has red color then some objects cannot be used as NURBS.

  .. image:: https://github.com/user-attachments/assets/e3d10f06-7791-4f79-bfcd-3088e049d8af
    :target: https://github.com/user-attachments/assets/e3d10f06-7791-4f79-bfcd-3088e049d8af

Unprocessed objects also shown in the node buttom with yellow color.

Inputs
------

Objects Socket. You can select object or link to Collection picker node to select a collection.

Operators
---------

This node has the following operator button:

* **GET Selection**. When pressed, the node will update the list of objects bringed into
  Sverchok with a list of currently selected objects. If there are objects
  along selected ones, which are not NURBS curves or surfaces, the node will
  skip them.

Parameters
----------

This node has the following parameters:

* **Implementation**. This defines the implementation of NURBS mathematics to be used. The available options are:

  * **Geomdl**. Use Geomdl_ library. This option is available only when Geomdl package is installed.
  * **Sverchok**. Use built-in Sverchok implementation.
  
  In general, built-in implementation should be faster; but Geomdl implementation is better tested.
  The default option is **Geomdl**, when it is available; otherwise, built-in implementation is used.

* **Sort**. If checked, the node will sort selected objects by name. Checked by default.
* **Apply matrices**. If checked, the node will apply all transforms to
  Blender's objects before bringing the coordinates into Sverchok. Checked by
  default.

In the lower part of the node, the list of currently imported objects is shown.

