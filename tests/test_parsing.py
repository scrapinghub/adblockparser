# -*- coding: utf-8 -*-
from __future__ import absolute_import
from adblockparser import AdblockRules, AdblockRule, AdblockParsingError

import pytest

try:
    import re2
    USE_RE2 = [True, False, 'auto']
except Exception:
    USE_RE2 = ['auto']

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


RULES_WITH_OPTIONS_TESTS = {
    # rule: url, params, matches?
    "||example.com": [
        ("http://example.com", {'third-party': True}, True),
        ("http://example2.com", {'third-party': True}, False),
        ("http://example.com", {'third-party': False}, True),
    ],
    "||example.com^$third-party": [
        ("http://example.com", {'third-party': True}, True),
        ("http://example2.com", {'third-party': True}, False),
        ("http://example.com", {'third-party': False}, False),
    ],
    "||example.com^$third-party,~script": [
        ("http://example.com", {'third-party': True, 'script': True}, False),
        ("http://example.com", {'third-party': True, 'script': False}, True),
        ("http://example2.com", {'third-party': True, 'script': False}, False),
        ("http://example.com", {'third-party': False, 'script': False}, False),
    ],

    "adv$domain=example.com|example.net": [
        ("http://example.net/adv", {'domain': 'example.net'}, True),
        ("http://somewebsite.com/adv", {'domain': 'example.com'}, True),
        ("http://www.example.net/adv", {'domain': 'www.example.net'}, True),
        ("http://my.subdomain.example.com/adv", {'domain': 'my.subdomain.example.com'}, True),

        ("http://example.com/adv", {'domain': 'badexample.com'}, False),
        ("http://example.com/adv", {'domain': 'otherdomain.net'}, False),
        ("http://example.net/ad", {'domain': 'example.net'}, False),
    ],

    "adv$domain=example.com|~foo.example.com": [
        ("http://example.net/adv", {'domain': 'example.com'}, True),
        ("http://example.net/adv", {'domain': 'foo.example.com'}, False),
        ("http://example.net/adv", {'domain': 'www.foo.example.com'}, False),
    ],

    "adv$domain=~example.com|foo.example.com": [
        ("http://example.net/adv", {'domain': 'example.com'}, False),
        ("http://example.net/adv", {'domain': 'foo.example.com'}, True),
        ("http://example.net/adv", {'domain': 'www.foo.example.com'}, True),
    ],

    "adv$domain=~example.com": [
        ("http://example.net/adv", {'domain': 'otherdomain.com'}, True),
        ("http://somewebsite.com/adv", {'domain': 'example.com'}, False),
    ],

    "adv$domain=~example.com|~example.net": [
        ("http://example.net/adv", {'domain': 'example.net'}, False),
        ("http://somewebsite.com/adv", {'domain': 'example.com'}, False),
        ("http://www.example.net/adv", {'domain': 'www.example.net'}, False),
        ("http://my.subdomain.example.com/adv", {'domain': 'my.subdomain.example.com'}, False),

        ("http://example.com/adv", {'domain': 'badexample.com'}, True),
        ("http://example.com/adv", {'domain': 'otherdomain.net'}, True),
        ("http://example.net/ad", {'domain': 'example.net'}, False),
    ],

    "adv$domain=example.com|~example.net": [
        # ~example.net should be ignored here
        ("http://example.net/adv", {'domain': 'example.net'}, False),
        ("http://somewebsite.com/adv", {'domain': 'example.com'}, True),
        ("http://www.example.net/adv", {'domain': 'www.example.net'}, False),
        ("http://my.subdomain.example.com/adv", {'domain': 'my.subdomain.example.com'}, True),

        ("http://example.com/adv", {'domain': 'badexample.com'}, False),
        ("http://example.com/adv", {'domain': 'otherdomain.net'}, False),
        ("http://example.net/ad", {'domain': 'example.net'}, False),
    ],

    "adv$domain=example.com,~foo.example.com,script": [
        ("http://example.net/adv", {'domain': 'example.com', 'script': True}, True),
        ("http://example.net/adv", {'domain': 'foo.example.com', 'script': True}, False),
        ("http://example.net/adv", {'domain': 'www.foo.example.com', 'script': True}, False),

        ("http://example.net/adv", {'domain': 'example.com', 'script': False}, False),
        ("http://example.net/adv", {'domain': 'foo.example.com', 'script': False}, False),
        ("http://example.net/adv", {'domain': 'www.foo.example.com', 'script': False}, False),
    ],

    "$websocket,domain=extratorrent.cc|firstrowau.eu": [
        ("http://example.com", {'domain': 'extratorrent.cc', 'websocket': True}, True),
        ("http://example.com", {'domain': 'extratorrent.cc', 'websocket': False}, False),
    ]
}

MULTIRULES_WITH_OPTIONS_TESTS = {
    # rules: url, params, should_block
    ("adv", "@@advice.$~script"): [
        ("http://example.com/advice.html", {'script': False}, False),
        ("http://example.com/advice.html", {'script': True}, True),
        ("http://example.com/advert.html", {'script': False}, True),
        ("http://example.com/advert.html", {'script': True}, True),
    ],
}

@pytest.mark.parametrize('use_re2', USE_RE2)
@pytest.mark.parametrize(('rule_text', 'results'), DOCUMENTED_TESTS.items())
def test_documented_examples(rule_text, results, use_re2):
    rule = AdblockRule(rule_text)
    rules = AdblockRules([rule_text], use_re2=use_re2)

    for url in results["blocks"]:
        assert rule.match_url(url)
        assert rules.should_block(url)

    for url in results["doesn't block"]:
        assert not rule.match_url(url)
        assert not rules.should_block(url)


@pytest.mark.parametrize('use_re2', USE_RE2)
@pytest.mark.parametrize(('rules', 'results'), RULE_EXCEPTION_TESTS.items())
def test_rule_exceptions(rules, results, use_re2):
    rules = AdblockRules(rules, use_re2=use_re2)

    for url in results["blocks"]:
        assert rules.should_block(url)

    for url in results["doesn't block"]:
        assert not rules.should_block(url)


@pytest.mark.parametrize('use_re2', USE_RE2)
@pytest.mark.parametrize(('rule_text', 'results'), RULES_WITH_OPTIONS_TESTS.items())
def test_rule_with_options(rule_text, results, use_re2):
    rule = AdblockRule(rule_text)
    rules = AdblockRules([rule_text], use_re2=use_re2)

    for url, params, match in results:
        assert rule.match_url(url, params) == match
        assert rules.should_block(url, params) == match


@pytest.mark.parametrize('use_re2', USE_RE2)
@pytest.mark.parametrize(('rules', 'results'), MULTIRULES_WITH_OPTIONS_TESTS.items())
def test_rules_with_options(rules, results, use_re2):
    rules = AdblockRules(rules, use_re2=use_re2)
    for url, params, should_block in results:
        assert rules.should_block(url, params) == should_block


def test_regex_rules():
    rules = AdblockRules(["/banner\d+/"])
    assert rules.should_block("banner123")
    assert not rules.should_block("banners")


def test_rules_supported_options():
    rules = AdblockRules(["adv", "@@advice.$~script"])
    assert not rules.should_block("http://example.com/advice.html", {'script': False})

    # exception rule should be discarded if "script" option is not supported
    rules2 = AdblockRules(["adv", "@@advice.$~script"], supported_options=[])
    assert rules2.should_block("http://example.com/advice.html", {'script': False})


def test_rules_instantiation():
    rule = AdblockRule("adv")
    rules = AdblockRules([rule])
    assert rule.match_url("http://example.com/adv")
    assert rules.should_block("http://example.com/adv")


def test_empty_rules():
    rules = AdblockRules(["adv", "", " \t", AdblockRule("adv2")])
    assert len(rules.rules) == 2


def test_empty_regexp_rules():
    with pytest.raises(AdblockParsingError):
        AdblockRules(['adv', '/', '//'])
