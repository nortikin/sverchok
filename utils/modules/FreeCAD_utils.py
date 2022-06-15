"""
find the add-on version of this module at:
https://gist.github.com/yorikvanhavre/680156f59e2b42df8f5f5391cae2660b

reproduced large parts with generous permission, includes modifications for convenience
"""
from types import SimpleNamespace
import sys, bpy, xml.sax, zipfile, os
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
from mathutils import Quaternion, Matrix 

from sverchok.dependencies import FreeCAD
if FreeCAD:
    from sverchok.utils.decorators import duration
    import Part

    class FreeCAD_xml_handler(xml.sax.ContentHandler):

        """A XML handler to process the FreeCAD GUI xml data"""

        # this creates a dictionary where each key is a FC object name,
        # and each value is a dictionary of property:value pairs

        def __init__(self):

            self.guidata = {}
            self.current = None
            self.properties = {}
            self.currentprop = None
            self.currentval = None

        # Call when an element starts

        def startElement(self, tag, attributes):

            if tag == "ViewProvider":
                self.current = attributes["name"]
            elif tag == "Property":
                name = attributes["name"]
                if name in ["Visibility", "ShapeColor", "Transparency", "DiffuseColor"]:
                    self.currentprop = name
            elif tag == "Bool":
                if attributes["value"] == "true":
                    self.currentval = True
                else:
                    self.currentval = False
            elif tag == "PropertyColor":
                c = int(attributes["value"])
                r = float((c>>24)&0xFF)/255.0
                g = float((c>>16)&0xFF)/255.0
                b = float((c>>8)&0xFF)/255.0
                self.currentval = (r,g,b)
            elif tag == "Integer":
                self.currentval = int(attributes["value"])
            elif tag == "Float":
                self.currentval = float(attributes["value"])
            elif tag == "ColorList":
                self.currentval = attributes["file"]

        # Call when an elements ends

        def endElement(self, tag):

            if tag == "ViewProvider":
                if self.current and self.properties:
                    self.guidata[self.current] = self.properties
                    self.current = None
                    self.properties = {}
            elif tag == "Property":
                if self.currentprop and (self.currentval != None):
                    self.properties[self.currentprop] = self.currentval
                    self.currentprop = None
                    self.currentval = None

    def get_guidata(filename):

        # check if we have a GUI document
        guidata = {}
        with zipfile.ZipFile(filename) as zdoc:

            if "GuiDocument.xml" in zdoc.namelist():

                with zdoc.open("GuiDocument.xml") as gf:
 
                    guidata = gf.read()
                    Handler = FreeCAD_xml_handler()
                    xml.sax.parseString(guidata, Handler)
                    guidata = Handler.guidata
                    for key, properties in guidata.items():

                        if (diffuse_file := properties.get("DiffuseColor")):
                        
                            with zdoc.open(diffuse_file) as df:
                                buf = df.read()
                                # first 4 bytes are the array length, then each group of 4 bytes is abgr
                                # overwrite file reference with color data.
                                cols = [(buf[i*4+3], buf[i*4+2], buf[i*4+1], buf[i*4]) for i in range(1,int(len(buf)/4))]
                                guidata[key]["DiffuseColor"] = cols

        return guidata


    def hascurves(shape):
        for e in shape.Edges:
            if not isinstance(e.Curve, (Part.Line, Part.LineSegment)): return True
        return False

    @duration
    def import_fcstd(
        filename,
        update=False,
        placement=True,
        tessellation=1.0,
        skiphidden=True,
        scale=1.0,
        sharemats=True,
        report=None):

        guidata = get_guidata(filename)

        doc = FreeCAD.open(filename)
        docname = doc.Name
        if not doc:
            print("Unable to open the given FreeCAD file")
            return

        matdatabase = {} # to store reusable materials
        obj_data = []

        for obj in doc.Objects:

            if skiphidden:
                if obj.Name in guidata:
                    if "Visibility" in guidata[obj.Name]:
                        if guidata[obj.Name]["Visibility"] == False:
                            continue

            verts = []
            vdict = dict() # maybe we gain some speed in lookups.
            edges = []
            faces = []
            add_face = faces.append # alias increase speed
            matindex = [] # face to material relationship
            faceedges = [] # a placeholder to store edges that belong to a face
            name = "Unnamed"

            if obj.isDerivedFrom("Part::Feature"):

                # create mesh from shape
                shape = obj.Shape
                if placement:
                    placement = obj.Placement
                    shape = obj.Shape.copy()
                    shape.Placement = placement.inverse().multiply(shape.Placement)

                if shape.Faces:

                    # write FreeCAD faces as polygons when possible
                    for face in shape.Faces:
                        
                        if (len(face.Wires) > 1) or (not isinstance(face.Surface, Part.Plane)) or hascurves(face):
                            # face has holes or is curved, so we need to triangulate it
                            rawdata = face.tessellate(tessellation)
                            
                            for v in rawdata[0]:
                                if not (v1 := (v.x, v.y, v.z)) in vdict:
                                    vdict[v1] = len(vdict)
                            
                            for f in rawdata[1]:
                                raw = rawdata[0]
                                nf = [vdict[(nv.x, nv.y, nv.z)] for nv in [raw[vi] for vi in f]]
                                add_face(nf)

                            matindex.append(len(rawdata[1]))
                        
                        else:
                        
                            f = []
                            ov = face.OuterWire.OrderedVertexes
                        
                            for v in ov:
                                vec = (v.X, v.Y, v.Z)
                                if not vec in vdict:
                                    vdict[vec] = len(vdict)
                                    f.append(len(vdict) - 1)
                                else:
                                    f.append(vdict[(v.X, v.Y, v.Z)])
                        
                            # FreeCAD doesn't care about verts order. Make sure our loop goes clockwise
                            c = face.CenterOfMass
                            v1 = ov[0].Point.sub(c)
                            v2 = ov[1].Point.sub(c)
                            n = face.normalAt(0,0)
                            if (v1.cross(v2)).getAngle(n) > 1.57:
                                f.reverse() # inverting verts order if the direction is couterclockwise
                            
                            add_face(f)
                            matindex.append(1)
                        
                        for e in face.Edges:
                            faceedges.append(e.hashCode())

                for edge in shape.Edges:
                    # Treat remaining edges (that are not in faces)
                    if not (edge.hashCode() in faceedges):
                        
                        if hascurves(edge):
                            dv = edge.discretize(9) #TODO use tessellation value
                            for i in range(len(dv)-1):
                                dv1 = (dv[i].x,   dv[i].y,   dv[i].z)
                                dv2 = (dv[i+1].x, dv[i+1].y, dv[i+1].z)
                                if not dv1 in vdict:
                                    vdict[dv1] = len(vdict)
                                if not dv2 in vdict:
                                    vdict[dv2] = len(vdict)
                                edges.append([vdict[dv1], vdict[dv2]])
                        
                        else:
                        
                            e = []
                            for vert in edge.Vertexes:
                                # TODO discretize non-linear edges
                                v = (vert.X,vert.Y,vert.Z)
                                if not v in vdict: vdict[v] = len(vdict)
                                e.append(vdict[v])

                            edges.append(e)

                verts = list(vdict.keys())

            elif obj.isDerivedFrom("Mesh::Feature"):
                # convert freecad mesh to blender mesh
                mesh = obj.Mesh
                if placement:
                    placement = obj.Placement
                    mesh = obj.Mesh.copy() # in meshes, this zeroes the placement
                t = mesh.Topology
                verts = [(v.x, v.y, v.z) for v in t[0]]
                faces = t[1]

            current_obj = SimpleNamespace(verts=verts, edges=edges, faces=faces, matindex=matindex, plac=None, faceedges=faceedges, name=obj.Name)
            current_obj.matrix = Matrix()
            current_obj.loc = (0.0, 0.0, 0.0)

            if placement:            
                current_obj.loc = placement.Base.multiply(scale)[:]
                if placement.Rotation.Angle:
                    # FreeCAD Quaternion is XYZW while Blender is WXYZ
                    x, y, z, w = placement.Rotation.Q
                    new_quaternion = Quaternion((w, x, y, z))
                    current_obj.matrix = new_quaternion.to_matrix().to_4x4()
                    current_obj.loc = placement.Base.multiply(scale)[:]
    
            obj_data.append(current_obj)

            if verts and (faces or edges):

                continue # this is here so the code below can be syntax highlighted while not being run :)
                if not obj.Name in guidata: continue

                if matindex and ("DiffuseColor" in guidata[obj.Name]) and (len(matindex) == len(guidata[obj.Name]["DiffuseColor"])):

                    # we have per-face materials. Create new mats and attribute faces to them
                    fi = 0
                    objmats = []
                    for i in range(len(matindex)):
                        
                        # DiffuseColor stores int values, Blender use floats
                        rgba = tuple([float(x)/255.0 for x in guidata[obj.Name]["DiffuseColor"][i]])
                        # FreeCAD stores transparency, not alpha
                        alpha = 1.0
                        if rgba[3] > 0:
                            alpha = 1.0 - rgba[3]
                        rgba = rgba[:3]+(alpha,)
                        bmat = None

                        if sharemats:
                            if rgba in matdatabase:
                                bmat = matdatabase[rgba]
                                if not rgba in objmats:
                                    objmats.append(rgba)
                                    bobj.data.materials.append(bmat)
                        if not bmat:
                            if rgba in objmats:
                                bmat = bobj.data.materials[objmats.index(rgba)]
                        if not bmat:
                            bmat = bpy.data.materials.new(name=obj.Name+str(len(objmats)))
                            bmat.use_nodes = True
                            principled = PrincipledBSDFWrapper(bmat, is_readonly=False)
                            principled.base_color = rgba[:3]
                            if alpha < 1.0:
                                bmat.diffuse_color = rgba
                                principled.alpha = alpha
                                bmat.blend_method = "BLEND"
                            objmats.append(rgba)
                            bobj.data.materials.append(bmat)
                            if sharemats:
                                matdatabase[rgba] = bmat
                        for fj in range(matindex[i]):
                            bobj.data.polygons[fi+fj].material_index = objmats.index(rgba)
                        fi += matindex[i]

                else:

                    # one material for the whole object
                    # alpha = 1.0
                    # rgb = (0.5,0.5,0.5)

                    # if "Transparency" in guidata[obj.Name]:
                    #     if guidata[obj.Name]["Transparency"] > 0:
                    #         alpha = (100 - guidata[obj.Name]["Transparency"]) / 100.0
                    if (transparency := guidata[obj.Name].get("Transparency", 1.0)) > 0:
                        alpha = (100 - transparency) / 100.0
                    else:
                        alpha = 1.0

                    # if "ShapeColor" in guidata[obj.Name]:
                    #     rgb = guidata[obj.Name]["ShapeColor"]
                    rgb = guidata[obj.Name].get("ShapeColor", (0.5, 0.5, 0.5))

                    rgba = rgb + (alpha,)
                    bmat = None
                    if sharemats:
                        if rgba in matdatabase:
                            bmat = matdatabase[rgba]

                    if not bmat:

                        bmat = bpy.data.materials.new(name=obj.Name)
                        
                        bmat.use_nodes = True
                        principled = PrincipledBSDFWrapper(bmat, is_readonly=False)
                        principled.base_color = rgb
                        if alpha < 1.0:
                            bmat.diffuse_color = rgba
                        
                        if sharemats:
                            matdatabase[rgba] = bmat

                    bobj.data.materials.append(bmat)


        FreeCAD.closeDocument(docname)

        print("Import finished without errors")
        return obj_data


class SVFreeCADImporterProps(bpy.types.PropertyGroup):
    # usage : 
    #     props: bpy.props.CollectionProperty(type=SVFreeCADImporterProps)

    option_skiphidden : bpy.props.BoolProperty(name="Skip hidden objects", default=True,
        description="Only import objects that where visible in FreeCAD"
    )
    # option_update : bpy.props.BoolProperty(name="Update existing objects", default=True,
    #     description="Keep objects with same names in current scene and their materials, only replace the geometry"
    # )
    option_placement : bpy.props.BoolProperty(name="Use Placements", default=True,
        description="Set Blender pivot points to the FreeCAD placements"
    )
    option_tessellation : bpy.props.FloatProperty(name="Tessellation value", default=1.0,
        description="The tessellation value to apply when triangulating shapes"
    )
    option_scale : bpy.props.FloatProperty(name="Scaling value", default=0.001,
        description="A scaling value to apply to imported objects. Default value of 0.001 means one Blender unit = 1 meter"
    )
    option_sharemats : bpy.props.BoolProperty(name="Share similar materials", default=True,
        description="Objects with same color/transparency will use the same material"
    )


classes = [SVFreeCADImporterProps]
register, unregister = bpy.utils.register_classes_factory(classes)
