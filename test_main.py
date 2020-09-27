from main import has_en


def test_has_en():
    assert has_en('lala')
    assert has_en('LALA')
    assert not has_en('עברית')
    assert has_en('עברית English')
