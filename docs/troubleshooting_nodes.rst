Troubleshooting Nodes
=====================

 Because Sverchok is *visual programming* we'll use the same terminology as regular programming to talk about errors/bugs, Sverchok is really a Python library with a node interface.
 
For users
---------

**Errors / Error state**

Sometimes a node enters a state where it fails to produce useful output (error state). Sverchok will change the color of that node to red, as an indication to you of the approximate location of a problem. I say "approximate" because the node that exhibits the error might not be the node causing the error, in that case it's one of the nodes upstream from the node.

Nodes that enter the error state do so because the internal algorithms of the node tried to process information and couldn't, the node then throws what in programming is called "An Exception" (something didn't compute). 

**Exceptions**

Exceptions can occur for a variety of reasons, sometimes you have to solve a sequence of errors. Usually it leads you to understanding the data being sent through the node tree better. This is seriously a good thing, mostly for your productivity. We have tools to help you see the data coming out or going in to a node.

**Causes**

- A node can receive input that it doesn't expect, before starting to process the data. Some nodes will throw an exception as early as possible.

- A node's internal algorithm arrives at a point in processing the incoming data where the data being used to perform a calculation doesn't make sense.

     in the realm of math. errors like:
        - div x by zero
        - log of 0 or negative
     in the realm of programming data structures:
        - trying to divide a list/iterable by a number
        - trying to add a list/iterable to a numer
        - many many more. If you're a programmer you can imagine this list is long and not worth being exhausted.
 
- Nodes that interact directly with Blender objects can be doing so incorrectly. Usually this is forgiving, but sometimes you will cause Blender to close to the desktop.
 
**Ways to solve these issues, or at least understand them**
 
For most "unwanted" situations we can find what their cause is. We have quite a few ways to see the state of the output or input of a node.

- start blender from a console, and keep it visisble as you work. When a node turns red it will print data into the console/cmd view. Read the error. Contemplate what it means.

- Stethoscope node:  Hook up this node to a stream of data that you want to probe. The node will display the incoming data directly in the NodeView. You might see immediately that there's something up with the data. You might see a single set of brackets, or your data has many more brackets than you expect. You might see that the data is not in the form you expect (extra nesting perhaps). For better info about stethoscope, see the docs that accompany this node.

- Viewer Text node: When sthetoscope sees only the first lines of data, it's possible to see the raw data. To help you quickly see the level of nestedness of your data you can use the Viewer Text, push the view button and look at the `Frame` or in text file `Sverchok Viewer`. 

- Data shape: As Viewer Text it sees levels, but not in terms of user cases. When we utilize data we know that the first list is just a container, inside are the `objects` and then data in digits or lists. Here we have a plain explanation.

- Debug Print node:  This node is also one you hookup to the socket data you are interested in seeing. The node however will print the data into the console/cmd window. This node allows you to connect multiple sockets (it will auto generate new input sockets). This lets you see a few sockets' data at a glance. This node is definitely more raw and you are advised to be aware of the amount of data you are passing. Don't give it thousands of vertices.

 - some tips if you use either `Debug Print` and `Stethoscope nodes`:
    - if you can't understand a problem, you need to try to reproduce the problem with as little geometry as possible. Dial all the sliders down to minimal values while the problem is still evident, then start debugging.
    - (you might have to) disconnect the error node, and "listen" to the data that was going into that node
    - switch off the nodes when you don't need them. 

- Debug timings mode: 
    - heatmap: Sometimes you need to know which node is taking the longest to process it's dataload. We have a heatmap mode that gives us a quick way to pinpoint the nodes where sverchok spends more time calculating.
    - print timings: this gives an overview of how exactly how much time is spent in each node, you'll get a list of nodes and their time-duration.


