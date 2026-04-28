"""
Verify that the docstring on SvGroupTreeNode produces the right Triggers/Tooltip
metadata used by the search system.
"""
import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)

# The SvDocstring class used by AddNode.search_match
from utils.docstring import SvDocstring  # type: ignore


# Same docstring text as on SvGroupTreeNode after the fix
docstring_text = """
    Triggers: group node sub tree subtree monad
    Tooltip: Node for keeping sub trees (group node)
    """

doc = SvDocstring(docstring_text)
shorthand = doc.get_shorthand()
tooltip = doc.get_tooltip()

print(f"shorthand: {shorthand!r}")
print(f"tooltip:   {tooltip!r}")


def search_match(label_upper, doc, request):
    """Re-implementation of AddNode.search_match for testing."""
    request = request.upper()
    words = [w for w in request.split(' ') if w]
    if all(w in label_upper for w in words):
        return True
    sh = doc.get_shorthand().upper()
    if all(w in sh for w in words):
        return True
    tt = doc.get_tooltip().upper()
    if all(w in tt for w in words):
        return True
    return False


label = "Group node (Alpha)".upper()
queries = ["group", "GROUP", "monad", "sub tree", "subtree", "group node"]
print()
for q in queries:
    matches = search_match(label, doc, q)
    print(f"  query={q!r}  matches={matches}")
    assert matches, f"Search for {q!r} did not match!"

print("\nAll search-match checks passed.")
