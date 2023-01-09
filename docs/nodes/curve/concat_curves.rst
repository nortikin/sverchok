Concatenate Curves
==================

.. image:: https://user-images.githubusercontent.com/14288520/211277635-e2739eca-904c-4635-a0ab-14b71ba85a35.png
  :target: https://user-images.githubusercontent.com/14288520/211277635-e2739eca-904c-4635-a0ab-14b71ba85a35.png

Functionality
-------------

This node composes one Curve object from several Curve objects, by "glueing"
their ends. It assumes that end points of the curves being concatenated are
already coinciding. You can make the node check this fact additionally.

Curve domain: summed up from domains of curves being concatenated.

.. image:: https://user-images.githubusercontent.com/14288520/211287456-bcbb6644-580b-40f5-b387-abdc4f2b94cc.png
  :target: https://user-images.githubusercontent.com/14288520/211287456-bcbb6644-580b-40f5-b387-abdc4f2b94cc.png

Inputs
------

This node has the following input:

* **Curves**. A list of curves to be concatenated. This input is mandatory.

Parameters
----------

This node has the following parameters:

* **Check coincidence**. If enabled, then the node will check that the end points of curves being concatenated do actually coincide (within threshold). If they do not, the node will give an error (become red), and the processing will stop.
* **Max distance**. Maximum distance between end points of the curves, which is allowable to decide that they actually coincide. The default value is 0.001. This parameter is only available if **Check coincidence** parameter is enabled.
* **All NURBS**. This parameter is available in the N panel only. If checked,
  then the node will try to convert all input curves to NURBS, and output a
  NURBS curve. The node will fail (become red) if it was not able either to
  convert one of input curves, or join resulting NURBS curves.

Outputs
-------

This node has the following output:

* **Curve**. The resulting concatenated curve.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/211297333-4832ca4c-b0fc-489a-a7c8-91864728e1c7.png
  :target: https://user-images.githubusercontent.com/14288520/211297333-4832ca4c-b0fc-489a-a7c8-91864728e1c7.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Bezier Spline Segment (Curve) </nodes/curve/bezier_spline>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* List->List Struct-> :doc:`List First & Last </nodes/list_struct/start_end>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Make single curve from two segments of line and an arc:

.. image:: https://user-images.githubusercontent.com/14288520/211300273-6fdca411-6fb9-40df-a90b-5a9ebb13eb7a.png
  :target: https://user-images.githubusercontent.com/14288520/211300273-6fdca411-6fb9-40df-a90b-5a9ebb13eb7a.png

* Curves->Curve Primitives-> :doc:`Line (Curve) </nodes/curve/line>`
* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`