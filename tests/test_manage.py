"""Tests for manage.py CLI — does not require a live DB."""
import subprocess
import sys


def test_manage_help_exits_zero():
    result = subprocess.run(
        [sys.executable, "manage.py", "--help"],
        capture_output=True, text=True,
        cwd="/Users/jaime.henao/arheanja/ABA-Projects/repo-andres/proyecto-facturas/.worktrees/saas-mvp"
    )
    assert result.returncode == 0
    assert "init-db" in result.stdout
    assert "create-org" in result.stdout


def test_manage_unknown_command_exits_nonzero():
    result = subprocess.run(
        [sys.executable, "manage.py", "unknown-command"],
        capture_output=True, text=True,
        cwd="/Users/jaime.henao/arheanja/ABA-Projects/repo-andres/proyecto-facturas/.worktrees/saas-mvp"
    )
    assert result.returncode != 0
