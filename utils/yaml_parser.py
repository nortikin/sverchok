"""
Limited implementation of reading yaml files. Should be replaced when such
library is available in build-in Python source.
"""


def load(file):
    with open(file) as yaml_lines:
        stack: list = []
        for raw_line in yaml_lines:
            line = YamlLine(raw_line)
            if line.is_blank or line.is_comment:
                continue
            while len(stack) > line.indent_level:
                stack.pop()
            current = stack[-1] if stack else ...

            if line.is_list_value:

                # init root list
                if not stack:
                    data = []
                    stack.append(data)
                    current = data

                # replace None dict value with a list
                if current is None:  # all dicts can keep only dicts for now
                    new_list = []
                    for key in stack[-2].keys():  # should have only one key
                        stack[-2][key] = new_list
                        break
                    stack[-1] = new_list
                    current = new_list

                if line.is_dict_value:  # it is list item and new dictionary
                    if not isinstance(current, list):
                        raise TypeError("A list was expected here")
                    new_dict = {line.key: line.dict_value}
                    current.append(new_dict)
                    stack.append(new_dict)
                    stack.append(line.dict_value)

                else:  # new list item to a list
                    stack[-1].append(line.list_value)

            elif line.is_dict_value:
                raise TypeError(f'Dictionary values are excepted only as part of some list - "{raw_line}"')
            else:
                raise TypeError(f'Any value should be either list of dictionary key - "{raw_line}"')
    return data


class YamlLine:
    def __init__(self, line):
        self._line: str = self._remove_comment(line)

    @property
    def is_comment(self):
        return self._line.strip().startswith('#')

    @property
    def is_blank(self):
        return not self._line.strip()

    @property
    def is_list_value(self):
        return self._line.strip().startswith('-')

    @property
    def is_dict_value(self):
        line = self._line.expandtabs(1).strip()
        return ': ' in line or ':' == line[-1]

    @property
    def indent_level(self):
        # https://docs.python.org/3/reference/lexical_analysis.html#indentation
        first_letter, *_ = self._line.strip()
        indention = self._line.expandtabs(4).index(first_letter)
        return (indention // 4) * 2 + 1  # fragile

    @property
    def key(self):
        line = self._line.expandtabs(1).strip()
        if line.startswith('-'):
            line = line[1:].strip()
        if ':' == line[-1]:
            return line[:-1].strip()
        key, value = line.split(': ')
        return key.strip()

    @property
    def list_value(self):
        line = self._line.expandtabs(1).strip()
        if self.is_list_value:
            return line.split('-', 1)[1].strip()

    @property
    def dict_value(self):
        line = self._line.expandtabs(1).strip()
        if ':' == line[-1]:
            return None
        key, value = line.split(': ')
        return value.strip().strip("'\"")  # always return as a string for now

    @staticmethod
    def _remove_comment(line):
        line, _, comment = line.partition(' #')  # can be incorrect inside string values
        return line


if __name__ == '__main__':
    from pprint import pprint
    pprint(load('../index.yaml'))
