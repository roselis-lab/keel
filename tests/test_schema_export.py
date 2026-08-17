from keel.schema_export import build_schemas


def test_threat_schema_has_frozen_vocab_enums():
    schemas = build_schemas()
    threat = schemas["threat"]
    assert threat["properties"]["harm"]["enum"] == [
        "wrong-decision", "data-exposed", "code-execution", "downtime", "reputation-legal",
    ]
    assert "title" in threat["required"]
    # weaknesses must carry its sub-schema so the UI can render the repeatable card
    assert threat["properties"]["weaknesses"]["type"] == "array"


def test_build_schemas_covers_all_entities():
    schemas = build_schemas()
    assert set(schemas) == {"threat", "mitigation", "weakness", "mitigation_link"}


def test_write_and_check_roundtrip(tmp_path):
    from keel.schema_export import write_schemas, schemas_are_fresh
    out = tmp_path / "schema"
    write_schemas(out)
    assert (out / "threat.schema.json").is_file()
    assert schemas_are_fresh(out) is True
    # a stale file is detected
    (out / "threat.schema.json").write_text("{}", encoding="utf-8")
    assert schemas_are_fresh(out) is False
