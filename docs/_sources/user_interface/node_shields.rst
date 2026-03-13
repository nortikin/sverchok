Node Shields
------------

.. image:: https://user-images.githubusercontent.com/28003269/194277098-66690aab-a6c6-4dfb-9469-65a4ad811587.png

When node is added to a tree or when some file with Sverchok trees is oppened
nodes can be marked by putting them into special frames. Such frames mark
nodes that they have a certain state. There are currently two states:

Deprecated Node
  It marks that current node is deprecated. Usually such state can get nodes
  when an old file was opened. You can still use such nodes, they keep the same
  functionality, but usually there is new version of old nodes which has
  improved functionality. To replace old node with new version (if it's
  available) use *Replace With New Version Name* operator. The operator can be
  found in context menu of a node (``RMB`` on a node).

Alpha/Beta Node
  It means that a node is in development state. Node in such state can change
  its sockets, properties, functionality and even can be removed. So it's
  recommended to use these nodes only for testing. Layouts with such nodes
  can be broken in process of Sverchok development. Usually all such nodes
  should loose the state after a next release.
