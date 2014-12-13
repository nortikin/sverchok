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

To begin we want to create a series of numbers, to get the range ``[0.25 pi, 0.75 pi, 1.25 pi, 1.75 pi]``. Because these aren't whole numbers, but so called ``Floats``, we want a Node that generates a range of them: Range Float. (or 'Float series' as it's called when added to the node view). We will tell the Float series Node to make ``[0.25, 0.75, 1.25, 1.75]`` and multiply them with the constant PI.  

**Making a series of numbers**

``new -> numbers -> Range Float``

[ image ]

**Seeing the output of the Range Float node**

``new -> Text -> Stethoscope``  
Hook up the `Stethoscope` input into the `Float range` output, you'll see text printed onto the node view. You can change the color of the Stethoscope text using the color property if the background color is too similar to the text color.



**Multiplying the series by PI**

``new -> numbers -> Math``

[ image ]