"""
in verts v
enum = A B
enum2 = A B
out overts v
"""

def ui(self, context, layout):
    layout.prop(self, 'custom_enum', expand=True)
    layout.prop(self, 'custom_enum_2', expand=True)

for vex in verts:
    offset = 0 if self.custom_enum == "A" else 1
    offset2 = 0 if self.custom_enum_2 == "A" else 1
    overts.append([[v[0], v[1]+offset2, v[2]+offset] for v in vex])
