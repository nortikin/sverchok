from collections import UserList


class NodeMenuList(UserList):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.icon_name = None

    def set_property(self, name, value):
        if not hasattr(self, name):
            print(KeyError(f'NodeMenuList does have "{name}" attribute'))
        setattr(self, name, value)

    def pprint(self, indent=''):
        print(f"{indent}## {self.name} (icon_name={self.icon_name}):")
        indent += "    "
        for v in self.data:
            if hasattr(v, 'pprint'):
                v.pprint(indent)
            else:
                print(f"{indent}{v}")

    def __repr__(self):
        return f"<{self.name} (icon_name={self.icon_name}): {super().__repr__()}>"


class MenuStringLine:
    def __init__(self, line):
        self._line = line

    @property
    def is_comment(self):
        return self._line.strip().startswith('>')

    @property
    def is_blank(self):
        return not self._line.strip()

    @property
    def is_category(self):
        return self._line.strip().startswith('##')

    @property
    def is_property(self):
        return not self.is_category and ":" in self._line

    @property
    def indention_level(self):
        # https://docs.python.org/3/reference/lexical_analysis.html#indentation
        first_letter, *_ = self._line.strip()
        indention = self._line.expandtabs(4).index(first_letter)
        return indention // 4

    @property
    def name(self):
        if self.is_category:
            _, category = self._line.split('##', 1)
            return category.strip()
        if self.is_property:
            name, value = self._line.split(':', 1)
            return name.strip()
        return self._line.strip()

    @property
    def value(self):
        if self.is_property:
            name, value = self._line.split(':', 1)
            return value.strip().strip("'\"")  # return as string


class MainNodeMenu:
    def __init__(self, file):
        self._struct = []
        self._parsing(file)

    def pprint(self):
        for v in self._struct:
            v.pprint()

    def _parsing(self, file):
        with open(file) as md:
            stack: list[NodeMenuList] = []
            for raw_line in md:
                line = MenuStringLine(raw_line)
                if line.is_blank or line.is_comment:
                    continue
                while len(stack) > line.indention_level:
                    stack.pop()
                if line.is_category:
                    menu_list = NodeMenuList(line.name)
                    if line.indention_level == 0:
                        self._struct.append(menu_list)
                    else:
                        stack[-1].append(menu_list)
                    stack.append(menu_list)
                elif line.is_property:
                    stack[-1].set_property(line.name, line.value)
                else:
                    stack[-1].append(line.name)

    def __repr__(self):
        return repr(self._struct)


if __name__ == "__main__":
    from tempfile import NamedTemporaryFile

    test_strings = b"""
> ### This file is parsed by menu.py
>
> The following rules apply to editing this file:
>
> - do not use tabs, anywhere
> - indent the Node's line using 4 spaces
> - if you aren't sure, follow the existing convention
>
> Failing to follow these points will break the node category parser.

## Generator
    icon_name: 'OBJECT_DATAMODE'

    SvLineNodeMK4
    SvSegmentGenerator
    ## SubGenerators
        SomeNode
        ## SubSubGenerator
            SomeNodeAgain
    NodeA
    NodeB

## Category2
    Node2
    """

    expected = "[<Generator: ['SvLineNodeMK4', 'SvSegmentGenerator', " \
               "<SubGenerators: ['SomeNode', <SubSubGenerator: " \
               "['SomeNodeAgain']>]>, 'NodeA', 'NodeB']>, <Category2: ['Node2']>]"

    tf = NamedTemporaryFile(delete=False)
    tf.write(test_strings)
    tf.close()  # makes it possible to read
    assert repr(MainNodeMenu(tf.name)) == expected
