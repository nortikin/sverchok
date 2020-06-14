lib = None
mdl = None
func = None
param = {}
result = [0.0]
#in_socks_c = []
cdef = ""
code = ""
#parameters = [1, 2]

 
def load(name):
    import bpy, imp
    code = bpy.data.texts[name].as_string()
    mdl = imp.new_module(name)
    # warning, dangerous !
    exec(code, mdl.__dict__)
    return str(getattr(mdl, "cdef")) , str(getattr(mdl, "code"))

def execute(lib, mdl, function, params):
    import timeit
    
    def wrapper(func, *args, **kwargs):
        def wrapped():
            return func(*args, **kwargs)
        return wrapped
    
    args = [lib]
    print("EXEC", params)
    for p in params:
        args.append(p) 
    # take from sockets later....
    f = getattr(mdl, function)
    print(f)
    w = wrapper(f, *args)
    # print("Function execution", function,  timeit.timeit(w, number=1))
    return [w()]

def wrap(func, param):
    import imp
    params = ""
    le = len(param.items()) - 1
    #print(le)
    for index, i in enumerate(param.items()):
        #print(index, i)
        if index < le:
            params += (i[0] + ",")
        else:
            params += i[0]
            
    function = func[1]    
    print(function, params)
    
    code = "def "+function+"(lib, " + params +"):\n return lib."+function+"("+params+")"
    mdl = imp.new_module(function)
    #warning, dangerous !
    exec(code, mdl.__dict__)
    return mdl

def map_sockets(func, params, socks_v):
    mdl = None
    for i, p in enumerate(params):
        param[p[1]] = socks_v[i][0]
    
    print("PARAM", param)       
    mdl = wrap(func, param)
    
    return mdl
    
    
def testfn(i):
    return i % 2 == 1

def parse(item):
    item = item.strip()
    print("ITEM1", item)
    x = item.split("(")
    print("X", x)
    n = x[0].split(" ")
    o = x[1].split(")")[0].split(",")
    print("PARSE", o)
    t = []
    for i in range(0, len(o)):
        o[i] = o[i].strip()
        tk = o[i].split(" ")
        t.append((tk[0], tk[1]))
    return n, t

def test(item):
    it = item.strip()
    return it != ""

def parse_functions(cdef):
    #expect only one function prototype, for now
    itemz = cdef.split("\n")
    print(itemz)
    ite = [parse(it) for it in itemz if test(it)]
    print(ite)
    return ite[0]
    
def compile(cdef, code):
    
    import bpy, os, cffi
    #todo, make configurable
    path = os.path.dirname(bpy.data.filepath)
    pypath = bpy.app.binary_path + "../2.83/python/include"
    bpath = path + "/build"
    src = "/home/martin/BlenderSVN/blender_git/source/blender/"  # not so relevant yet.
    inc = ["blenkernel", "makesrna", "makesdna", "blenlib", "makesrna/intern"]
    incdirs = [src + i for i in inc]
    incdirs.append(pypath)
    
    ffi = cffi.FFI()        
    ffi.cdef(cdef)
    lib = ffi.verify(code, tmpdir=bpath, include_dirs=incdirs)
    
    return lib

