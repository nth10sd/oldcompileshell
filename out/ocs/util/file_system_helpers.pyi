from pathlib import Path
from typing import Any

def handle_rm_readonly_files(_func: Any, path_: Path, exc: Any) -> None: ...
def rm_tree_incl_readonly_files(dir_tree: Path) -> None: ...
