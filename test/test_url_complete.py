from gfeeds.util.create_full_url import create_full_url


def test_create_full_url_already_full():
    assert (
        create_full_url('', 'https://example.org/') ==
        'https://example.org/'
    )
    assert (
        create_full_url('', 'https://example.org') ==
        'https://example.org'
    )
    assert (
        create_full_url('', 'http://example.org/') ==
        'http://example.org/'
    )
    assert (
        create_full_url('', 'http://example.org') ==
        'http://example.org'
    )
    assert (
        create_full_url('', 'https://example.org/foo') ==
        'https://example.org/foo'
    )
    assert (
        create_full_url('', 'https://example.org/foo/bar') ==
        'https://example.org/foo/bar'
    )
    assert (
        create_full_url('', 'https://example.org/foo/bar/') ==
        'https://example.org/foo/bar/'
    )


def test_create_full_url_abspath():
    assert (
        create_full_url('https://example.org/', '/') ==
        'https://example.org/'
    )
    assert (
        create_full_url('https://example.org/', '/foo') ==
        'https://example.org/foo'
    )
    assert (
        create_full_url('https://example.org/', '/foo/bar') ==
        'https://example.org/foo/bar'
    )
    assert (
        create_full_url('https://example.org/', '/foo/bar/') ==
        'https://example.org/foo/bar/'
    )
    assert (
        create_full_url('https://example.org', '/') ==
        'https://example.org/'
    )
    assert (
        create_full_url('https://example.org', '/foo') ==
        'https://example.org/foo'
    )
    assert (
        create_full_url('https://example.org', '/foo/bar') ==
        'https://example.org/foo/bar'
    )
    assert (
        create_full_url('https://example.org', '/foo/bar/') ==
        'https://example.org/foo/bar/'
    )


def test_create_full_url_relpath():
    assert (
        create_full_url('https://example.org/', '') ==
        'https://example.org/'
    )
    assert (
        create_full_url('https://example.org/', 'foo') ==
        'https://example.org/foo'
    )
    assert (
        create_full_url('https://example.org/', 'foo/bar') ==
        'https://example.org/foo/bar'
    )
    assert (
        create_full_url('https://example.org/', 'foo/bar/') ==
        'https://example.org/foo/bar/'
    )
    assert (
        create_full_url('https://example.org/baz/', 'foo') ==
        'https://example.org/baz/foo'
    )
    assert (
        create_full_url('https://example.org/baz/', 'foo/bar') ==
        'https://example.org/baz/foo/bar'
    )
    assert (
        create_full_url('https://example.org', '') ==
        'https://example.org/'
    )
    assert (
        create_full_url('https://example.org', 'foo') ==
        'https://example.org/foo'
    )
    assert (
        create_full_url('https://example.org', 'foo/bar') ==
        'https://example.org/foo/bar'
    )
    assert (
        create_full_url('https://example.org', 'foo/bar/') ==
        'https://example.org/foo/bar/'
    )
    assert (
        create_full_url('https://example.org/baz', 'foo') ==
        'https://example.org/baz/foo'
    )
    assert (
        create_full_url('https://example.org/baz', 'foo/bar') ==
        'https://example.org/baz/foo/bar'
    )
