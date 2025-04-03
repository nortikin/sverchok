Switch
======

.. image:: https://user-images.githubusercontent.com/14288520/189731409-413d3278-54d4-4474-be18-90d959f0cbbf.png
  :target: https://user-images.githubusercontent.com/14288520/189731409-413d3278-54d4-4474-be18-90d959f0cbbf.png

Functionality
-------------

Switches between to sets of inputs. Also can work as filter.

Category
--------

Logic -> Switch

Inputs
------

- **State** - True or False (0 or 1)
- **A_0 - 10** - True, False or None
- **B_0 - 10** - True, False or None


Outputs
-------

- **Out_0 - 10** - result of switching between two values

Parameters
----------

+--------------------------+-------+--------------------------------------------------------------------------------+
| Parameters               | Type  | Description                                                                    |
+==========================+=======+================================================================================+
| in/out number (N panel)  | 0 - 10| Number of socket sets                                                          |
+--------------------------+-------+--------------------------------------------------------------------------------+

Usage
-----

**Generation of bool sequence easily:**

.. image:: https://user-images.githubusercontent.com/14288520/189741094-76efb8cf-bc66-4887-b486-7627cd714007.png
  :target: https://user-images.githubusercontent.com/14288520/189741094-76efb8cf-bc66-4887-b486-7627cd714007.png

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

**Working with different types of data:**

.. image:: https://user-images.githubusercontent.com/14288520/189732804-2d8be7a3-ba0c-435f-9ef6-605b5044ec3c.png
  :target: https://user-images.githubusercontent.com/14288520/189732804-2d8be7a3-ba0c-435f-9ef6-605b5044ec3c.png

* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/189732604-c36ab6c1-bbb4-4eee-b745-de5cc8e1b52e.gif
  :target: https://user-images.githubusercontent.com/14288520/189732604-c36ab6c1-bbb4-4eee-b745-de5cc8e1b52e.gif

**It is possible to deal with empty objects:**

.. image:: https://user-images.githubusercontent.com/14288520/189734577-f30d7df8-ef03-4469-9a7a-09f9fd7689fa.png
  :target: https://user-images.githubusercontent.com/14288520/189734577-f30d7df8-ef03-4469-9a7a-09f9fd7689fa.png

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List-> :doc:`Filter Empty Objects </nodes/list_mutators/filter_empty_lists>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* List->List Struct-> :doc:`List Split </nodes/list_struct/split>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Script-> :doc:`Formula </nodes/script/formula_mk5>`

**Using as filter:**

.. image:: https://user-images.githubusercontent.com/14288520/189739541-753f27e2-7129-4fe7-bc29-ce49637f9491.png
  :target: https://user-images.githubusercontent.com/14288520/189739541-753f27e2-7129-4fe7-bc29-ce49637f9491.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* MODULO X, EQUAL: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

It has supporting of numpy arrays. Output is related with input from socket A and socket B. 
Output will be numpy array if at least one input sockets (A or B) has numpy array and another socket does not have 
list with two or more values.

.. image:: https://user-images.githubusercontent.com/14288520/189739875-0cd27fc9-3e36-48fd-9b5a-e29de6cd2ff9.png
  :target: https://user-images.githubusercontent.com/14288520/189739875-0cd27fc9-3e36-48fd-9b5a-e29de6cd2ff9.png

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

**Alternative of list mask out node:**

.. image:: https://user-images.githubusercontent.com/14288520/189739962-68fc989e-38e6-4845-bc7f-dd473708308e.png
  :target: https://user-images.githubusercontent.com/14288520/189739962-68fc989e-38e6-4845-bc7f-dd473708308e.png

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Working inside and outside of object level
------------------------------------------

Something unexpected can be with none iterable objects like matrix or Blender objects. 
On the picture below it can be expected that switch should add first matrix and second quaternion:

.. image:: https://user-images.githubusercontent.com/14288520/189740102-41008bb1-8b2e-4abf-bc82-2d5bdef8de97.png
  :target: https://user-images.githubusercontent.com/14288520/189740102-41008bb1-8b2e-4abf-bc82-2d5bdef8de97.png

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

but for this states input should have values on first object level not on second data level:

.. image:: https://user-images.githubusercontent.com/14288520/189740124-1ab19668-bf50-4f62-926a-7900cb8dbea1.png
  :target: https://user-images.githubusercontent.com/14288520/189740124-1ab19668-bf50-4f62-926a-7900cb8dbea1.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* List->List Struct-> :doc:`List Sort </nodes/list_struct/sort>`