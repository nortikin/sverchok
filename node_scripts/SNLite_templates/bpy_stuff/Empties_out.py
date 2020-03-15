"""
in  bounds  v   .=[]    n=0
out text    s
"""

from mathutils import Matrix, Vector

text = []
for i, obj in enumerate(bounds):
    a,b = obj[0],obj[-1]
    text_ = str(i)+':'+str(round((abs(a[0])-abs(b[0]))*1000))+'x'+str(round((abs(a[1])-abs(b[1]))*1000))
    text_ += ' '
    text.append(text_)
text = [text]