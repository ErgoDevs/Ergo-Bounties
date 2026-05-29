import json

from src.core.config import BountyConfig


def test_config_loads_root_dotenv_token(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("github_token=local-token\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("github_token", raising=False)

    config = BountyConfig()

    assert config.github_token == "local-token"


def test_config_prefers_environment_token(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("GITHUB_TOKEN=file-token\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_TOKEN", "env-token")
    monkeypatch.delenv("github_token", raising=False)

    config = BountyConfig()

    assert config.github_token == "env-token"


def test_load_json_config_requires_list(tmp_path, monkeypatch):
    config_dir = tmp_path / "src" / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "tracked_repos.json").write_text(json.dumps({"owner": "org"}), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_TOKEN", "token")

    config = BountyConfig()

    assert config.load_tracked_repos() == []
