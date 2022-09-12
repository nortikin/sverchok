Smooth Numbers
==============

.. image:: https://user-images.githubusercontent.com/14288520/189191850-160c4369-0afa-46c2-af21-8673dc287ed6.png
  :target: https://user-images.githubusercontent.com/14288520/189191850-160c4369-0afa-46c2-af21-8673dc287ed6.png

This node smooths a number list by reducing the difference between consecutive numbers.

This node will accept flat Numpy arrays and can will out them if *Output Numpy* is activated.

This node will accept any list shape (vectorized).

Input and Output
----------------


+-------------------+-------------------------------+
| socket            | description                   |
+===================+===============================+
| **inputs**        |                               |
+-------------------+-------------------------------+
| Values            | lists to smooth               |
+-------------------+-------------------------------+
| Iterations        | number of smoothing iterations|
+-------------------+-------------------------------+
| Factor            | smoothing factor              |
+-------------------+-------------------------------+
| **outputs**       |                               |
+-------------------+-------------------------------+
| Out               | outcoming lists               |
+-------------------+-------------------------------+

Options
-------

* **Cyclic**: Smooth first value with last value and last with first.

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

* **Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster).
* **List Match**: Define how list with different lengths should be matched.


Examples
--------

Basic example:

.. image:: https://user-images.githubusercontent.com/10011941/98470033-5f97aa80-21e3-11eb-865a-141797498440.png
    :target: https://user-images.githubusercontent.com/10011941/98470033-5f97aa80-21e3-11eb-865a-141797498440.png

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Viz-> :doc:`Viewer 2D </nodes/viz/viewer_2d>`
