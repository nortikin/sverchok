Path Group Length
=================

.. image:: https://github.com/user-attachments/assets/caae3331-5bf7-47d4-8363-8bdd4474fb2d
  :target: https://github.com/user-attachments/assets/caae3331-5bf7-47d4-8363-8bdd4474fb2d

Functionality
-------------

This node calculates length of a paths composed from edges. Edges can be grouped.

    .. image:: https://github.com/user-attachments/assets/9b344c48-ae42-45a3-a069-7652f902d03c
      :target: https://github.com/user-attachments/assets/9b344c48-ae42-45a3-a069-7652f902d03c

Inputs
------

* **Vertices**
* **Edges**
* **Groups** - grouped name of every edge (numbers int or float or strings). If len of group if less than length of edges then group will extend to the length of edges. ex.: group: [["K19"]], edges: [[ [0 1], [1,2], [2,3] ]] then group get: [["K19", "K19", "K19",]]

Outputs
-------

* **Segments** - length of every segment
* **Group of Segments** - rearrange groups per edges
* **Length** - summ of Length of group of Segments
* **Group of Length** - What group assingned to every Length
* **Merged Length** - Merged length in all objects with equals group number/name
* **Grouped of Merged Length** - What group associated with Merged Length

    .. image:: https://github.com/user-attachments/assets/bd49eef9-cc7d-4af5-b6e7-458e54bd9af3
      :target: https://github.com/user-attachments/assets/bd49eef9-cc7d-4af5-b6e7-458e54bd9af3

if Groups are not connected then default group is 0.

    .. image:: https://github.com/user-attachments/assets/84e692fd-2a19-4cca-8c79-57f31740df6d
      :target: https://github.com/user-attachments/assets/84e692fd-2a19-4cca-8c79-57f31740df6d


Examples
--------

Show length of edges with groups:

.. image:: https://github.com/user-attachments/assets/33372d19-cfb5-4566-a5ba-26aff5c72ad7
  :target: https://github.com/user-attachments/assets/33372d19-cfb5-4566-a5ba-26aff5c72ad7