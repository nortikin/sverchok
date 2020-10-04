**********************************
Introduction to modular components
**********************************

**prerequisites**

You should have a general understanding of Vectors and Trigonometry, if not then soon enough parts of these lessons might be confusing. If you want to get the most of out Sverchok but don't have a strong Math background then work your way through related KhanAcademy content, it's a great resource and mind bogglingly comprehensive.

Lesson 01 - A Plane
-------------------

Nodes covered in this lesson: ``Scalar Math, Vector In, Number, Number Range, Viewer Draw, Stethoschope, Simple Topology, Vector Math``. 

Let's make a Plane, we will need 4 vectors and we'll define them using math. I'll use the Trigonometric concept of the ``unit-circle`` to get coordinates which are ``0.5 PI`` appart.

   *Note*: The perimeter of a circle is C=2*PI*r . In the unit-circle radius=1 so it's perimter is C=2*PI . For the square we need 4 vertexes with equal distance apart so 2*PI/4=0.5*PI. If you consider that a circle represents an angle of 360 degrees then 2πr=360º and this means that 0*π places represents a vertex at 0 degrees of the circle: 0PI=0º ; 0.5PI=90º ; 1PI=180º ; 1.5PI=270º

.. image:: https://cloud.githubusercontent.com/assets/619340/5426922/20290ef0-837b-11e4-9863-8a0a586aed7d.png

We will rotate the square 45º to match the Blender's Plane. So the starting vertex will not be at 0*PI=0º but at 0.25PI=45º

We carefully pick points on the unit-circle so that when we connect them via edges it results in a square. To begin we want to create a series of numbers, to represent those points on the unit-circle. Essentially this sequence is ``[0.25 pi, 0.75 pi, 1.25 pi, 1.75 pi]``. Because these aren't whole numbers (``Integers``), but so called ``Floats``, we use a ``Number Range`` Node configured to output ``Floats``.

**Making a series of numbers**

-  ``Add -> Number -> Number Range``

|number_range|

By default this node will generate a standard range: ``[0.0, 1.0, 2.0, 3.0.....9.0]``,

**Seeing the output of the Range Float node**

-  ``Add -> Text -> Stethoscope``  

Hook up the `Stethoscope` input into the `Number Range` output, you'll see numbers printed onto the NodeView. You can change the color of the Stethoscope output using the color property if the background color is too similar to the text color.

   *Note*: With any node selected there's a faster way to add a Stethoschope: `Ctrl+Right Click` , it even automatically connects the stethoscope.

|num_range_and_stethoscope_default|

   *Note*: The stethoscope will draw 1.00 as 1 when there is no significant information behind the decimal point.

   *Note*: When you move the Stethoscope around it is possible that the drawing of the text beside it does not move with the node, whenever you update a value in a node upstream from the Stethoscope the drawing *will* be updated.

**Setting up the input values of Number Range to generate the 4 multipliers**

Type these numbers into the number fields instead of adjusting the slider, it's fast and accurate. Especially useful for entering *Floats*.

- Set the Number Range mode to ``Step`` and 
- make sure the *Start* value is ``0.25`` and 
- *Step* value is ``0.50``
- Set the *Count* slider to ``4``

|num_range_and_stethoscope|

**Multiplying the Range by PI**

-  ``Add -> Number -> Scalar Math`` 

We know the output of the *Number Range* now, what we will do is multiply the range by a constant PI. This is like doing::

   [0.25, 0.75, 1.25, 1.75] * pi

which is what we wanted from the beginning, namely;::

   [0.25 * pi, 0.75 * pi, 1.25 * pi, 1.75 * pi]

- Set the *Scalar Math* node to the function ``PI * X`` 
- Connect the output of the *Number Range* into the input of the ``PI * X`` node.

The result should look something like this, hook up the Stethoscope to see the outputs.

|pi_times_xrange|

**Getting the Sine and Cosine of this range**

-  ``Add -> Number -> Scalar Math``

The ``Scalar Math`` node will do the Trigonometry for us. From the dropdown you can pick the ``Sin & Cos`` function. This node will now output the *cos* and *sin* of whatever is routed into it, in this case the range of Floats.

|sincos_img1|

See the outputs of the ``SINCOS X``, each element of these new ranges represent a component (x or y) of the set of Vectors we want. **Sine** will represent ``Y`` and **Cosine** will be ``X``. 

   *Note*: I minimized the stethoschope node for visual readability (click the little triangle), stethoschope has many features that are not not useful to us right now.

**Making Vectors from a range of numbers**

- ``Add -> Vector -> Vector In``

The `Vector In` node takes as input 1 or more numbers per component. Sockets which are not explicitely connected to will be represented by a zero. 

1) Connect the resulting ``Cos( x )`` to the first component in of *Vector in*: ``X``
2) Connect the resulting ``Sin( X )`` to the second component in of *Vector in*: ``Y``
3) Leaving Vector In's 3rd socket (``z``) empty puts a ``0.0`` as the ``z`` component for all vectors generated by that node.

  *Note*: Alert readers will have noticed that we connected a ``Vector socket`` (orange) to a ``"Numbers" socket`` (green). We allow any connection between socket types that can be made to work, Sverchok does various automatic conversions in the background. We call them implicit conversions.

|sincos_img2|

**Display Geometry**

- ``Add -> Viz -> Viewer Draw``

Sverchok draws geometry using the Viewer Nodes. You might have noticed that the list of ``Viz`` nodes is extensive, this is because there are a variety of different ways to represent geometry; either just drawing to the view using openGL or making Blender's ``Objects`` directly. For now we'll focus on ``Viewer Draw``. Stethoscope is useful for showing the values of any socket, but when we're dealing with final geometric constructs like Vectors often we want to see them in 3D to get a better understanding, ``Viewer Draw`` is our lightweight drawing function.

Connect the output of ``Vectors In`` into the ``Verts`` on the Viewer Draw node. You should see 4 vertices appear on your ``3d view`` (but don't worry if you don't immediately spot them, by default they will be drawn in white):

|first_vdmk3|

Notice the 3 color fields on the Viewer Draw node, they represent the color that this node gives to its Vertices, Edges, and Faces. If (after connecting Vector In to ViewerDraw) you don't see the Vertices in 3dview, it is probably because your background 3dview color is similar to the Vertex color. Adjust the color field to make them visible.

**Increasing the Size of the Vertex**

Sometimes, especially while introducing Sverchok, it's preferred to display Vertices a little bigger than the default values of ``4 pixels``. If you had difficulty spotting the vertices initially you will understand why. The N-panel (`side panel`, or `properties panel`) for the Node View will have extra panels when viewing a ``Sverchok NodeTree``. Some nodes have a dedicated properties area in this panel to hold features that might otherwise complicate the node's UI.

|vdmk3_npanel|

In the case of the `Viewer Draw`, there's quite a bit of extra functionality hidden away in the properties area. For now we are interested only in the ``Point Size`` property. This slider has a range between 1 and 15, set it to whatever is most comfortable to view. Here a close up:

|closeup|

I think you'll agree that the Vertices are much easier to see now:

|second_vdmk3|

**Make some edges**

We've created vertices, now we're going to generate edges. We have 4 vertices and thus 4 indices: ``[0,1,2,3]``, the edges will be connected as ``[[0,1],[1,2],[2,3],[3,0]]``.

Vertices Indexed: 

.. image:: https://cloud.githubusercontent.com/assets/619340/5428066/f9445494-83b5-11e4-9b3b-6294d732fa00.png

We're going to add a simple topology node. Instead of using the menu to add a node, this time we'll use ``alt+space`` search field.

- ``alt+space -> type in:  top``  ( you should see something like the following )

|alt_search|

navigate down to the node named "Simple Topology" and hit enter to add it to the nodeview.

There are numerous ways to generate the *index list* for ``edges``. For our basic example we'll input them manually. Eventually you will be making hundreds of Vertices and at that point it won't be viable to write them out manually. For this lesson we'll not touch that subject.

The *Simple Topology Node* evaluates what you write into the two topology fields, and then outputs the results. Type into the ``Edges`` field (top one) the following sequence ``0 1, 1 2, 2 3, 3 0``. Internally the Simple Topology node converts this shorthand to a python list of indices::

    #input
    0 1, 1 2, 2 3, 3 0          <--- easy to input as a human

    #produces
    [[0,1],[1,2],[2,3],[3,0]]   <--- let python worry about the list syntax


Now hook the ``Edges`` output socket of *Simple Topology* node into the ``Edges`` input of *Viewer Draw*. You should see the following:

|edges_first|

  *Note 1*: I adjusted the Edge Width, if you're on a Mac this may not work. sorry. 
  *Note 2*: The ``Wrap`` button on Simple Topology node will enclose the output in an extra set of square brackets. This is appropriate see the documentation on ``Geometry``. 

**Make a first Polygon**

Using the same Simple Topology Node we will instead pass a polygon to the Viewer Draw, the Viewer Draw is able to infer how to draw edges from the Polygon information. 

- Disconnect the ``Edges`` socket from the ``Viewer Draw`` (you don't have to clear the Edges field)
- In *Simple Topology* node fill the Faces field with the shorthand: ``0 1 2 3``.  This means "i want a face described by these vertex indices".
- Connect the output of the ``Faces`` socket to the ``Faces`` input on Viewer Draw. You should now see the following:

|first_face|

**Controlling the size of the Polygon**

There are many ways to scale up a set of vectors, we'll use the *Vector Math* node.

- ``rightclick nodeview -> Vector Math``

Change the `Vector Math` node's ``mode`` to `Multiply Scalar`. This will let you feed a number to the Vectors to act as a multiplier. We'll add a *Number* node to generate the multiplier. 

- ``rightclick nodeview -> A Number``

1) Hook up the *Number* node to the Scalar (green) input of the `Vector Math (Multiply Scalar)` node
2) Connect the output of the `Vector In` node into the top input of the Vector Math node. 
3) Now connect the output of the `Vector Math` node into the ``Verts`` socket of the Viewer Draw node.

You should have something like this. 

|final_image|

Now if you change the slider on the *Number* node, you'll notice that the Polygon will start to increase and decrease in size because you are multiplying the ``x, y, and z`` components of the Vectors by that amount.

**End of lesson 01**

Save this .blend you've been working in now, somewhere where you will find it easily, as `Sverchok_Unit_01_Lesson_01`. We will use it as a starting point for the next lesson.

We'll stop here for lesson 01, if you've followed most of this you'll be making crazy shapes in a matter of hours. Please continue on to `Lesson 02 - A Circle`, but take a break first. Look outside, stare at a tree -- do something else for 10 minutes.


.. |number_range| image:: https://user-images.githubusercontent.com/619340/81541992-40bf7500-9374-11ea-82ce-4e5b1bbffb7a.png
.. |num_range_and_stethoscope_default| image:: https://user-images.githubusercontent.com/619340/81544402-c5f85900-9377-11ea-8a88-d13b3a9d00ce.png
.. |num_range_and_stethoscope| image:: https://user-images.githubusercontent.com/619340/81544544-f93ae800-9377-11ea-8789-fda3e2fb2500.png
.. |final_image| image:: https://user-images.githubusercontent.com/619340/82145036-31df3380-9848-11ea-84a7-1ed761c00e84.png
.. |pi_times_xrange| image:: https://user-images.githubusercontent.com/619340/81560341-850d3e00-9391-11ea-87f9-6f3b551ebeb9.png
.. |sincos_img1| image:: https://user-images.githubusercontent.com/619340/81560667-2a281680-9392-11ea-8223-29b9e09d01f7.png
.. |sincos_img2| image:: https://user-images.githubusercontent.com/619340/81565850-4def5a80-939a-11ea-9bc9-62c59414027c.png
.. |first_vdmk3| image:: https://user-images.githubusercontent.com/619340/81577343-95c9ae00-93a9-11ea-98a4-565d18cddb73.png
.. |second_vdmk3| image:: https://user-images.githubusercontent.com/619340/81568926-c48e5700-939e-11ea-84c0-72a884369054.png
.. |vdmk3_npanel| image:: https://user-images.githubusercontent.com/619340/81578234-ccec8f00-93aa-11ea-986a-b42949019e79.png
.. |closeup| image:: https://user-images.githubusercontent.com/619340/81578680-6ddb4a00-93ab-11ea-99b4-2512585adb35.png
.. |alt_search| image:: https://user-images.githubusercontent.com/619340/81579054-f1953680-93ab-11ea-86b3-a1ca585d511d.png
.. |edges_first| image:: https://user-images.githubusercontent.com/619340/81580514-d5929480-93ad-11ea-9ecf-9a7d5abf4be3.png
.. |first_face| image:: https://user-images.githubusercontent.com/619340/81581935-b3017b00-93af-11ea-850e-55207de956f7.png
