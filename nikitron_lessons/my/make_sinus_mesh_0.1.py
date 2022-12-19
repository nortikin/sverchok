import bpy
import mathutils
import math

# сам себе выдал задание:
# генератор поверхности от формулы



# задаваемые параметры:

size_x = 20 # количество точек Х

size_y = 20 # количество точек У

step_x = 0.3 # шаг Х

step_y = 0.3 # шаг У

step_z = 0.3 # шаг Z

name = 'formula' # имя объекта

def form(x, y, z): # задаём формулу
    return  math.exp(math.sin(x*y/5))
# разбиваем сетку шаги x и y
def x_list(size_x):
    x = []
    for i in range(0, size_x):
        x.append(i)
    return x
def y_list(size_y):
    y = []
    for i in range(0, size_y):
        y.append(i)
    return y
# заполняем векторы точек
def locations(x,y,stx,sty,stz):
    loc = []
    for xi in x:
        for yi in y:
            loc.append(mathutils.Vector((step_x*xi, step_y*yi, form(xi/2,yi/2,step_z/100))))
    return loc
# заполняем полигоны
def faces(x,y):
    fac = []
    for xi in x[1:]:
        for yi in y[1:]:
            one = yi-1+(xi-1)*len(y)
            two = yi+(xi-1)*len(y)
            thr = yi+xi*len(y)
            fou = yi-1+xi*len(y)
            fac.append((one, two, thr, fou))
            #fac.append((yi-1,yi,thr,fou)) - веер :-)
    return fac
# Производим объект и мэш
def makeMesh(name):
    return bpy.data.meshes.new(name+'Mesh')
def makeOb(name,me):
    ob = bpy.data.objects.new(name, me)
    ob.location = (0,0,0)
    ob.show_name = True
    bpy.context.scene.objects.link(ob)
    return
# присваиваем значения
def regit(me,loc,fac):
    me.from_pydata((loc), [], fac)
    me.update(calc_edges=True)
    return

def main():
    x = x_list(size_x)
    y = y_list(size_y)
    loc = locations(x,y,step_x,step_y,step_z)
    fac = faces(x,y)
    me = makeMesh(name)
    makeOb(name,me)
    regit(me,loc,fac)
    return

if __name__ == '__main__':
    main()



