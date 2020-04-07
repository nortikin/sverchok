filter empty lists
==================

start out due to this issue: https://github.com/nortikin/sverchok/pull/2089


  While this may seem like a bug in the mentioned nodes, it is in-fact a useful feature for parametric trees. Sometimes it's important to know when a set of parameters-mesh does not result in an output. The node proposed by kosvor will handle the output of such nodes in a way that will allow users to react to empty 'products' of the operation.

the `tldr`, it drops all empty lists from the socket data