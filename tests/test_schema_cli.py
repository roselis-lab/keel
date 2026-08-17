import subprocess
import sys


def test_schema_check_passes_after_write(tmp_path):
    # writing then checking in the same dir must succeed
    from keel.schema_export import schemas_are_fresh, write_schemas

    write_schemas(tmp_path)
    assert schemas_are_fresh(tmp_path)


def test_cli_schema_check_exit_code():
    # the committed schema/ must be fresh, so --check exits 0
    r = subprocess.run(
        [sys.executable, "-m", "keel", "schema", "--check"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
