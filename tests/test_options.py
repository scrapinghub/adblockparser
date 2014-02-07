# -*- coding: utf-8 -*-
from __future__ import absolute_import
import pytest
from adblockparser import AdblockRule

SPLIT_OPTIONS_TESTS = [
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
    ),
    (
        "domain=~example.com,foo.example.com,script",
        ["domain=~example.com,foo.example.com", "script"]
    ),
]

DOMAIN_PARSING_TESTS = [
    ("domain=example.com", {'example.com': True}),
    ("domain=example.com|example.net", {
        'example.com': True,
        'example.net': True
    }),
    ("domain=~example.com", {'example.com': False}),
    ("domain=example.com|~foo.example.com", {
        'example.com': True,
        'foo.example.com': False
    }),
    ("domain=~foo.example.com|example.com", {
        'example.com': True,
        'foo.example.com': False
    }),
    ("domain=example.com,example.net", {
        'example.com': True,
        'example.net': True
    }),
    ("domain=example.com|~foo.example.com", {
        'example.com': True,
        'foo.example.com': False
    }),
    ("domain=~msnbc.msn.com,~www.nbcnews.com", {
        'msnbc.msn.com': False,
        'www.nbcnews.com': False
    }),
]

PARSE_OPTIONS_TESTS = [
    ("domain=foo.bar", {}),
    ("+Ads/$~stylesheet", {'stylesheet': False}),
    ("-advertising-$domain=~advertise.bingads.domain.com", {
        "domain": {'advertise.bingads.domain.com': False}
    }),
    (".se/?placement=$script,third-party", {
        'script': True,
        'third-party': True
    }),
    ("||tst.net^$object-subrequest,third-party,domain=domain1.com|domain5.com", {
        'object-subrequest': True,
        'third-party': True,
        'domain': {
            'domain1.com': True,
            'domain5.com': True,
        }
    })
]

@pytest.mark.parametrize(('text', 'result'), SPLIT_OPTIONS_TESTS)
def test_option_splitting(text, result):
    assert AdblockRule._split_options(text) == result


@pytest.mark.parametrize(('text', 'result'), DOMAIN_PARSING_TESTS)
def test_domain_parsing(text, result):
    assert AdblockRule._parse_domain_option(text) == result


@pytest.mark.parametrize(('text', 'result'), PARSE_OPTIONS_TESTS)
def test_options_extraction(text, result):
    rule = AdblockRule(text)
    assert rule.options == result

