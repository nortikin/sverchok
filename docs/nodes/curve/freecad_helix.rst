Helix (FreeCAD)
===============

.. image:: https://user-images.githubusercontent.com/14288520/205449851-57e0b8d9-0cd0-4dd8-86a2-44eb8391694a.png
  :target: https://user-images.githubusercontent.com/14288520/205449851-57e0b8d9-0cd0-4dd8-86a2-44eb8391694a.png

Dependencies
------------

This node requires FreeCAD_ libraries installed to work.

.. _FreeCAD: https://www.freecadweb.org/

Functionality
-------------

This node generates a helix Curve. The helix can be either cylyndrical (by default) or conical.

The produced Curve object is NURBS-like, i.e. will be automatically converted
to NURBS by nodes which require NURBS curves.

.. image:: https://user-images.githubusercontent.com/14288520/205449936-94831101-2ca4-486a-addc-6b9a29f1e332.png
  :target: https://user-images.githubusercontent.com/14288520/205449936-94831101-2ca4-486a-addc-6b9a29f1e332.png

Inputs
------

This node has the following inputs:

* **Radius**. Helix radius. The default value is 1.0.

.. image:: https://user-images.githubusercontent.com/14288520/205450690-2ca55bd7-4db3-44f6-b51d-6c3b89f4eee3.png
  :target: https://user-images.githubusercontent.com/14288520/205450690-2ca55bd7-4db3-44f6-b51d-6c3b89f4eee3.png

* **Height**. Helix height. The default value is 4.0.

.. image:: https://user-images.githubusercontent.com/14288520/205450642-a427d6f1-9a20-451b-a89c-11a3c9a1c34e.png
  :target: https://user-images.githubusercontent.com/14288520/205450642-a427d6f1-9a20-451b-a89c-11a3c9a1c34e.png

* **Pitch**. Helix pitch, i.e. the distance between turns of the helix. The
  default value is 1.0.

.. image:: https://user-images.githubusercontent.com/14288520/205450756-53ada085-4470-4186-b89c-8b30ec9b4b8d.png
  :target: https://user-images.githubusercontent.com/14288520/205450756-53ada085-4470-4186-b89c-8b30ec9b4b8d.png

* **Angle**. Apex angle of the cone for conic helixes, in degrees; when this is
  set to 0 (by default), the node will generate a cylindrical helix. (0 is minimum)

.. image:: https://user-images.githubusercontent.com/14288520/205450833-915fa8bb-170b-46e3-9ee4-c6a126fe7166.png
  :target: https://user-images.githubusercontent.com/14288520/205450833-915fa8bb-170b-46e3-9ee4-c6a126fe7166.png

Parameters
----------

This node has the following parameter:

* **Join**. When checked, the node will generate one flat list of Curves for
  all values in the input. If not checked, the node will produce a separate
  list of Curves for each list of input parameters. Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205451179-09b64530-a022-4b43-80e7-2491f32a488b.png
  :target: https://user-images.githubusercontent.com/14288520/205451179-09b64530-a022-4b43-80e7-2491f32a488b.png

* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Outputs
-------

This node has the following output:

* **Curve**. The generated helix Curve object.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/205451285-6605bff1-e52f-470f-8d29-85d30a2f2f73.png
  :target: https://user-images.githubusercontent.com/14288520/205451285-6605bff1-e52f-470f-8d29-85d30a2f2f73.png

* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`