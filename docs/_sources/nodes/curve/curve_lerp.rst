Curve Lerp
==========

.. image:: https://user-images.githubusercontent.com/14288520/211165837-39a6b37f-d3e0-4c1d-bf6f-6eeaa8805e75.png
  :target: https://user-images.githubusercontent.com/14288520/211165837-39a6b37f-d3e0-4c1d-bf6f-6eeaa8805e75.png

Functionality
-------------

This node generates a linear interpolation ("lerp") between two curves. More
precisely, it generates a curve, each point of which is calculated by linear
interpolation of two corresponding points on two other curves.

.. image:: https://user-images.githubusercontent.com/14288520/211166063-a3dc6c4f-6ed2-4321-a88c-169d36f828ee.png
  :target: https://user-images.githubusercontent.com/14288520/211166063-a3dc6c4f-6ed2-4321-a88c-169d36f828ee.png

If the coefficient value provided is outside `[0 .. 1]` range, then the node
will calculate linear extrapolation instead of interpolation.

.. image:: https://user-images.githubusercontent.com/14288520/211166242-49779c9d-e6d5-47c5-9090-568f387713d0.png
  :target: https://user-images.githubusercontent.com/14288520/211166242-49779c9d-e6d5-47c5-9090-568f387713d0.png

Inputs
------

This node has the following inputs:

* **Curve1**. The first curve. This input is mandatory.
* **Curve2**. The second curve. This input is mandatory.
* **Coefficient**. The interpolation coefficient. When it equals to 0, the
  resulting curve will be the same as **Curve1**. When the coefficient is 1.0,
  the resulting curve will be the same as **Curve2**. The default value is 0.5,
  which is something in the middle.

.. image:: https://user-images.githubusercontent.com/14288520/211166461-2487e5d9-ea83-4d30-9872-2f2f2350c1c5.png
  :target: https://user-images.githubusercontent.com/14288520/211166461-2487e5d9-ea83-4d30-9872-2f2f2350c1c5.png

Outputs
-------

This node has the following output:

* **Curve**. The interpolated curve.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/211166583-a13c966d-efd9-4fdb-9055-ec3a97dbcd7f.png
  :target: https://user-images.githubusercontent.com/14288520/211166583-a13c966d-efd9-4fdb-9055-ec3a97dbcd7f.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

---------

Several curves calculated as linear interpolation between half a circle and a straight line segment:

.. image:: https://user-images.githubusercontent.com/14288520/211166710-5e0a177e-971e-4ebf-a2e4-35da6b3cbfbb.png
  :target: https://user-images.githubusercontent.com/14288520/211166710-5e0a177e-971e-4ebf-a2e4-35da6b3cbfbb.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Curves->Curve Primitives-> :doc:`Line (Curve) </nodes/curve/line>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`