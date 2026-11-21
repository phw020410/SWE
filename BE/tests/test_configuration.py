import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def configurator(tmp_path):
    source = Path(__file__).resolve().parents[2] / "scripts/configure.py"
    spec = importlib.util.spec_from_file_location("swe_configure", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = tmp_path
    (tmp_path / "BE").mkdir()
    (tmp_path / "FE").mkdir()
    return module, tmp_path


def test_demo_configuration_uses_existing_be_fe_layout(configurator):
    configure, root = configurator
    configure.configure("demo")
    env = (root / "BE/.env").read_text()
    assert 'AI_PROVIDER="mock"' in env
    assert 'ENABLE_DEMO_ITEMS="true"' in env
    assert 'STORAGE_BACKEND="sqlite"' in env
    assert (root / "FE/.env.local").exists()
    assert not (root / "backend").exists()


@pytest.mark.parametrize("job_key", ["ALIO_SERVICE_KEY", "DATA_GOKR_SERVICE_KEY"])
def test_live_accepts_either_issuer_specific_job_key_without_printing_secrets(configurator, job_key, capsys):
    configure, root = configurator
    keys = root / "test-keys.txt"
    keys.write_text("GEMINI_API_KEY=test-model-key\nWORK24_AUTH_KEY=test-training-key\n"
                    "SUPABASE_URL=https://example.supabase.co\nSUPABASE_SERVICE_ROLE_KEY=test-db-key\n"
                    + job_key + "=test-job-secret\n")
    configure.configure("live", keys)
    env = (root / "BE/.env").read_text()
    assert f'{job_key}="test-job-secret"' in env
    assert 'ENABLE_DEMO_ITEMS="false"' in env
    assert 'STORAGE_BACKEND="supabase"' in env
    assert "test-job-secret" not in capsys.readouterr().out


def test_existing_configuration_is_not_silently_overwritten(configurator):
    configure, root = configurator
    configure.configure("demo")
    original = (root / "BE/.env").read_bytes()
    with pytest.raises(SystemExit):
        configure.configure("demo")
    assert (root / "BE/.env").read_bytes() == original
