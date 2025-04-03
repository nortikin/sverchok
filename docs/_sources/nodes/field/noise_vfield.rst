Noise Vector Field
==================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/3506be1a-cde3-4e39-b220-07a350309750
  :target: https://github.com/nortikin/sverchok/assets/14288520/3506be1a-cde3-4e39-b220-07a350309750

Functionality
-------------

This node generates a Vector Field, which is defined by one of several noise types supported.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/5eb1f27c-537d-466b-8551-0f74b33e12c2
  :target: https://github.com/nortikin/sverchok/assets/14288520/5eb1f27c-537d-466b-8551-0f74b33e12c2

Inputs
------

This node has the following input:

* **Seed**. The noise seed.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/4decf713-6ffa-4acd-85e5-bba21ffe9c7e
  :target: https://github.com/nortikin/sverchok/assets/14288520/4decf713-6ffa-4acd-85e5-bba21ffe9c7e

Parameters
----------

This node has the following parameter:

* **Type**. The type of noise. The available values are:

  * **Blender**
  * **Perlin Original**
  * **Perlin New**
  * **Voronoi F1**
  * **Voronoi F2**
  * **Voronoi F3**
  * **Voronoi F4**
  * **Voronoi F2F1**
  * **Voronoi Crackle**
  * **Cellnoise**

.. image:: https://github.com/nortikin/sverchok/assets/14288520/7c8265c6-6dd7-4ffa-bd5f-74bc5aab79ec
  :target: https://github.com/nortikin/sverchok/assets/14288520/7c8265c6-6dd7-4ffa-bd5f-74bc5aab79ec


Outputs
-------

This node has the following output:

* **Noise**. The generated vector field.

Example of usage
----------------

Visualize the noise field:

.. image:: https://user-images.githubusercontent.com/284644/79488796-b8c7a300-8033-11ea-956c-fc66819a0aed.png
  :target: https://user-images.githubusercontent.com/284644/79488796-b8c7a300-8033-11ea-956c-fc66819a0aed.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Vector Field Graph </nodes/field/vector_field_graph>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/2b3e3067-8422-4024-9a9a-fb9444eb1273
  :target: https://github.com/nortikin/sverchok/assets/14288520/2b3e3067-8422-4024-9a9a-fb9444eb1273

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Fields-> :doc:`Evaluate Vector Field </nodes/field/vector_field_eval>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`