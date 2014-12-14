************************************************
Introduction to Visual programming with Sverchok
************************************************

> Dealga McArdle | December | 2014

You have installed the addon, if not then read **this**. The following Units will introduce no more than 10 node types per lesson. Take your time to get through the parts that are text heavy, some concepts take longer to explain not because they are difficult to understand, but because there is simply more to cover.


Unit 01 - 4 vectors
===================

**prerequisites**

You should have a general understanding of Vectors and Trigonometry, if not then soon enough parts of these lessons might be confusing. If you want to get the most of out Sverchok but don't have a strong Math background then work your way through related KhanAcademy content, it's a great resource and mind bogglingly comprehensive.

Lesson 01
---------

Nodes covered in this lesson: ``Math, Vector In, Float, Range Float, Viewer Draw, Stethoschope, Formula``. 

Let's make a set of 4 vectors and combine them to represent a plane. I'll use the Trigonometric concept of the `unit-circle` to get coordinates which are `0.5 PI appart`. 

.. image:: https://cloud.githubusercontent.com/assets/619340/5426922/20290ef0-837b-11e4-9863-8a0a586aed7d.png

We carefully pick points on the unit-circle so that when we connect them via edges it results in a square. To begin we want to create a series of numbers, to represent those points on the unit-circle. Essentially this sequence is ``[0.25 pi, 0.75 pi, 1.25 pi, 1.75 pi]``. Because these aren't whole numbers, but so called ``Floats``, we use a Node that generates a range of Floats: ``Range Float``. (or 'Float series' as it's called when added to the node view). 

**Making a series of numbers**

-  ``new -> numbers -> Range Float``  

.. image:: https://cloud.githubusercontent.com/assets/619340/5425016/91b2bd2a-8306-11e4-8c96-a2d2b4de6094.png

This node has a set of defaults which output ``[0.000, 1.000..... 9.000]``. We will tell the  node to make ``[0.25, 0.75, 1.25, 1.75]`` and multiply them later with the constant PI.  


**Seeing the output of the Range Float node**

-  ``new -> Text -> Stethoscope``  

Hook up the `Stethoscope` input into the `Float range` output, you'll see text printed onto the node view. You can change the color of the Stethoscope text using the color property if the background color is too similar to the text color.

.. image:: https://cloud.githubusercontent.com/assets/619340/5424823/fa98153e-8300-11e4-878f-c496afbbbe2f.png

**Setting up the input values of Range Float to generate the right output**

Set the Float Series mode to `Step` and make sure the `Start` value is 0.25 and `Step` value is 0.50. You should type these numbers in instead of adjusting the slider, it's fast and instantly accurate. Set the `Count` slider to 4, whichever way is fastest for you.

.. image:: https://cloud.githubusercontent.com/assets/619340/5425218/8dbcdc26-830d-11e4-8ef1-a38b8723a00f.png


**Multiplying the series by PI**

-  ``new -> numbers -> Math``  ( add two math nodes)

We know the output of the Float series now, what we will do is multiply the series by a constant PI. This is like doing ``[0.25, 0.75, 1.25, 1.75] * pi``, which is what we wanted from the beginning, namely; ``[0.25 * pi, 0.75 * pi, 1.25 * pi, 1.75 * pi]``. 

1) Set one of the Math nodes to the constant ``PI`` 

2) Switch the other Math node to a Multiplier node by selecting ``Multiplication (*)`` from its dropdowns.

3) Connect the output of PI to one of the input sockets of the Multiply Node

4) Connect the output of the Float Series into the other input of the Multiply Node. 


The result should look something like this, hook up the Stethoscope to see the outputs.

.. image:: https://cloud.githubusercontent.com/assets/619340/5425420/5ecb5ba0-8316-11e4-9edc-ec7e111d9cd4.png

**Getting the Sine and Cosine this series**

-  ``new -> numbers -> Math``  ( add two math nodes)

These new `Math` nodes will do the Trigonometry for us. Set one of them to a `Cosine` and the other to a `Sine`. These two nodes will now output the *cos* or *sin* of whatever is routed into them, in this case the series of Floats.

.. image:: https://cloud.githubusercontent.com/assets/619340/5425497/8868cf8a-8319-11e4-8369-dd36d250e91b.png

See the outputs of the Sine and Cosine node, each element represents a component of the set of Vectors we want to make. Sine might represent `X` and Cosine could be `Y`. 

**Making Vectors from a series of numbers**

- ``new -> Vector -> Vector In``  

The `Vector In` node takes as input 1 or more numbers per component. Sockets which are not explicitely connected to will be represented by a zero. 

1) Connect the resulting `Sine` series to the first component in of Vector in (x)
2) Connect the resulting `Cosine` series to the second component in of Vector in (y)
3) Leaving Vector In's 3rd socket (z) empty puts a zero as the z component for all vectors generated by that node.

.. image:: https://cloud.githubusercontent.com/assets/619340/5427307/8f754164-8396-11e4-84bb-b06690223738.png

**Display Geometry**

- ``new -> Viz -> Viewer Draw``

Sverchok draws geometry using the Viewer Nodes, there are two types of viewer nodes but we'll focus on Viewer Draw for the moment. Stethoscope is useful for showing the values of any socket, but when we're dealing with final geometric constructs like Vectors often we want to see them in 3D to get a better understanding.

Connect the output of `Vectors In` into the `Vertices` on the Viewer Draw node. You should see 4 vertices appear on your 3d view:

.. image:: https://cloud.githubusercontent.com/assets/619340/5427315/ac6e384c-8397-11e4-809e-4ffa14342408.png

Notice the 3 color fields on the Viewer Draw node, they represent the color that this node gives to its Vertices, Edges, and Faces. If (after connecting Vector In to ViewerDraw) you don't see the Vertices in 3dview, it is probably because your background 3dview color is similar to the Vertex color. Adjust the color field to make them visible.

**Increasing the Size of the Vertex**

Sometimes, especially while introducing Sverchok, it's preferred to display Vertices a little bigger than the default values of 3 pixels. If you had difficulty spotting the vertices initially you will understand why. The N-panel (`side panel`, or `properties panel`) for the Node View will have extra panels when viewing a [Sverchok Node Tree]. Some nodes have a dedicated properties area in this panel to hold features that might otherwise complicate the node's UI.

In the case of the `Viewer Draw`, there's quite a bit of extra functionality hidden away in the properties area. For now we are interested only in the Vertex Size property. In the image below it's marked with a (red) dot. This slider has a range between 0 and 10, set it to whatever is most comfortable to view.

.. image:: https://cloud.githubusercontent.com/assets/619340/5427372/02a617be-839a-11e4-9af5-2c435dd5178d.png

**Make some edges**

// -- todo

