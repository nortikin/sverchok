Vector Interpolation
====================

.. image:: https://user-images.githubusercontent.com/14288520/189502489-6e0aaee6-237e-4a43-a150-5648590d5a44.png
  :target: https://user-images.githubusercontent.com/14288520/189502489-6e0aaee6-237e-4a43-a150-5648590d5a44.png

Functionality
-------------

Performs linear or cubic spline interpolation based on input points by creating a function ``x,y,z = f(t)`` with ``t=[0,1]``. The interpolation is based on the distance between the input points.


Input & Output
--------------

+--------+----------+------------------------------------------------+
| socket | name         | Description                                |
+========+==============+============================================+
| input  | Vertices     | Points to interpolate                      |
+--------+--------------+--------------------------------------------+
| input  | t            | Value to interpolate                       |
+--------+--------------+--------------------------------------------+
| output | Vertices     | Interpolated points                        |
+--------+--------------+--------------------------------------------+
| output | Tangent      | Tangents at outputted vertices             |
+--------+--------------+--------------------------------------------+
| output | Tangent Norm | Normalized Tangents at outputted vertices  |
+--------+--------------+--------------------------------------------+

Parameters
----------

  - *Mode* : Interpolation method. Can be Linear or Cubic
  - *Cyclic*: Treat the input vertices as a cyclic path.
  - *Int Range*: When activated the node will expect a Integer Value in the 't' input and will create a range from 0 to 1 with the inputted steps.
  - *End Point*: (Only when Int Range is activated) If active the generated range will exclude 1. Useful when the value 0 and 1 of the interpolation is the same

Extra Parameters
----------------

  - *Knot Mode*: Used for different cubic interpolations. Can be 'Manhattan', 'Euclidean', 'Points' and 'Chebyshev'
  - *List Match*: How List should be matched
  - *Output Numpy*: Outputs numpy arrays in stead of regular python lists (makes node faster)

Examples
--------
.. image:: https://user-images.githubusercontent.com/14288520/189503211-8a5a353e-70e9-4a11-9d45-0dc997e77649.png
  :target: https://user-images.githubusercontent.com/14288520/189503211-8a5a353e-70e9-4a11-9d45-0dc997e77649.png

* TAU: Number-> :doc:`A Number </nodes/number/numbers>`
* Float Series: Number-> :doc:`Number Range </nodes/number/number_range>`
* SINE X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Sine interpolated from 5 points. The input points are shown with numbers.

.. image:: https://user-images.githubusercontent.com/14288520/189503217-b780838f-b39d-43c1-b9b6-6f658bf6fd72.png
  :target: https://user-images.githubusercontent.com/14288520/189503217-b780838f-b39d-43c1-b9b6-6f658bf6fd72.png

* Float Series: Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Struct-> :doc:`List Flip </nodes/list_struct/flip>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`

An interpolated surface between sine and cosine.

.. image:: https://user-images.githubusercontent.com/14288520/189502495-367f3e94-0332-4195-a62d-b3dac66221b8.png
  :target: https://user-images.githubusercontent.com/14288520/189502495-367f3e94-0332-4195-a62d-b3dac66221b8.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* SINE X, COSINE X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* List->List Struct-> :doc:`List Flip </nodes/list_struct/flip>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

An interpolated surface between sine, cosine, sine.

.. image:: https://user-images.githubusercontent.com/14288520/189502741-1c168af8-e51d-4e19-8f6c-b5bf1355a4d4.gif
  :target: https://user-images.githubusercontent.com/14288520/189502741-1c168af8-e51d-4e19-8f6c-b5bf1355a4d4.gif

Notes
-------

The node doesn't extrapolate. Values outside of ``[0, 1]`` are ignored.

See also
--------

* Number-> :doc:`Mix Inputs </nodes/number/mix_inputs>`
* Matrix-> :doc:`Matrix Interpolation </nodes/matrix/interpolation>`
