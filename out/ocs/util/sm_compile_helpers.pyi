from pathlib import Path

def ensure_cache_dir(base_dir: Path) -> Path: ...
def autoconf_run(working_dir: Path) -> None: ...
def get_lock_dir_path(cache_dir_base: Path, repo_dir: Path, tbox_id: str=...) -> Path: ...
def verify_full_win_pageheap(shell_path: Path) -> None: ...
