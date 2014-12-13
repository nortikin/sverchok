************************************************
Introduction to Visual programming with Sverchok
************************************************

You have installed the addon, if not then read **this**. The following Units will introduce no more than 10 node types per lesson. 


Unit 01 - 4 vectors
===================

**prerequisites**

You should have a general understanding of Vectors and Trigonometry, if not then work your way through related KhanAcademy content, they are fantastic and comprehensive. It is essential for meaningful use of Sverchok to have a grasp on these concepts, maybe not initially, but later you'll want to do cooler and complex stuff.

Lesson 01
---------

Nodes covered in this lesson: ``Math, Vector In, Float, Range Float, Viewer Draw, Stethoschope``. 

Let's make a set of 4 vectors and combine them to represent a plane. I'll use the Trigonometric concept of the `unit-circle` to get coordinates which are `0.5 PI appart`. 

[image of said unit circle and four points]

To begin we want to create a series of numbers, to represent the points on the unit circle above that form the square. Essentially this sequence ``[0.25 pi, 0.75 pi, 1.25 pi, 1.75 pi]``. Because these aren't whole numbers, but so called ``Floats``, we want a Node that generates a range of Floats: Range Float. (or 'Float series' as it's called when added to the node view). We will tell the Float series Node to make ``[0.25, 0.75, 1.25, 1.75]`` and multiply them later with the constant PI.  

**Making a series of numbers**

-  ``new -> numbers -> Range Float``  

The `Range Float` node has a set of defaults which output

[ image ]

**Seeing the output of the Range Float node**

-  ``new -> Text -> Stethoscope``  

Hook up the `Stethoscope` input into the `Float range` output, you'll see text printed onto the node view. You can change the color of the Stethoscope text using the color property if the background color is too similar to the text color.

.. image:: https://cloud.githubusercontent.com/assets/619340/5424823/fa98153e-8300-11e4-878f-c496afbbbe2f.png

**Setting up the input values of Range Float to generate the right output**


**Multiplying the series by PI**

-  ``new -> numbers -> Math``  

We know the output of the Float series now, what we will do now is multiply the series by a constant PI. This is like doing ``[0.25, 0.75, 1.25, 1.75] * pi``. 

[ image ]