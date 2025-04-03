Split Curve
===========

.. image:: https://github.com/nortikin/sverchok/assets/14288520/5e36b51e-038d-445c-aec8-10dec10c89b4
  :target: https://github.com/nortikin/sverchok/assets/14288520/5e36b51e-038d-445c-aec8-10dec10c89b4

Functionality
-------------

This node splits one Curve object into several Curves, by dividing it at some
values of curve's T parameter. The values of T parameter, at which the split
should be made, can be either specified manually or calculated automatically by
the provided number of cuts.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/82e7bb2f-e506-410e-9920-7dec012f12f2
  :target: https://github.com/nortikin/sverchok/assets/14288520/82e7bb2f-e506-410e-9920-7dec012f12f2

* List->List Main-> :doc:`List Decompose </nodes/list_main/decompose>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

Note that equal ranges of T parameter do not necessarily mean equal parts of
curve length. To split a curve into parts of equal length, you can use "Curve
Length Parameter" node to calculate corresponding values of the T parameter.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/5482cd05-1032-400d-bc0c-e2a2073d8a57
  :target: https://github.com/nortikin/sverchok/assets/14288520/5482cd05-1032-400d-bc0c-e2a2073d8a57

* Curves-> :doc:`Curve Length Parameter </nodes/curve/length_parameter>`
* Curves-> :doc:`Curve Length Parameter </nodes/curve/curve_length>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* List->List Main-> :doc:`List Decompose </nodes/list_main/decompose>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

Inputs
------

This node has the following inputs:

* **Curve**. The curve to be split. This input is mandatory.
* **Segments**. Number of pieces the curve is to be split into. This input is
  available only if **Mode** parameter is set to **Even**. The default value is

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/0cff5691-d921-4d41-a152-34beac4ab24e
      :target: https://github.com/nortikin/sverchok/assets/14288520/0cff5691-d921-4d41-a152-34beac4ab24e


* **Split**. The value of curve's T parameter, at which the curve is to be
  split. This input is only available when **Mode** parameter is set to
  **Explicit**. This input can consume several values per each curve. The
  default value is 0.5.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/f3cdf824-c6ef-4cae-b704-f6aae8aadf43
      :target: https://github.com/nortikin/sverchok/assets/14288520/f3cdf824-c6ef-4cae-b704-f6aae8aadf43

Parameters
----------

This node has the following parameters:

* **Mode**. This defines how the values of curve's T parameter, at which the
  curve is to be split, are determined. The available options are:

  * **Even**. The curve will be split by even ranges of T parameter. Number of
    pieces to split into is defined in the **Segments** input. For example, if
    curve domain is ``[0; 1]``, and **Segments** input is set to ``2``, then
    the curve will be split into two segments with domains of ``[0; 0.5]`` and
    ``[0.5; 1]``.
  * **Explicit**. The values of T parameter are provided in the **Split** input.

* **Recale to 0..1**. If checked, then parametrizations of generated Curve
  objects will be adjusted, so that each of them will have domain of ``[0;
  1]``. Otherwise, the domain of generated Curve objects will be equal to
  corresponding part of initial curve's domain. Unchecked by default.
* **Join**. If checked, then the node will generate single list of pieces for
  each provided list of Curve objects. Otherwise, the node will generate
  separate list of pieces for each provided Curve object. Unchecked by default.

Outputs
-------

This node has the following output:

* **Curves**. The generated Curve objects.

Examples of usage
-----------------

Split a Circle (which has domain ``[0; 2*pi]``) at point T = 0.5:

.. image:: https://user-images.githubusercontent.com/284644/82467377-09bb3300-9adb-11ea-9590-64b332443621.png
  :target: https://user-images.githubusercontent.com/284644/82467377-09bb3300-9adb-11ea-9590-64b332443621.png

* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Split a Circle into 5 pieces:

.. image:: https://user-images.githubusercontent.com/284644/82467383-0aec6000-9adb-11ea-9024-2f2b749198d7.png
  :target: https://user-images.githubusercontent.com/284644/82467383-0aec6000-9adb-11ea-9024-2f2b749198d7.png

* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`