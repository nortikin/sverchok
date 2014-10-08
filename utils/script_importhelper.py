import inspect
from utils.sv_script import SvScript

def load_script(source, name):
    try:
        from_file = '<{}>'.format(name)
        code = compile(source, from_file, 'exec', optimize=0)
        # insert classes that we can inherit from
        local_space = {cls.__name__:cls for cls in SvScript.__subclasses__()}
        local_space["SvScript"] = SvScript
        
        exec(code, globals(),local_space)
    except SyntaxError as err:
        print("Script Node, load error: {}".format(err))
        return
    except TypeError:
        print("No script found")
        return
    script = None
    for name in code.co_names:
        try: 
            script_class = local_space.get(name)
            if inspect.isclass(script_class):
                script = script_class()
                if isinstance(script, SvScript):
                    print("Script Node found script {}".format(name))
                    script = script
                    globals().update(local_space)
        except Exception as Err:
            print("Script Node couldn't load {0}".format(name))
            print(str(Err)) 
            pass
    return script
    
