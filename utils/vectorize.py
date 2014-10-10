def is_atom(func):
    def level_check(x):
        return isinstance(x, (int, float))
    return level_check

def atom_level(func):
    return func(

def vectorize(func, level=is_atom):
    def inner(*args):
        # verify data types
        data_types = [level_check(arg) for arg in args]
        if all(data_types):
            return func(*args)
        # uneven levels, build up
        if any(data_types):
            new_args = []
            for i_s, arg in zip(data_types, args):  
                if i_s: #is_atom
                    new_args.append([arg])
                else:
                    new_args.append(arg)
            return inner(args)
        
        # 
        res = [] 
        for param in sv_zip_longest(*args):
            res.append(inner(param))
        return res
        
    return inner


