lamp out
========


This node offers a nodification of the currently implemented lamps in Blender. It should be self explanatory.
- you can pass it multiple vectors and it will generate an individual lamp for each
- if you want unique colors per lamp, then feed it the output of a Colour Out node (with a list-split before hand)

Issues
------
There are internal inconsistent naming conventions in Blender's "light/laap" arsenal, some features may be broken before we realize.


Peculiarities
-------------

This node outputs objects of type "Object" not **bpy.data.light** ( use the `.data` accessor from an *Obj ID set* node if you need to dig deeper into the object (for something like luxcore, something `data.luxcore.rgb_gain`)