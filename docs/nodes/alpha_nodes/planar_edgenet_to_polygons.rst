Planar edgenet to polygons
==========

Functionality
-------------

It fills all closed countors of edge net. Be careful edge net have to be planar otherwise work of node will be broken or even you can receive memory error caused of everlasting cycle.

See here, what planar edge net is - https://en.wikipedia.org/wiki/Planar_graph

Some details is here - https://github.com/nortikin/sverchok/issues/86

Inputs
------

- **Vertices** Only X and Y coords used
- **Edges**

Outputs
-------

- **Vertices**
- **Polygons**. All faces of resulting mesh.

Examples of usage
-----------------

.. image:: https://user-images.githubusercontent.com/28003269/37073575-31ba7430-21e1-11e8-8642-928dda1688a6.png

https://gist.github.com/6252a8e55ddfacca2c023a2eef8b1fd0

Unlike fill node

.. image:: https://user-images.githubusercontent.com/28003269/37105808-8e29b4f2-2249-11e8-9f36-e1da399153fc.png

https://gist.github.com/b0eb16271d33924457e443d74ac3c8d1
