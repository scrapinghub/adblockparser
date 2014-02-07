# -*- coding: utf-8 -*-
from __future__ import absolute_import
import re
from functools import partial


class AdblockRule(object):
    r"""
    AdBlock Plus rule.

    Check these links for the format details:

    * https://adblockplus.org/en/filter-cheatsheet
    * https://adblockplus.org/en/filters

    Instantiate AdblockRule with a rule line:

    >>> from adblock_parser import AdblockRule
    >>> rule = AdblockRule("@@||mydomain.no/artikler/$image,~third-party")

    Parsed data is available as rule attributes:

    >>> rule.is_comment
    False
    >>> rule.is_exception
    True
    >>> rule.is_html_rule
    False
    >>> rule.options
    ['image', '~third-party']
    >>> print(rule.regex)
    ^(?:[^:/?#]+:)?(?://(?:[^/?#]*\.)?)?mydomain\.no/artikler/

    To check if rule applies to an URL, use ``match_url`` method::

    >>> rule = AdblockRule("swf|")
    >>> rule.match_url("http://example.com/annoyingflash.swf")
    True
    >>> rule.match_url("http://example.com/swf/index.html")
    False

    Rules involving CSS selectors are detected but not supported well:

    >>> AdblockRule("domain.co.uk,domain2.com#@#.ad_description").is_html_rule
    True
    >>> AdblockRule("##.spot-ad").is_html_rule
    True
    """

    BINARY_OPTIONS = [
        "script",
        "image",
        "stylesheet",
        "object",
        "xmlhttprequest",
        "object-subrequest",
        "subdocument",
        "document",
        "elemhide",
        "other",
        "background",
        "xbl",
        "ping",
        "dtd",
        "media",
        "third-party",
        "match-case",
        "collapse",
        "donottrack",
    ]
    OPTIONS_SPLIT_PAT = ',(?=~?(?:%s))' % ('|'.join(BINARY_OPTIONS + ["domain"]))
    OPTIONS_SPLIT_RE = re.compile(OPTIONS_SPLIT_PAT)

    def __init__(self, rule_text):
        self.raw_rule_text = rule_text

        rule_text = rule_text.strip()
        self.is_comment = rule_text.startswith(('!', '[Adblock'))
        if self.is_comment:
            self.is_html_rule = self.is_exception = False
        else:
            self.is_html_rule = '##' in rule_text or '#@#' in rule_text  # or rule_text.startswith('#')
            self.is_exception = rule_text.startswith('@@')
            if self.is_exception:
                rule_text = rule_text[2:]

        if not self.is_comment and '$' in rule_text:
            rule_text, options_text = rule_text.split('$', 1)
            self.options = self.split_options(options_text)
        else:
            self.options = []

        self.rule_text = rule_text

        if self.is_comment or self.is_html_rule:
            # TODO: add support for HTML rules.
            # We should split the rule into URL and HTML parts,
            # convert URL part to a regex and parse the HTML part.
            self.regex = ''
        else:
            self.regex = self.rule_to_regex(rule_text)

    def match_url(self, url):
        if self.is_comment or self.is_html_rule:
            return False

        # print(self.rule_re.pattern)
        return bool(re.search(self.regex, url))

    @classmethod
    def split_options(cls, options_text):
        return cls.OPTIONS_SPLIT_RE.split(options_text)

    @classmethod
    def parse_domain_option(cls, text):
        if not text.startswith('domain='):
            raise ValueError("Domain option must starts with 'domain='")

        domains = text[len('domain='):]
        parts = domains.replace(',', '|').split('|')
        return [(not p.startswith('~'), p.lstrip('~')) for p in parts]


    @classmethod
    def rule_to_regex(cls, rule):
        """
        Convert AdBlock rule to a regular expression.
        """
        if not rule:
            raise ValueError("Invalid rule")
            # return rule

        # escape special regex characters
        rule = re.sub(r"([.$+?{}()\[\]\\])", r"\\\1", rule)

        # XXX: the resulting regex must use non-capturing groups (?:
        # for performance reasons; also, there is a limit on number
        # of capturing groups, no using them would prevent building
        # a single regex out of several rules.

        # Separator character ^ matches anything but a letter, a digit, or
        # one of the following: _ - . %. The end of the address is also
        # accepted as separator.
        rule = rule.replace("^", "(?:[^\w\d%_\-.%]|$)")

        # * symbol
        rule = rule.replace("*", ".*")

        # | in the end means the end of the address
        if rule[-1] == '|':
            rule = rule[:-1] + '$'

        # || in the beginning means beginning of the domain name
        if rule[:2] == '||':
            # XXX: it is better to use urlparse for such things,
            # but urlparse doesn't give us a single regex.
            # Regex is based on http://tools.ietf.org/html/rfc3986#appendix-B
            if len(rule) > 2:
                #          |            | complete part     |
                #          |  scheme    | of the domain     |
                rule = r"^(?:[^:/?#]+:)?(?://(?:[^/?#]*\.)?)?" + rule[2:]

        elif rule[0] == '|':
            # | in the beginning means start of the address
            rule = '^' + rule[1:]

        # other | symbols should be escaped
        # we have "|$" in our regexp - do not touch it
        rule = re.sub("(\|)[^$]", r"\|", rule)

        return rule


class AdblockRules(object):

    BINARY_RULES = ['']

    def __init__(self, rules, use_re2=False, max_mem=256*1024*1024):
        self.rules = [r for r in (AdblockRule(r) for r in rules)
                      if r.regex and not (r.is_comment or r.is_html_rule)]

        basic_rules = [r for r in self.rules if not r.options]
        advanced_rules = [r for r in self.rules if r.options]

        self.blacklist, self.whitelist = self._split_bw(basic_rules)
        self.blacklist2, self.whitelist2 = self._split_bw(advanced_rules)

        _combined = partial(combined_regex, use_re2=use_re2, max_mem=max_mem)

        self.blacklist_re = _combined([r.regex for r in self.blacklist])
        self.whitelist_re = _combined([r.regex for r in self.whitelist])

    def should_block(self, url):
        if self.whitelist_re and self.whitelist_re.search(url):
            return False

        # todo: advanced rules

        if self.blacklist_re and self.blacklist_re.search(url):
            return True

        return False

    @classmethod
    def _split_bw(cls, rules):
        blacklist = [r for r in rules if not r.is_exception]
        whitelist = [r for r in rules if r.is_exception]
        return blacklist, whitelist


def combined_regex(regexes, flags=re.IGNORECASE, use_re2=False, max_mem=None):
    """
    Return a compiled regex combined (using OR) from a list of ``regexes``.
    If there is nothing to combine, None is returned.

    re2 library (https://github.com/axiak/pyre2) often can match large
    regexes much faster (10x is not uncommon) than stdlib re module,
    but there are some gotchas:

    * at the moment of writing (Feb 2014) re2 from pypi doesn't work,
      it must be installed from the github repo;
    * in case of "DFA out of memory" errors use ``max_mem`` argument
      to increase the amount of memory re2 is allowed to use.
    """
    joined_regexes = "|".join(r for r in regexes if r)
    if not joined_regexes:
        return None

    regex_str = "(%s)" % joined_regexes
    if use_re2:
        import re2
        return re2.compile(regex_str, flags=flags, max_mem=max_mem)
    return re.compile(regex_str)
