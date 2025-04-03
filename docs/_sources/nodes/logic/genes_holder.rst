Genes Holder
============

.. image:: https://user-images.githubusercontent.com/14288520/189763727-88587af2-16a5-4cc8-9368-be6a089d9b64.png
  :target: https://user-images.githubusercontent.com/14288520/189763727-88587af2-16a5-4cc8-9368-be6a089d9b64.png

This node stores a list of values (Integers, Floats or Vectors) that can be modified by the Evolver Node into the Genetics algorithm system.

The node will keep the data and wont be affected by the regular updates.

Parameters
----------

* **Data type**: Integers (Int), Floats or Vectors
* **Variation Mode**: Order and Range. In Order mode the variation will be made by changing the order of the elements. In Range Mode the variation will be made by variating each element among the defined range(s)
* **Min**: Minimum value a gene can have. Only in "Range" mode
* **Maximum**: Maximum value a gene can have. Note that with the Integers this number will never be reached so to get a "Boolean" genes the maximum should be 2 to get values from 0 to 1. Only in "Range" mode
* **Population amount**: Number of members of the population.
* **Iterations**: Iterations of the system
* **Random Seed**: Random Seed used in the system, this affects the initial population and the crossover and mutation process.

Operators
---------

* **Reset**: This will reset the memory of the node filling it with random values or values coming  from the input socket

Inputs
------

* **Numbers**: Input to fill the memory of the node with numbers.
* **Vectors**: Input to fill the memory of the node with vectors.
* **Bounding Box**: Input to stablish the boundaries of the vectors (when generating the Evolver population). Only in "Range" mode


Outputs
-------

* **Numbers / Vectors**: Outputs memory of the node

Examples
--------

Solved problem: Which is the shortest path that cycles through all the points?. Note that this problem with 20 points has over 2 trillions of solutions, the Genetics Algorithm offers the best solution in a defined time

.. image:: https://user-images.githubusercontent.com/10011941/84772313-113b0280-afdb-11ea-89ec-971d19aee2cc.png
    :target: https://user-images.githubusercontent.com/10011941/84772313-113b0280-afdb-11ea-89ec-971d19aee2cc.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Analyzers-> :doc:`Path Length </nodes/analyzer/path_length_2>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Logic-> :doc:`Evolver </nodes/logic/evolver>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
