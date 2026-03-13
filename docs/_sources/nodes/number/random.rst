Random
======

.. image:: https://user-images.githubusercontent.com/14288520/189146711-488eca42-a734-498a-b6de-9f28b3d8a1f2.png
  :target: https://user-images.githubusercontent.com/14288520/189146711-488eca42-a734-498a-b6de-9f28b3d8a1f2.png
  :alt: NumberRandomDemo1.PNG

Functionality
-------------

Produces a list of random numbers (0.0-1.0) from a seed value.


Inputs & Parameters
-------------------

+------------+-------------------------------------------------------------------------+
| Parameters | Description                                                             |
+============+=========================================================================+
| Count      | Number of random numbers to spit out                                    |
+------------+-------------------------------------------------------------------------+
| Seed       | Accepts float values, they are hashed into *Integers* internally.       |
+------------+-------------------------------------------------------------------------+

What's a Seed? Read the `Python docs here <https://docs.python.org/3.4/library/random.html>`_

Outputs
-------

A list, or nested lists.

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/189147541-7b5561dd-3fdf-4b70-b3b9-2ec7239eb5da.png
  :target: https://user-images.githubusercontent.com/14288520/189147541-7b5561dd-3fdf-4b70-b3b9-2ec7239eb5da.png
  :alt: NumberRandomDemo2.PNG

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Notes
-----

Providing a float values as a Seed parameter may be unconventional, if you are uncomfortable with it you 
could place a :doc:`Number->Float to Integer </nodes/number/float_to_int>` node before the Seed parameter. We may add more Random Nodes in future.



Remark
------

For random numeric list see:

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>` (int/float, range)

For random vector list see:

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`