import yaml

import keel.config
from keel import store as store_mod


def test_get_store_honors_configured_catalog_dir(tmp_path, monkeypatch):
    # a minimal throwaway catalog with a single threat
    threats = tmp_path / "threats"
    threats.mkdir()
    (threats / "T-SANDBOX.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "T-SANDBOX",
                "title": "Sandbox threat",
                "harm": "data-exposed",
                "weaknesses": [{"component": "tool", "text": "sandbox weakness"}],
                "reachability": "NOT applicable in the sandbox",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(keel.config.settings, "catalog_dir", str(tmp_path))
    store_mod.set_store(None)
    try:
        store = store_mod.get_store()
        assert store.dir == tmp_path
        assert "T-SANDBOX" in store.threats
    finally:
        store_mod.set_store(None)
