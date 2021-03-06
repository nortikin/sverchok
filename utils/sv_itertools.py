from itertools import chain, repeat, zip_longest
from sverchok.data_structure import levels_of_list_or_np, list_match_func

# the class based should be slower but kept until tested
class SvZipExhausted(Exception):
    pass

class SvSentinel:
    def __init__(self, fl, top):
        self.fl = fl
        self.top = top
        self.done = False

    def __next__(self):
        if self.done:
            raise StopIteration
        self.top.counter -= 1
        if not self.top.counter:
            raise SvZipExhausted
        self.done = True
        return self.fl

    def __iter__(self):
        return self

class sv_zip_longest:
    def __init__(self, *args):
        self.counter = len(args)
        self.iterators = []
        for lst in args:
            fl = lst[-1]
            filler = repeat(fl)
            self.iterators.append(chain(lst, SvSentinel(fl,self), filler))

    def __next__(self):
        try:
            if self.counter:
                return tuple(map(next, self.iterators))
            else:
                raise StopIteration
        except SvZipExhausted:
            raise StopIteration

    def __iter__(self):
        return self


def sv_zip_longest2(*args):
    # by zeffi
    longest = max([len(i) for i in args])
    itrs = [iter(sl) for sl in args]
    for i in range(longest):
        yield tuple((next(iterator, args[idx][-1]) for idx, iterator in enumerate(itrs)))


def recurse_fx(l, f):
    if isinstance(l, (list, tuple)):
        return [recurse_fx(i, f) for i in l]
    else:
        return f(l)

def recurse_fxy(l1, l2, f):
    l1_type = isinstance(l1, (list, tuple))
    l2_type = isinstance(l2, (list, tuple))
    if not (l1_type or l2_type):
        return f(l1, l2)
    elif l1_type and l2_type:
        fl = l2[-1] if len(l1) > len(l2) else l1[-1]
        res = []
        res_append = res.append
        for x, y in zip_longest(l1, l2, fillvalue=fl):
            res_append(recurse_fxy(x, y, f))
        return res
    elif l1_type and not l2_type:
        return [recurse_fxy(x, l2, f) for x in l1]
    else: #not l1_type and l2_type
        return [recurse_fxy(l1, y, f) for y in l2]

def recurse_f_multipar(params, f, matching_f):
    '''params will spread using the matching function (matching_f)
        on the lowest level applys f (function)'''
    is_list = [isinstance(l, (list, tuple)) for l in params]
    if any(is_list):
        res = []
        if not all(is_list):
            l_temp = []
            for l in params:
                if not isinstance(l, (list, tuple)):
                    l_temp.append([l])
                else:
                    l_temp.append(l)
                params = l_temp
        params = matching_f(params)
        for z in zip(*params):
            res.append(recurse_f_multipar(z,f, matching_f))
        return res
    else:
        return f(params)

def recurse_f_multipar_const(params, const, f, matching_f):
    '''params will spread using the matching function, the const is a constant
        parameter that you dont want to spread '''
    is_list = [isinstance(l, (list, tuple)) for l in params]
    if any(is_list):
        res = []
        if not all(is_list):
            l_temp = []
            for l in params:
                if not isinstance(l, (list, tuple)):
                    l_temp.append([l])
                else:
                    l_temp.append(l)
                params = l_temp
        params = matching_f(params)
        for z in zip(*params):
            res.append(recurse_f_multipar_const(z, const, f, matching_f))
        return res
    else:
        return f(params, const)

def recurse_f_level_control(params, constant, main_func, matching_f, desired_levels, concatenate="APPEND"):
    '''params will spread using the matching function (matching_f), the const is a constant
        parameter that you dont want to spread , the main_func is the function to apply
        and the desired_levels should be like [1, 2, 1, 3...] one level per parameter'''
    input_levels = [levels_of_list_or_np(p) for p in params]
    over_levels = [lv > dl for lv, dl in zip(input_levels, desired_levels)]
    if any(over_levels):
        p_temp = []
        result = []
        result_add = result.extend if concatenate == 'EXTEND' else result.append
        for p, lv, dl in zip(params, input_levels, desired_levels):
            if lv <= dl:
                p_temp.append([p])
            else:
                p_temp.append(p)
        params = matching_f(p_temp)
        for g in zip(*params):
            result_add(recurse_f_level_control(matching_f(g), constant, main_func, matching_f, desired_levels, concatenate=concatenate))
    else:
        result = main_func(params, constant, matching_f)
    return result

def process_matched(params, main_func, matching_mode, input_nesting, outputs_num):
    '''params will spread using the matching fmode,
       the main_func is the function to apply
       the input_nesting should be like an Integer List like [1, 2, 1, 3...] one level per parameter
       outputs_num: number of outputs (Integer)
       '''
    input_levels = [levels_of_list_or_np(p) for p in params]

    over_levels = [lv > dl for lv, dl in zip(input_levels, input_nesting)]
    one_output = outputs_num == 1
    matching_f = list_match_func[matching_mode]
    if one_output:
        result = []
    else:
        result = [[] for l in range(outputs_num)]
    if any(over_levels):
        p_temp = []
        for p, lv, dl in zip(params, input_levels, input_nesting):
            print(lv,dl)
            if lv <= dl:
                p_temp.append([p])
            else:
                p_temp.append(p)

        params = matching_f(p_temp)
        for g in zip(*params):
            local_result = process_matched(g, main_func, matching_mode, input_nesting, outputs_num)
            append_result(result, local_result, one_output)

    else:
        result = main_func(matching_f(params))

    return result
def append_result(result, local_result, one_output):
    if one_output:
        result.append(local_result)
    else:
        for r, r_local in zip(result, local_result):
            r.append(r_local)
def extend_result(result, local_result, one_output):
    if one_output:
        result.extend(local_result)
    else:
        for r, r_local in zip(result, local_result):
            r.extend(r_local)

def extend_if_needed(vl, wl, default=0.5):
    # match wl to correspond with vl
    try:
        last_value = wl[-1][-1]
    except:
        last_value = default

    if (len(vl) > len(wl)):
        num_new_empty_lists = len(vl) - len(wl)
        for emlist in range(num_new_empty_lists):
            wl.append([])

    # extend each sublist in wl to match quantity found in sublists of v1
    for i, vlist in enumerate(vl):
        if (len(vlist) > len(wl[i])):
            num_new_repeats = len(vlist) - len(wl[i])
            for n in range(num_new_repeats):
                wl[i].append(last_value)
    return wl
