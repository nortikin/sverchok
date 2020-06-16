Genes Holder
============

This node stores a list of values (Integers, Floats or Vectors) that can be modified by the Evolver Node into the Genetics algorithm system.

The node will keep the data and wont be affected by the regular updates.

Parameters
----------

**Data type**: Integers (Int), Floats or Vectors

**Variation Mode**: Order and Range. In Order mode the variation will be made by changing the order of the elements. In Range Mode the variation will be made by variating each element among the defined range(s)

**Min**: Minimum value a gene can have. Only in "Range" mode

**Maximum: Maximum value a gene can have. Note that with the Integers this number will never be reached so to get a "Boolean" genes the maximum should be 2 to get values from 0 to 1. Only in "Range" mode

**Population amount**: Number of members of the population.

**Iterations**: Iterations of the system

**Random Seed**: Random Seed used in the system, this affects the initial population and the crossover and mutation process.

Operators
---------

**Reset**: This will reset the memory of the node filling it with random values or values coming  from the input socket

Inputs
------

**Numbers**: Input to fill the memory of the node with numbers.

**Vectors**: Input to fill the memory of the node with vectors.

**Bounding Box**: Input to stablish the boundaries of the vectors (when generating the Evolver population). Only in "Range" mode


Outputs
-------

**Numbers / Vectors**: Outputs memory of the node

Examples
--------

Solved problem: Which is the shortest path that cycles through all the points?. Note that this problem with 20 points has over 2 trillions of solutions, the Genetics Algorithm offers the best solution in a defined time

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/logic/evolver/evolver_genetics_algorithm_sverchok_blender_example_03.png
