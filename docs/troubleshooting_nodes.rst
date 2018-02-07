Troubleshooting Nodes
=====================

 Because Sverchok is *visual programming* we'll use the same terminology as regular programming to talk about errors/bugs, Sverchok is really a Python library with a node interface.
 
For users
---------

**Errors / Error state**

Sometimes a node enters a state where it fails to produce useful output (error state). Sverchok will change the color of that node to red, as an indication to you of the approximate location of a problem. I say "approximate" because the node that exhibits the error might not be the node causing the error, in that case it's one of the nodes upstream from the node.

Nodes that enter the error state do so because the internal algorithms of the node tried to process information and couldn't, the node then throws what in programming is called "An Exception" (something didn't compute). 

**Exceptions**

A variety of reasons can cause exceptions, sometimes you have to solve a sequence of errors. Usually it leads you to understanding the data being sent through the node tree better. This is seriously as good thing, mostly for your productivity.

**Causes**

- A node can receives input that it doesn't expect, before starting to process the data. Some nodes will throw an exception as early as possible.

- A node's internal algorithm arrives at a point in processing the incoming data where the data being used to perform a calculation doesn't make sense.

     in the realm of math. errors like:
        - div x by zero
        - log of 0 or negative
     in the realm of programming data structures:
        - trying to divide a list/iterable by a number
        - trying to add a list/iterable to a numer
        - many many more. If you're a programmer you can imagine this list is long and not worth being exhausted.
 
- Nodes that interact directly with Blender objects can be doing so incorrectly.
 
**Ways to solve these issues, or at least understand them**
 
We have quite a few ways to see the state of the output of a node
