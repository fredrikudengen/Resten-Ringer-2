import os
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_src_dir = os.path.join(_project_root, "src")
_tests_dir = os.path.join(_project_root, "tests")  # for `from fakes import ...`
for _path in (_src_dir, _tests_dir):
    if _path not in sys.path:
        sys.path.insert(0, _path)
