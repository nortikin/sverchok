************************************************
Introduction to Visual programming with Sverchok
************************************************

You have installed the addon, if not then read **this**. The following Units will introduce no more than 10 node types per lesson. 


Unit 01 - 4 vectors
===================

**prerequisites**

You should have a general understanding of Vectors and Trigonometry, if not then soon enough parts of these lessons might be confusing. If you want to get the most of out Sverchok but don't have a strong Math background then work your way through related KhanAcademy content, it's a great resource and mind bogglingly comprehensive.

Lesson 01
---------

Nodes covered in this lesson: ``Math, Vector In, Float, Range Float, Viewer Draw, Stethoschope``. 

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

**Getting the Cos and Sin of this series**

-  ``new -> numbers -> Math``  ( add two math nodes)

These new ``Math`` nodes will do the Trigonometry for us. Set one of them to a `Cos` and the other to a `Sin`. These two nodes will now output the result of taking the *cosine* or *sine* of whatever is routed into them.

