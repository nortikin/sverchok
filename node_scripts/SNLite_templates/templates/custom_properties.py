"""
out float_out s
out int_out s
out bool_out s
out vec_out v
out color_out c
out str_out T
out obj_out o
out coll_out o
"""

# Initialization
if 'my_float' not in self.keys():
    self['my_float'] = 0.5
if 'my_integer' not in self.keys():
    self['my_integer'] = 5
if 'my_boolean' not in self.keys():
    self['my_boolean'] = 0
    bool_prop = self.id_properties_ui("my_boolean")
    bool_prop.update(min=0, max=1)
if 'my_vector' not in self.keys():
    self['my_vector'] = (0.0, 0.0, 1.0)
if 'my_color' not in self.keys():
    self['my_color'] = (1.0, 0.0, 0.0, 1.0)
    col_prop = self.id_properties_ui("my_color")
    #  Also it could be subtype="COLOR"
    col_prop.update(soft_min=0.0, soft_max=1.0, default=(0, 0, 0, 1.0), subtype="COLOR_GAMMA")
if 'my_string' not in self.keys():
    self['my_string'] = 'Hello World!'
if 'my_object' not in self.keys():
    self['my_object'] = ''
if 'my_collection' not in self.keys():
    self['my_collection'] = ''

# Outputs
float_out = [[self['my_float']]]
int_out = [[self['my_integer']]]
bool_out = [[self['my_boolean']]]
vec_out = [[tuple(self['my_vector'])]]
color_out = [[tuple(self['my_color'])]]
str_out = [[self['my_string']]]

if self['my_object'] in bpy.data.objects.keys():
    obj_out = [bpy.data.objects[self['my_object']]]

if self['my_collection'] in bpy.data.collections.keys():
    coll_objs = [obj for obj in bpy.data.collections[self['my_collection']].objects.values()]
    coll_out = coll_objs

# UI
def ui(self, context, layout):
    layout.prop(self, '["my_float"]', text="MyFloat")
    layout.prop(self, '["my_integer"]', text="MyInteger")
    layout.prop(self, '["my_boolean"]', text="MyBoolean")
    layout.prop(self, '["my_vector"]', text="MyVector")
    layout.prop(self, '["my_color"]', text="MyColor")
    layout.prop(self, '["my_string"]', text="MyString")
    layout.prop_search(self, '["my_object"]', bpy.data, "objects", text="MyObject")
    layout.prop_search(self, '["my_collection"]', bpy.data, "collections", text="MyCollection")
