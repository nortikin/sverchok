DXF Import
==========

Functionality
-------------

This node imports geometry from DXF files into Sverchok. It supports layer filtering and outputs various types of geometry including lines, polygons, annotations, text, and curves.

**Features:**

- Layer-based filtering for selective import
- Multiple curve implementation options (Geomdl, Sverchok, FreeCAD)
- Automatic viewer node creation for quick visualization
- Support for text annotations and dimensions

Inputs
------

- File Path: Path to the DXF file to import

Options
-------

- Implementation: Curve implementation type (Geomdl, Sverchok, or FreeCAD)
- Scale: Overall scale factor for imported geometry
- Resolution: Resolution for arc and circle discretization
- Text Scale: Scale factor for text elements

Operators
---------

- Import DXF: Main import button - loads and processes the DXF file
- Load Layers: Loads all available layers from the DXF file
- Update Filter: Applies current layer selection and re-imports
- Clear Layers: Clears the layer list
- Add Viewers: Automatically creates 5 viewer nodes for different geometry types

Outputs
-------

- Vertices (Lines): Vertices for line geometry
- Edges (Lines): Edge indices for line geometry
- Vertices (Polygons): Vertices for polygon geometry
- Polygons: Polygon face indices
- Vertices (Annotations): Vertices for annotation geometry
- Edges (Annotations): Edge indices for annotation geometry
- Vertices (Text): Vertex positions for text elements
- Text: Text content strings
- Curves: NURBS curves from the DXF file
- Knots: Knot vectors for the curves

Layer Management
----------------

The node provides layer filtering capabilities:

0. Forst of all press import DXF
1. Click "Load Layers" to load all layers from the DXF file
2. Use checkboxes to enable/disable specific layers
3. Click "Update Filter" to apply the selection
4. Layers are automatically enabled when loaded

Viewer Nodes
------------

The "Add Viewers" button creates 5 specialized viewer nodes:

- DXF Lines: Displays line geometry
- DXF Polygons: Displays polygon geometry  
- DXF Annotations: Displays annotation geometry
- DXF Text: Displays text elements with index viewer
- DXF Curves: Displays NURBS curves

Examples
--------

*LibreCAD initial DXF*

.. image:: https://github.com/user-attachments/assets/01b5ddd1-18a6-4c7f-b908-5553ed6632c8

*Example of DXF import with all layers*

.. image:: https://github.com/user-attachments/assets/97c06b7b-7ee3-4233-baba-642b431106e1

*Example of DXF import with some layers switched off*

.. image:: https://github.com/user-attachments/assets/5b851361-6bfa-46c2-8ffb-01d53696cc08

*Example of DXF import before layers searched from dxf. First import DXF, than lookup for layers*

.. image:: https://github.com/user-attachments/assets/ca09f8ed-8d82-4c2d-8dd3-adba5bacc6ef
