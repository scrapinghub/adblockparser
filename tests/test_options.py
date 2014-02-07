# -*- coding: utf-8 -*-
from __future__ import absolute_import
import pytest
from adblock_parser import AdblockRule

OPTIONS_TESTS = [
    (
        "subdocument,third-party",
        ["subdocument", "third-party"]
    ),
    (
        "object-subrequest,script,domain=~msnbc.msn.com,~www.nbcnews.com",
        ["object-subrequest", "script", "domain=~msnbc.msn.com,~www.nbcnews.com"],
    ),
    (
        "object-subrequest,script,domain=~msnbc.msn.com,~www.nbcnews.com",
        ["object-subrequest", "script", "domain=~msnbc.msn.com,~www.nbcnews.com"],
    ),
    (
        "~document,xbl,domain=~foo,bar,baz,~collapse,domain=foo.xbl|bar",
        ["~document", "xbl", "domain=~foo,bar,baz", "~collapse", "domain=foo.xbl|bar"]
    )
]

@pytest.mark.parametrize(('options_text', 'result'), OPTIONS_TESTS)
def test_option_splitting(options_text, result):
    assert result == AdblockRule.split_options(options_text)


def doctest_parse_domain():
    """
    >>> AdblockRule.parse_domain_option("domain=example.com")
    [(True, 'example.com')]
    >>> AdblockRule.parse_domain_option("domain=example.com|example.net")
    [(True, 'example.com'), (True, 'example.net')]
    >>> AdblockRule.parse_domain_option("domain=~example.com")
    [(False, 'example.com')]
    >>> AdblockRule.parse_domain_option("domain=example.com|~foo.example.com")
    [(True, 'example.com'), (False, 'foo.example.com')]
    >>> AdblockRule.parse_domain_option("domain=~foo.example.com|example.com")
    [(False, 'foo.example.com'), (True, 'example.com')]
    >>> AdblockRule.parse_domain_option("domain=example.com,example.net")
    [(True, 'example.com'), (True, 'example.net')]
    >>> AdblockRule.parse_domain_option("domain=example.com|~foo.example.com")
    [(True, 'example.com'), (False, 'foo.example.com')]
    >>> AdblockRule.parse_domain_option("domain=~msnbc.msn.com,~www.nbcnews.com")
    [(False, 'msnbc.msn.com'), (False, 'www.nbcnews.com')]
    """
    pass
