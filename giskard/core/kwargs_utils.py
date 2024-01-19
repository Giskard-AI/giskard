from typing import Dict, List, Optional, Set, Tuple, Union

import inspect
from collections import defaultdict


def get_imports_code(obj):
    imports = _get_imports(obj)
    return "\n".join([f'from {module} import {", ".join(classes)}' for module, classes in imports.items()])


def _get_imports(obj, imports: Optional[defaultdict] = None):
    imports = imports or defaultdict(set)
    module = inspect.getmodule(obj)

    if isinstance(obj, Dict):
        for i in obj.values():
            imports = _get_imports(i, imports)
    elif isinstance(obj, Union[List, Set, Tuple]):
        for i in obj:
            print(i)
            imports = _get_imports(i, imports)
    elif hasattr(obj, "__dict__"):
        imports = _get_imports(obj.__dict__.values(), imports)

    if module is None:
        return imports

    imports[module.__name__].add(obj.__class__.__name__)
    return imports
