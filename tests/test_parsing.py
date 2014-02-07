# -*- coding: utf-8 -*-
from __future__ import absolute_import
from adblock_parser import AdblockRules

import pytest

try:
    import re2
    USE_RE2 = [True, False]
except Exception:
    USE_RE2 = [False]

# examples are from https://adblockplus.org/en/filter-cheatsheet
# and https://adblockplus.org/en/filters
DOCUMENTED_TESTS = {
    "/banner/*/img^": {
        "blocks": [
            "http://example.com/banner/foo/img",
            "http://example.com/banner/foo/bar/img?param",
            "http://example.com/banner//img/foo",
        ],
        "doesn't block": [
            "http://example.com/banner/img",
            "http://example.com/banner/foo/imgraph",
            "http://example.com/banner/foo/img.gif",
        ]
    },

    "||ads.example.com^": {
        "blocks": [
            "http://ads.example.com/foo.gif",
            "http://server1.ads.example.com/foo.gif",
            "https://ads.example.com:8000/",
        ],
        "doesn't block": [
            "http://ads.example.com.ua/foo.gif",
            "http://example.com/redirect/http://ads.example.com/",
        ]
    },

    "|http://example.com/|": {
        "blocks": [
            "http://example.com/",
        ],
        "doesn't block": [
            "http://example.com/foo.gif",
            "http://example.info/redirect/http://example.com/",
        ]
    },

    "swf|": {
        "blocks": ["http://example.com/annoyingflash.swf"],
        "doesn't block": ["http://example.com/swf/index.html"]
    },

    "|http://baddomain.example/": {
        "blocks": ["http://baddomain.example/banner.gif"],
        "doesn't block": ["http://gooddomain.example/analyze?http://baddomain.example"]
    },

    "||example.com/banner.gif": {
        "blocks": [
            "http://example.com/banner.gif",
            "https://example.com/banner.gif",
            "http://www.example.com/banner.gif",
        ],
        "doesn't block": [
            "http://badexample.com/banner.gif",
            "http://gooddomain.example/analyze?http://example.com/banner.gif",
        ]
    },

    "http://example.com^": {
        "blocks": [
            "http://example.com/",
            "http://example.com:8000/ ",
        ],
        "doesn't block": [
            "http://example.com.ar/",
        ]
    },

    "^example.com^": {
        "blocks": ["http://example.com:8000/foo.bar?a=12&b=%D1%82%D0%B5%D1%81%D1%82"],
        "doesn't block": []
    },

    "^%D1%82%D0%B5%D1%81%D1%82^": {
        "blocks": ["http://example.com:8000/foo.bar?a=12&b=%D1%82%D0%B5%D1%81%D1%82"],
        "doesn't block": []
    },

    "^foo.bar^": {
        "blocks": ["http://example.com:8000/foo.bar?a=12&b=%D1%82%D0%B5%D1%81%D1%82"],
        "doesn't block": []
    },
}


RULE_EXCEPTION_TESTS = {
    ("adv", "@@advice."): {
        "blocks": ["http://example.com/advert.html"],
        "doesn't block": ["http://example.com/advice.html"]
    },
    ("@@advice.", "adv"): {
        "blocks": ["http://example.com/advert.html"],
        "doesn't block": ["http://example.com/advice.html"]
    },
    ("@@|http://example.com", "@@advice.", "adv", "!foo"): {
        "blocks": [
            "http://examples.com/advert.html"
        ],
        "doesn't block": [
            "http://example.com/advice.html",
            "http://example.com/advert.html"
            "http://examples.com/advice.html"
            "http://examples.com/#!foo"
        ]
    },
}


@pytest.mark.parametrize(('use_re2'), USE_RE2)
@pytest.mark.parametrize(('rule', 'results'), DOCUMENTED_TESTS.items())
def test_documented_examples(rule, results, use_re2):
    rules = AdblockRules([rule], use_re2=use_re2)

    for url in results["blocks"]:
        assert rules.should_block(url)

    for url in results["doesn't block"]:
        assert not rules.should_block(url)


@pytest.mark.parametrize(('use_re2'), USE_RE2)
@pytest.mark.parametrize(('rules', 'results'), RULE_EXCEPTION_TESTS.items())
def test_rule_exceptions(rules, results, use_re2):
    rules = AdblockRules(rules, use_re2=use_re2)

    for url in results["blocks"]:
        assert rules.should_block(url)

    for url in results["doesn't block"]:
        assert not rules.should_block(url)


@pytest.mark.xfail
def test_regex_rules():
    # Regex rules are not supported yet.
    # There are no such rules in EasyList filters.
    rules = AdblockRules(["/banner\d+/"])
    assert rules.should_block("banner123")
    assert not rules.should_block("banners")


