Surface Domain
==============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/033bac46-e408-46bc-8a32-b61f2db43b32
  :target: https://github.com/nortikin/sverchok/assets/14288520/033bac46-e408-46bc-8a32-b61f2db43b32

Functionality
-------------

This node outputs the domain of the Surface, i.e. the range of values the surface's U and V parameters are allowed to take.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/4a2c801f-9385-4564-9fe0-cbe34213df40
  :target: https://github.com/nortikin/sverchok/assets/14288520/4a2c801f-9385-4564-9fe0-cbe34213df40

* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Surfaces-> :doc:`Surface Formula </nodes/surface/surface_formula>`

Inputs
------

This node has the following input:

* **Surface**. The surface to be measured. This input is mandatory.

Outputs
-------

This node has the following outputs:

* **UMin**, **UMax**. Minimum and maximum allowed values of surface's U parameter.
* **URange**. The length of surface's domain along U direction; this equals to the difference **UMax** - **UMin**.
* **VMin**, **VRange**. Minimum and maximum allowed values of surface's V parameter.
* **VRange**. The length of surface's domain along V direction; this equals to the difference **VMax** - **VMin**.

Example of usage
----------------

Applied to the sphere with Equirectangular parametrization:

.. image:: https://user-images.githubusercontent.com/284644/79386265-50b98400-7f83-11ea-94bb-90d30a7c710a.png

* Surfaces-> :doc:`Sphere (Surface) </nodes/surface/surface_sphere>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`