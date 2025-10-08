from labki_packs_tools import const


def test_schema_dir():
    """
    Mild duplicate of the version in test_schema_dir in test_packaging -
    we want to test that the schema dir and accompanying consts
    are correctly found even when installed in editable mode.

    Just a mere test for existence, correctness and resolution is tested elsewhere
    """
    assert const.SCHEMA_DIR.exists()
    assert const.SCHEMA_INDEX.exists()
