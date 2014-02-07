# -*- coding: utf-8 -*-
from __future__ import absolute_import
import pytest
from adblockparser import AdblockRule

COMMENT_RULES = [
    "[Adblock Plus 2.0]",
    "! Checksum: nVIXktYXKU6M+cu+Txkhuw",
    "!/cb.php?sub$script,third-party",
    "!@@/cb.php?sub",
    "!###ADSLOT_SKYSCRAPER",
    "! *** easylist:easylist/easylist_whitelist_general_hide.txt ***",
]

HTML_RULES = [
    "###ADSLOT_SKYSCRAPER",
    "@@###ADSLOT_SKYSCRAPER",
    "##.adsBox",
    "eee.se#@##adspace_top",
    "domain1.com,domain2.com#@##adwrapper",
    "edgesuitedomain.net#@##ad-unit",
    "mydomain.com#@#.ad-unit",
    '##a[href^="http://affiliate.sometracker.com/"]',
]


@pytest.mark.parametrize("text", COMMENT_RULES)
def test_is_comment(text):
    rule = AdblockRule(text)
    assert rule.is_comment
    assert not rule.is_html_rule
    assert not rule.is_exception
    assert rule.options == {}
    assert not rule.regex


@pytest.mark.parametrize("text", HTML_RULES)
def test_is_html_rule(text):
    rule = AdblockRule(text)
    assert rule.is_html_rule
    assert not rule.is_comment
