from .sv_itertools import sv_zip_longest

# base method for all scripts
class SvScript:
    def get_data(self):
        '''Support function to get raw data from node'''
        node = self.node
        if node:
            return [(s.name, s.sv_get()) for s in node.inputs]
        else:
            raise Error
    
    def set_data(self, data):
        '''
        Support function to set data
        '''
        node = self.node
        for name, d in data.items():
            node.outputs[name].sv_set(d)

def recursive_depth(l):
    if isinstance(l, (list, tuple)) and l:
        return 1 + recursive_depth(l[0])
    elif isinstance(l, (int, float, str)):
        return 0
    else:
        return None

        
# this method will be renamed and moved
        
def atomic_map(f, *args):
    # this should support different methods for finding depth
    types = [isinstance(a, (int, float)) for a in args]
    if all(types):
        return f(*args)
    elif any(types):
        tmp = [] 
        for t,a in zip(types, args):
            if t:
                tmp.append([a])
            else:
                tmp.append(a)
        return atomic_map(f, *tmp)
    else:
        res = []
        for z_arg in sv_zip_longest(*args):
            res.append(atomic_map(f,*z_arg))
        return res

class SvScriptAuto(SvScript):
    """ f(x,y,z,...n) -> t"""
    def process(self):
        data = self.get_data()
        tmp = [d for name, d in data]
        res = atomic_map(self.function, *tmp)
        name = self.node.outputs[0].name
        self.set_data({name:res})
    
