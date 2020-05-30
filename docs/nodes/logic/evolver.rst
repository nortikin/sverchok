Evolver
=======

This node implements a Genetics Algorithm system inspired in Galapagos (the Grasshopper plugin) and the 9th chapter of "The Nature of Code" by Daniel Shiffman https://natureofcode.com/book/chapter-9-the-evolution-of-code/

The system creates a starting population, evaluates the fitness of each "agent" and creates a new population bases on the crossover of the fitter agents and a mutation chance. The new population is evaluated and mixed every iteration rising the global fitness of the population by generating fitter agents.

The starting value of the Genotype nodes will be the first agent of the population.

The fittest agent of each generation will survive cloning himself to the next iteration.

Every agent is composed by a set of genes that can oscillate among determined values, the fitter agents have more chances to spread their genetic information.

In Sverchok every gen is defined by a "A Number" node. This node type has a minimum and a maximum that will control the variation possibilities of this gen. The node can use all the "A number" nodes of the node-tree or only some of them if they are inside a "Frame Node" that can be selected from the "Genotype" dropdown menu.

The fitness of every member of the population will be evaluated by running the node-tree with the genes of that member and recording the value that is inputted in the "Fitness" socket.

Parameters
----------

**Genotype**: dropdown menu to chose to use as genes either all 'A Number' nodes or only the ones inside a 'Frame' Node

**Mode**:  "Maximum" and "Minimum" with the maximum selected a higher fitness value is considered better with the minimum a lower fitness will be considered as more fit.

**Population amount**: Number of members of the population.

**Iterations**: Iterations of the system

**Random Seed**: Random Seed used in the system, this affects the initial population and the crossover and mutation process.

**Fitness Boost**: This value affects how the ancestors are chosen. Taking two members, one with a fitness of 2 and another with a fitness of 1: With a value of 1 the first member will have the double chances to get selected than the second one. With a value of 2 the first one will have 4 times the chances of the second, with a boost value of 3 the first will have 8 times the chances of the second....

**Mutation**: 0 the gene will never mutate, 1 will always mutate. The mutation has a 50% of being totally new and other 50% of being inherited from its ancestors and changed by a random amount (small mutation)

**Max Seconds**: Maximum time to run the system, when achieved the system will stop providing the last valid generation of members

**Use Fitness Goal**: When active the process will stop if fitness goal is achieved or improved

**Fitness Goal**: Value that will stop the process if achieved or improved.

Operators
---------

**Run**: Triggers the system

**Set Fittest**: Will place the best evaluated values on the genes nodes

Options
-------

**Output all generations**: When enabled the node will output all the members of all the generations. When disabled it will only return the last generation of members

Inputs
------

**Fitness**: Input to get the fitness of each member (has to be a single number)


Outputs
-------

**Genes**: Outputs the genes of the system

**Population**: Outputs the population. It can be only the last generation or all generations.

**Fitness**: Outputs the fitness of the population. It can be only the last generation or all generations.

Examples
--------

Solved problem: Which is the smallest box (as the sum of faces area) in which I can fit Suzanne mesh?

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/logic/evolver/evolver_genetics_algorithm_sverchok_blender_example_01.png

Solved problem: Where is the point where the minimum distance to a set of points is closest to the maximum distance?

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/logic/evolver/evolver_genetics_algorithm_sverchok_blender_example_02.png
