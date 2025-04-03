Vector Out
==========

.. image:: https://user-images.githubusercontent.com/14288520/189363994-5d4a10e0-1214-4cc3-991c-50535995d81b.png
  :target: https://user-images.githubusercontent.com/14288520/189363994-5d4a10e0-1214-4cc3-991c-50535995d81b.png

Functionality
-------------

Outputs values/numbers from vertices.

The node will accept regular lists or lists of NumPy arrays if the arrays have two axis arrays with shape [n,3]

It can also output Numpy arrays (flat arrays) when using the activating the "Output NumPy" parameter.
(See advanced parameters)

Inputs
-------

* **Vector** - Vertex or series of vertices

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

* **Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster if you input NumPy arrays).

Outputs
-------

* **x** - velue or series of values
* **y** - velue or series of values
* **z** - velue or series of values

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/189367049-f6d0eb90-7f51-46df-a19d-213a43f9e013.png
  :target: https://user-images.githubusercontent.com/14288520/189367049-f6d0eb90-7f51-46df-a19d-213a43f9e013.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/189364026-1e67ba74-a594-4106-bc42-200caa1a99bf.png
  :target: https://user-images.githubusercontent.com/14288520/189364026-1e67ba74-a594-4106-bc42-200caa1a99bf.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* SINCOS X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`