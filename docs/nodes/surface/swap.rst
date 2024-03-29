Swap Surface U/V
================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/fb6fb6f2-b9f2-4079-810e-90e9d32e7a49
  :target: https://github.com/nortikin/sverchok/assets/14288520/fb6fb6f2-b9f2-4079-810e-90e9d32e7a49

Functionality
-------------

This node generates a Surface by swapping U and V directions of another Surface
parametrizations. More precisely, given the surface defined by formula `P =
S(U, V)`, it generates the surface defined by formula `P = S(V, U)`. This is
the same surface as the original one, but with another paramertization.

Swapping surface's parametrization direction flips the surface's normals.

Surface domain: in the U direction - the same as of original surface in the V
direction; and vice versa, in the V direction - the same as of original surface
in the U direction.

Inputs
------

This node has the following input:

* **Surface**. The surface to be processed. This input is mandatory.

Outputs
-------

This node has the following output:

* **Surface**. The new surface.

Example of usage
----------------

Let's generate a grid on some surface with 30 samples in U direction and 10
samples in V direction. Then we can see that directions are swapped by this
node:

.. image:: https://user-images.githubusercontent.com/284644/80011794-c8d4fc00-84e5-11ea-9030-266c178e1aee.png
  :target: https://user-images.githubusercontent.com/284644/80011794-c8d4fc00-84e5-11ea-9030-266c178e1aee.png

* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Surfaces-> :doc:`Extrude Curve Along Vector </nodes/surface/extrude_vector>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`