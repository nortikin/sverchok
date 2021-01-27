topology simple
===============

This node is useful for educational purposes. It allows you to declare the edges and face index lists of a basic geometry, but from directly inside the node. It allows you to use a simplified syntax to describe the indices (with less brackets..).

Please sees the development thread:
https://github.com/nortikin/sverchok/pull/2522


Notice that you can simply write all comma separated, and space separated::

    # edges
    0 1, 2 3, 4 5

    # faces (tris, ngons...) 
    0 1 2, 2 3 4, 3 4 5 6

looks like this on the node:

.. image:: https://user-images.githubusercontent.com/619340/64472483-7b2a9f80-d15f-11e9-8058-4ae75aa4e5dc.png
