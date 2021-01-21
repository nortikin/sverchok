Edgenet to Paths
================

Functionality
-------------

Splits each edgenet (mesh composed by verts and edges) in paths (sequences of ordered vertices)

Inputs
------

- **Vertices**
- **Edges**

Outputs
-------

- **Vertices**
- **Edges**
- **Verts indexes**: the indexes of the original vertices in the created paths
- **Edges indexes**: the indexes of the original edges in the created paths
- **Cyclic**: outputs True if the path is a closed path and False if not (only if close loops is activated)

Options
-------

- **Close Loops**: When checked, if the first and last vertices are identical they will merge; otherwise, this wont be checked


Examples of usage
-----------------

Simple:

.. image:: https://cloud.githubusercontent.com/assets/5783432/18611195/3b47ce74-7d43-11e6-8d05-335919636b2b.png
