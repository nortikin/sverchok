Blend Surfaces
==============

Functionality
-------------

This node generates a Surface, which creates a smooth blend between two other
surfaces. It is possible to select which edges of surfaces must be blended.
Also it is possible to provide arbitrary curves in U/V space of each surface,
along which the blending surface must start and end.

Surface domain: from 0 to 1 in both directions.

Inputs
------

This node has the following inputs:

* **Surface1**. The first surface to make a blend with. This input is mandatory.
* **UVCurve1**. A curve in U/V space of the first surface, along which the
  blending surface must start. This input is available and mandatory only when
  **Curve1** parameter is set to **Custom**.
* **Bulge1**. Bulge factor for the place where the blending surface touches the
  first surface. Bigger values lead to more smooth touch. Negative values will
  mean that the blending surface will touch the surface from another side of
  curve / edge. The default value is 1.0.
* **Surface2**. The second surface to make a blend with. This input is mandatory.
* **UVCurve2**. A curve in U/V space of the second surface, along which the
  blending surface must end. This input is available and mandatory only when
  **Curve2** parameter is set to **Custom**.
* **Bulge2**. Bulge factor for the place where the blending surface touches the
  second surface. Bigger values lead to more smooth touch. Negative values will
  mean that the blending surface will touch the surface from another side of
  curve / edge. The default value is 1.0.

Parameters
----------

This node has the following parameters:

* **Curve1**. This defines where the blending surface should touch the first surface. The available options are:

  * **Min U**. Use the edge of the surface with the minimum value of U parameter.
  * **Max U**. Use the edge of the surface with the maximum value of U parameter.
  * **Min V**. Use the edge of the surface with the minimum value of V parameter.
  * **Max V**. Use the edge of the surface with the maximum value of V parameter.
  * **Custom**. Use arbitrary curve in the surface's U/V space, which is
    provided in the **UVCurve1** input.

  The default value is **Min U**.

* **Flip Curve 1**. If checked, the direction of curve (or edge), where the
  blending surface touches the first surface, will be reversed. Unchecked by
  default.
* **Curve2**. This defines where the blending surface should touch the second
  surface. THe available options are the same as for **Curve1** parameter. The
  default value is **Min U**.
* **Flip Curve 2**. If checked, the direction of curve (or edge), where the
  blending surface touches the second surface, will be reversed. Unchecked by
  default.

Outputs
-------

This node has the following output:

* **Surface**. The generated blending surface.

Examples of usage
-----------------

A simple example. Make two planar patches and make a blending surface, which touches them at the edges:

.. image:: https://user-images.githubusercontent.com/284644/89387742-5b5b7d00-d71c-11ea-929c-43083ab34774.png

More complex example. Similar, but for one of the patches define a circular arc
in it's U/V space, and make the blending surface touch this plane along that
circular arc:

.. image:: https://user-images.githubusercontent.com/284644/89387738-5a2a5000-d71c-11ea-9018-4d62f6eb464f.png

