# clone_repos.py
import os, subprocess, shutil, stat, time, dulwich
from dulwich import porcelain
from dulwich.errors import NotGitRepository

from common_helpers import base_dir
REPO_DIR = base_dir() / "repos"

def _unlock(func, path, exc_info):
    """Clear read-only bit and retry the failed os.remove / os.rmdir."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def _wipe_repo(dest_path, attempts=3) -> bool:
    """Try to delete dest_path; return True if it's gone."""
    for _ in range(attempts):
        if not os.path.exists(dest_path):
            return True
        try:
            shutil.rmtree(dest_path, onerror=_unlock)
        except Exception:
            pass
        if not os.path.exists(dest_path):
            return True
        time.sleep(0.5)           # give Windows a moment
    return False

def get_repo_basename(url: str) -> str:
    return url.rstrip("/").split("/")[-1]

def clone_repo(repo_url: str) -> str | None:
    REPO_DIR.mkdir(exist_ok=True)
    dest_path = REPO_DIR / get_repo_basename(repo_url)

    # 1. remove stale copy
    if dest_path.exists():
        print("⚙️  Dọn dẹp repo cũ:", dest_path)
        _wipe_repo(dest_path)          # best effort
        shutil.rmtree(dest_path, ignore_errors=True)

    # 2. fresh clone
    try:
        print(f"⏳ Cloning {repo_url} vào {dest_path} ...")
        porcelain.clone(repo_url, dest_path, checkout=True)  # remove depth for full history
        print("✅ Clone thành công:", repo_url)
        return str(dest_path)
    except Exception as exc:
        print("❌ Lỗi clone:", exc)
        return None

