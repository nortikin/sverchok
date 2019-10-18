
from os.path import basename, splitext, dirname, join, exists
from os import walk

import sverchok
from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info, error

class DocumentationTests(SverchokTestCase):

    def test_all_node_docs_in_trees(self):
        """
        Check that each node documentation file is mentioned in corresponding index file.
        """

        def check(index_file_path, doc_file_path):
            (name, ext) = splitext(basename(doc_file_path))
            found = False
            with open(index_file_path, 'r') as index:
                for line in index:
                    line = line.strip()
                    if line == name:
                        found = True
                        break
            return found

        def check_dir(directory, fnames):
            dir_name = basename(directory)
            index_name = dir_name + "_index.rst"
            index_file_path = join(directory, index_name)
            bad_files = []
            for fname in fnames:
                if fname.endswith("_index.rst"):
                    continue
                if not check(index_file_path, fname):
                    bad_files.append(fname)
            if bad_files:
                error("The following files are not mentioned in %s:\n%s", index_name, "\n".join(bad_files))
                self.fail("Not all node documentation files are mentioned in their corresponding indexes.")

        sv_init = sverchok.__file__
        docs_dir = join(dirname(sv_init), "docs", "nodes")

        for directory, subdirs, fnames in walk(docs_dir):
            with self.subTest(directory=basename(directory)):
                check_dir(directory, fnames)

    def test_node_docs_refs_from_trees(self):

        def check_dir(directory):
            dir_name = basename(directory)
            index_name = dir_name + "_index.rst"
            index_file_path = join(directory, index_name)
            bad_files = []

            if exists(index_file_path):
                with open(index_file_path, 'r') as index:
                    start = False
                    for line in index:
                        line = line.strip()
                        if not line:
                            continue
                        if ":maxdepth:" in line:
                            start = True
                            continue
                        if not start:
                            continue
                        doc_name = line + ".rst"
                        doc_path = join(directory, doc_name)
                        if not exists(doc_path):
                            bad_files.append(doc_name)

                if bad_files:
                    error("The following files, which are referenced from %s, do not exist:\n%s", index_name, "\n".join(bad_files))
                    self.fail("Not all node documentation referenced from index files exist.")

        sv_init = sverchok.__file__
        docs_dir = join(dirname(sv_init), "docs", "nodes")

        for directory, subdirs, fnames in walk(docs_dir):
            with self.subTest(directory=basename(directory)):
                check_dir(directory)

