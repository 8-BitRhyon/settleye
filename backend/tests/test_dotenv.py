"""Tests for minimal .env loading (no third-party dependency).

The live scripts read process env, but humans keep keys in `.env`.
The loader bridges the two: explicit path or auto-found repo-root file,
never overriding real environment variables, silent when absent.
"""

from app.extract.live_check import load_dotenv_file, repo_env_path


def test_loads_key_from_file(tmp_path, monkeypatch) -> None:
    env = tmp_path / ".env"
    env.write_text('BASETEN_API_KEY="file-key"\n', encoding="utf-8")
    monkeypatch.delenv("BASETEN_API_KEY", raising=False)
    load_dotenv_file(env)
    import os

    assert os.environ["BASETEN_API_KEY"] == "file-key"
    del os.environ["BASETEN_API_KEY"]


def test_real_env_wins_over_file(tmp_path, monkeypatch) -> None:
    env = tmp_path / ".env"
    env.write_text("BASETEN_API_KEY=file-key\n", encoding="utf-8")
    monkeypatch.setenv("BASETEN_API_KEY", "real-key")
    load_dotenv_file(env)
    import os

    assert os.environ["BASETEN_API_KEY"] == "real-key"


def test_missing_file_is_silent(tmp_path) -> None:
    load_dotenv_file(tmp_path / "nope.env")


def test_comments_and_exports_ignored(tmp_path, monkeypatch) -> None:
    env = tmp_path / ".env"
    env.write_text(
        "# comment\nexport QUOTED='q v'\nPLAIN=plain\n", encoding="utf-8"
    )
    monkeypatch.delenv("QUOTED", raising=False)
    monkeypatch.delenv("PLAIN", raising=False)
    load_dotenv_file(env)
    import os

    assert os.environ["QUOTED"] == "q v"
    assert os.environ["PLAIN"] == "plain"
    del os.environ["QUOTED"]
    del os.environ["PLAIN"]


def test_repo_env_path_points_at_repo_root() -> None:
    assert repo_env_path().name == ".env"
    assert repo_env_path().parent.name == "promise-check"
