KDT Closest Verts
=================

Functionality
-------------

For every vertex in Verts, it checks the list of Vertices in Check Verts. 
What it does exactly depends on the *Search Mode*.

Search modes are mere examples of what is possible with Blender's KDTree module. The documentation for kdtree
is found at the latest version of ``mathutils.kdtree.html``. 


Inputs
------

- Verts
- Check Verts

Parameters
----------

| Search Mode | Description |
| 1           |
| N           |
| Radius      | 


Outputs
-------

Examples
--------

Notes
-------

If you need large kdtree searches and memoization or specific functionality you shall want to write your own Node to utilize the kdtree module. Part of the problem of making a *general use* node is that it becomes sub-optimal for certain tasks. On the up-side, having this node allows you to rip out the specifics and implement your own more specialized kdtree node. Recommend using a different Node name and sharing it with team Sverchok :)

.. image:: 
    :alt: some stuff


