Unit 01 - Vectors
===================

**prerequisites**

Same as lesson 01.


Lesson 02 - A Circle
--------------------

This will continue from the previous lesson where we made a plane from 4 vectors. We can reuse some of these nodes in order to make a Circle. If you saved it as suggested load it up, or download from **here**. You can also create it from scratch by cross referencing this image.

.. image:: https://cloud.githubusercontent.com/assets/619340/5428874/fac67fd4-83d5-11e4-9601-1399248dddd6.png

**A Circle**

Just like Blender has a Circle primitive, Sverchok also has a built in Circle primitive called the `Circle Generator`. We will avoid using the primtives until we've covered more of the fundamental nodes and how they interact.

**Dynamic Polygons**

In the collection of nodes we have in the Node View at the moment, the sequence used for linking up vertices to form a `polygon` is inputted manually. As mentioned earlier, as soon as you need to link many vertices instead of the current 4, you will want to make this `list creation` automatic. You will probably also want to make it dynamic to add new segments automatically if the vertex count increases. 

Because this is a common task, there's a dedicated node for it called ``UV Connect`` (link) , but just like the `Circle` generator nodes we will avoid using that and for the same reason. Learning how to build these things yourself is the best way to learn Visual Programming with nodes.

**Generating an index list for the polygon**

In order to make the list automatically, we should know how many vertices there are at any given moment.

- ``new -> List Basic -> List Length``

The `List Length` node lets you output the length of incoming data, it also lets you pick what level of the data you want to know the length of. It's worth reading the **reference** of this node for a comprehensive tour of its capabilities.

** Getting the number of Vertices**

1) hook the Vector In output into the `Data` input of `List Length`
2) hook a new Stethoscope up to the output of the the `List Length` node.
3) adjust the `Level` slider to 0, you should see ``[[4]]``

Notice that, besides all the square brackets, you see the length of the incoming data is `4`, as expected.



