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
- **Join**: If checked, generate one flat list of paths for all input meshes; otherwise, generate separate list of loose parts for each input mesh


Examples of usage
-----------------

Simple:

.. image:: https://user-images.githubusercontent.com/10011941/105373980-83299900-5c07-11eb-94ea-a90c621f4cb7.png


.. image:: https://user-images.githubusercontent.com/10011941/105376026-96d5ff00-5c09-11eb-9fb8-7430085004c5.png
