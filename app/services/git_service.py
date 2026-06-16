from dataclasses import dataclass
from pathlib import Path
import subprocess

from app.core.config import settings


@dataclass
class GitSyncResult:
    status: str
    detail: str | None = None


def _run_git(vault: Path, args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=vault,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if check and result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip())
    return result


def sync_obsidian_vault_to_git(
    report_date: str,
    vault_path: str | None = None,
    auto_commit: bool | None = None,
    branch: str | None = None,
) -> GitSyncResult:
    enabled = settings.git_auto_commit if auto_commit is None else auto_commit
    if not enabled:
        return GitSyncResult(status="skipped_disabled")

    configured_vault_path = vault_path if vault_path is not None else settings.obsidian_vault_path
    if not configured_vault_path:
        return GitSyncResult(status="skipped_not_configured")

    vault = Path(configured_vault_path).expanduser()
    if not vault.exists() or not vault.is_dir():
        return GitSyncResult(status="failed", detail=f"Vault path does not exist: {vault}")

    is_repo = _run_git(vault, ["rev-parse", "--is-inside-work-tree"])
    if is_repo.returncode != 0 or is_repo.stdout.strip() != "true":
        return GitSyncResult(status="skipped_not_git_repo")

    add_result = _run_git(vault, ["add", "."])
    if add_result.returncode != 0:
        return GitSyncResult(status="failed", detail=(add_result.stderr or add_result.stdout).strip())

    for pattern in [".env", ".env.*"]:
        _run_git(vault, ["reset", "--", pattern])

    no_changes = _run_git(vault, ["diff", "--cached", "--quiet"])
    if no_changes.returncode == 0:
        return GitSyncResult(status="skipped_no_changes")

    commit_message = f"Add daily intelligence report {report_date}"
    commit_result = _run_git(vault, ["commit", "-m", commit_message])
    if commit_result.returncode != 0:
        return GitSyncResult(status="failed", detail=(commit_result.stderr or commit_result.stdout).strip())

    target_branch = branch if branch is not None else settings.git_branch
    push_args = ["push"]
    if target_branch:
        push_args.extend(["origin", f"HEAD:{target_branch}"])
    push_result = _run_git(vault, push_args)
    if push_result.returncode != 0:
        return GitSyncResult(status="failed", detail=(push_result.stderr or push_result.stdout).strip())

    return GitSyncResult(status="success")
