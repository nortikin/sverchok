# support classes for SvScript node MK2
# some utility functions

import abc
# basic class for Script Node MK2   
from .sv_itertools import sv_zip_longest

import itertools

# base method for all scripts
class SvScript(metaclass=abc.ABCMeta):
    def get_data(self):
        '''Support function to get raw data from node'''
        node = self.node
        if node:
            return [(s.name, s.sv_get(deepcopy=False), s.bl_idname) for s in node.inputs]
        else:
            raise Error
    
    def set_data(self, data):
        '''
        Support function to set data
        '''
        node = self.node
        for name, d in data.items():
            node.outputs[name].sv_set(d)
    
    @abc.abstractmethod
    def process(self):
        return

def recursive_depth(l):
    if isinstance(l, (list, tuple)) and l:
        return 1 + recursive_depth(l[0])
    elif isinstance(l, (int, float, str)):
        return 0
    else:
        return None

        
# this method will be renamed and moved
        
def atomic_map(f, args):
    # this should support different methods for finding depth
    types = tuple(isinstance(a, (int, float)) for a in args)
    
    if all(types):
        return f(*args)
    elif any(types):
        tmp = [] 
        tmp_app = tmp.append
        for t,a in zip(types, args):
            if t:
                tmp_app((a,))
            else:
                tmp_app(a)
        return atomic_map(f, tmp)
    else:
        res = []
        res_app = res.append
        for z_arg in sv_zip_longest(*args):
            res_app(atomic_map(f, z_arg))
        return res


# not ready at all.
def v_map(f,*args, kwargs):
    def vector_map(f, *args):
        # this should support different methods for finding depth   
        types = tuple(isinstance(a, (int, float)) for a in args)
        if all(types):
            return f(*args)
        elif any(types):
            tmp = [] 
            tmp_app
            for t,a in zip(types, args):
                if t:
                    tmp_app([a])
                else:
                    tmp_app(a)
            return atomic_map(f, *tmp)
        else:
            res = []
            res_app = res.append
            for z_arg in sv_zip_longest(*args):
                res_app(atomic_map(f,*z_arg))
            return res
    

    
class SvScriptAuto(SvScript, metaclass=abc.ABCMeta):
    """ f(x,y,z,...n) -> t"""
    @staticmethod
    @abc.abstractmethod
    def function(*args):
        return
        
    def process(self):
        data = self.get_data()
        tmp = [d for name, d, stype in data]
        res = atomic_map(self.function, tmp)
        name = self.node.outputs[0].name
        self.set_data({name:res})

class SvScriptSimpleGenerator(SvScript, metaclass=abc.ABCMeta):
    """
    Simple generator script template
    outputs must be in the following format
    (socket_type, socket_name, socket_function)
    where socket_function will be called for linked socket production
    for each set of input parameters
    """
    def process(self):
        inputs = self.node.inputs
        outputs = self.node.outputs
        
        data = [s.sv_get()[0] for s in inputs]

        for socket, ref in zip(outputs, self.outputs):
            if socket.links:
                func = getattr(self, ref[2])
                out = tuple(itertools.starmap(func, sv_zip_longest(*data)))
                socket.sv_set(out)
