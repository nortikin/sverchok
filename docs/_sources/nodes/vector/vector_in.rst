Vector In
=========

.. image:: https://user-images.githubusercontent.com/14288520/189356797-4908a913-cdcc-49e9-8100-0bbcc5e3e9b1.png
  :target: https://user-images.githubusercontent.com/14288520/189356797-4908a913-cdcc-49e9-8100-0bbcc5e3e9b1.png

Functionality
-------------

Inputs vector from ranges or number values either integer of floats.

With the NumPy implementation the node will accept regular lists or lists of flat NumPy arrays

It can also output Numpy arrays (flat arrays) when using the activating the "Output NumPy" parameter.
(See advanced parameters)

Inputs
------

* **x** - value or series of values
* **y** - value or series of values
* **z** - value or series of values

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

* **Implementation**: Python or NumPy. Python is the default and is usually faster if you input regular lists and want to get regular list. The NumPy implementation will be faster if you are using/getting lists of NumPy arrays.
* **Output NumPy**: Get NumPy arrays in stead of regular lists.

Outputs
-------

* **Vector** - Vertex or series of vertices

Operators
---------

This node has two buttons:

- **3D Cursor**. This button is available only when no of inputs are connected. When pressed, this button assigns current location of Blender's 3D Cursor to X, Y, Z parameters.

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/189362245-d966cf84-da93-4da5-b137-bf578c3f2c6f.png
  :target: https://user-images.githubusercontent.com/14288520/189362245-d966cf84-da93-4da5-b137-bf578c3f2c6f.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/189359236-785757e5-a1c4-4dfa-86d9-65780cee1bd9.png
  :target: https://user-images.githubusercontent.com/14288520/189359236-785757e5-a1c4-4dfa-86d9-65780cee1bd9.png
  :alt: with vector out

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Sine X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector Out </nodes/vector/vector_out>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/189359252-e2bc72dd-03b2-427a-8c49-9d6cb8aaeeac.png
  :target: https://user-images.githubusercontent.com/14288520/189359252-e2bc72dd-03b2-427a-8c49-9d6cb8aaeeac.png
  :alt: generating line

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Sine X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/189359290-0879acdc-1ebb-4351-a9f1-789f387b834b.png
  :target: https://user-images.githubusercontent.com/14288520/189359290-0879acdc-1ebb-4351-a9f1-789f387b834b.png
  :alt: object mode

* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Gist: https://gist.github.com/cf884ea62f9960d609158ef2d5c994ed