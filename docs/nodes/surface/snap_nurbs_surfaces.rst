Snap NURBS Surfaces
===================

Functionality
-------------

This node can adjust two NURBS surfaces in such a way that their edges would
coincide. Optionally, it can adjust their tangents along the seam.

After snapping, it is possible to join surfaces into one Surface object with
"Concatenate Surfaces" node.

This node is somewhat similar to "Snap Curves" node.

Inputs
------

This node has the following inputs:

* **Surfaces**. Surfaces to be adjusted. This input is only available when
  the **Input mode** parameter is set to **List of Surfaces**. The edges of
  surfaces which will be adjusted are selected according to the order the
  surfaces are present in this list.
**Surface1**, **Surface2**. Surfaces to be adjusted. These inputs are
  only available when the **Input mode** parameter is set to **Two Surfaces**.

Parameters
----------

This node has the following parameters:

* **Input mode**. The available modes are **Two surfaces** and **List of
  surfaces**. The default mode is **Two surfaces**.
* **Direction**. Surface parameter direction along which the surfaces are
  arranged. The available options are **U** and **V**. The default option
  is **U**.
* **Bias**. This defines where the seam curve, along which the edges of two
  surfaces will coincide, will be. The following options are available:

  * **Middle line**. Both surfaces will be adjusted, and the seam line will be
    the medium line between edges of two original surfaces. This is the default
    option.
  * **Surface 1**. The edge of the first surface will be left in place. The
    second surface will be adjusted in such a way that it's edge coincides with
    the edge of the first surface.
  * **Surface 2**. The edge of the second surface will be left in place. The
    first surface will be adjusted in such a way that it's edge coincides with
    the edge of the second surface.

* **Tangents**. This defines what should be done with tangents of the surfaces
  along the seam line. The available options are:

  * **No matter**. The surfaces will be adjusted in such a way that total
    movement of their control points is minimal; the procedure will not
    consider tangents at all. In some cases the tangents can be changed, in
    some they will not change. This is the default option.
  * **Preserve**. The surfaces will be adjusted in such a way that their
    tangents along the seam are not changed.
  * **Medium**. Tangents of both surfaces will be adjusted; the resulting
    tangent vectors will be average between tangent vectors of the first and
    the second surface.
  * **Surface 1**. Tangents of the first surface will be left as is. Tangents
    of the second surface will be adjusted in order to match the tangents of
    the first surface.
  * **Surface 2**. Tangents of the second surface will be left as is. Tangents
    of the first surface will be adjusted in order to match the tangents of the
    second surface.

* **Cyclic**. If checked, the node will snap surfaces in cycle, i.e. it will
  snap the last surface to the first one. Unchecked by default.

Outputs
-------

This node has the following output:

* **Surfaces**. Adjusted surfaces.

Examples of Usage
-----------------

Original surfaces:

.. image:: https://github.com/user-attachments/assets/55777cb4-9e9b-479b-96bb-b68c309be362
  :target: https://github.com/user-attachments/assets/55777cb4-9e9b-479b-96bb-b68c309be362

Snap them with default settings - to middle line, not taking tangents into account:

.. image:: https://github.com/user-attachments/assets/52783655-ed26-4922-bf9c-1cc310dec0b6
  :target: https://github.com/user-attachments/assets/52783655-ed26-4922-bf9c-1cc310dec0b6

With "preserve tangents" option (tangent vectors of both original surfaces along V direction are horizontal):

.. image:: https://github.com/user-attachments/assets/3097e73f-c8a2-4ccb-9a35-09de28931909
  :target: https://github.com/user-attachments/assets/3097e73f-c8a2-4ccb-9a35-09de28931909

Snap second surface to the first one, not taking tangents into account:

.. image:: https://github.com/user-attachments/assets/db76fe80-5d02-456d-9bd7-8970d72d0933
  :target: https://github.com/user-attachments/assets/db76fe80-5d02-456d-9bd7-8970d72d0933

Snap first surface to the second one, not taking tangents into account:

.. image:: https://github.com/user-attachments/assets/1010e4a2-5c96-4450-9e8c-515a302d813a
  :target: https://github.com/user-attachments/assets/1010e4a2-5c96-4450-9e8c-515a302d813a

Now match tangents as well:

.. image:: https://github.com/user-attachments/assets/7879dcd9-c1d6-46f0-b2a7-d34a61c057e9
  :target: https://github.com/user-attachments/assets/7879dcd9-c1d6-46f0-b2a7-d34a61c057e9

Four original surfaces:

.. image:: https://github.com/user-attachments/assets/cf96022b-56be-4311-8bef-4df5a15ab451
  :target: https://github.com/user-attachments/assets/cf96022b-56be-4311-8bef-4df5a15ab451

Snap them in cyclic manner, with "preserve tangents" option:

.. image:: https://github.com/user-attachments/assets/914539d1-c6f8-4d1f-a024-ea9e6e45ba5b
  :target: https://github.com/user-attachments/assets/914539d1-c6f8-4d1f-a024-ea9e6e45ba5b

With "medium tangents" mode:

.. image:: https://github.com/user-attachments/assets/3a151a5f-6531-4339-a35f-2df64f2ff1c8
  :target: https://github.com/user-attachments/assets/3a151a5f-6531-4339-a35f-2df64f2ff1c8

