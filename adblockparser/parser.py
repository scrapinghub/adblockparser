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

    >>> from adblockparser import AdblockRule
    >>> rule = AdblockRule("@@||mydomain.no/artikler/$~third-party")

    Parsed data is available as rule attributes:

    >>> rule.is_comment
    False
    >>> rule.is_exception
    True
    >>> rule.is_html_rule
    False
    >>> rule.options
    {'third-party': False}
    >>> print(rule.regex)
    ^(?:[^:/?#]+:)?(?://(?:[^/?#]*\.)?)?mydomain\.no/artikler/

    To check if rule applies to an URL, use ``match_url`` method::

    >>> rule = AdblockRule("swf|")
    >>> rule.match_url("http://example.com/annoyingflash.swf")
    True
    >>> rule.match_url("http://example.com/swf/index.html")
    False

    Rules involving CSS selectors are detected but not supported well
    (``match_url`` doesn't work for them):

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
            self.raw_options = self._split_options(options_text)
            self.options = dict(self._parse_option(opt) for opt in self.raw_options)
        else:
            self.raw_options = []
            self.options = {}
        self._options_keys = frozenset(self.options.keys()) - set(['match-case'])

        self.rule_text = rule_text

        if self.is_comment or self.is_html_rule:
            # TODO: add support for HTML rules.
            # We should split the rule into URL and HTML parts,
            # convert URL part to a regex and parse the HTML part.
            self.regex = ''
        else:
            self.regex = self.rule_to_regex(rule_text)

    def match_url(self, url, params=None):
        """
        Return if this rule matches the URL.

        What to do if rule is matched is up to developer. Most likely
        ``.is_exception`` attribute should be taken in account.
        """
        params = params or {}
        for optname in self.options:
            if optname == 'match-case':  # TODO
                continue

            if optname not in params:
                raise ValueError("Rule requires option %s" % optname)

            if optname == 'domain':
                if not self._domain_matches(params['domain']):
                    return False
                continue

            if params[optname] != self.options[optname]:
                return False

        return self._url_matches(url)

    def _domain_matches(self, domain):
        domain_rules = self.options['domain']
        for domain in _domain_variants(domain):
            if domain in domain_rules:
                return domain_rules[domain]
        return False

    def _url_matches(self, url):
        return bool(re.search(self.regex, url))

    def matching_supported(self, params=None):
        """
        Return whether this rule can return meaningful result,
        given the `params` dict. If some options are missing,
        then rule shouldn't be matched against, and this function
        returns False.

        >>> rule = AdblockRule("swf|")
        >>> rule.matching_supported({})
        True
        >>> rule = AdblockRule("swf|$third-party")
        >>> rule.matching_supported({})
        False
        >>> rule.matching_supported({'domain': 'example.com', 'third-party': False})
        True

        """
        if self.is_comment:
            return False

        if self.is_html_rule:  # HTML rules are not supported yet
            return False

        params = params or {}
        params_keys = set(params.keys())
        if not params_keys.issuperset(self._options_keys):
            # some of the required options are not given
            return False

        return True

    @classmethod
    def _split_options(cls, options_text):
        return cls.OPTIONS_SPLIT_RE.split(options_text)

    @classmethod
    def _parse_domain_option(cls, text):
        domains = text[len('domain='):]
        parts = domains.replace(',', '|').split('|')
        return dict(cls._parse_option_negation(p) for p in parts)

    @classmethod
    def _parse_option_negation(cls, text):
        return (text.lstrip('~'), not text.startswith('~'))

    @classmethod
    def _parse_option(cls, text):
        if text.startswith("domain="):
            return ("domain", cls._parse_domain_option(text))
        return cls._parse_option_negation(text)

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

    def __init__(self, rules, supported_options=None, skip_unsupported_rules=True,
                 use_re2=False, max_mem=256*1024*1024, rule_cls=AdblockRule):

        if supported_options is None:
            self.supported_options = rule_cls.BINARY_OPTIONS + ['domain']
        else:
            self.supported_options = supported_options

        _params = dict((opt, True) for opt in self.supported_options)
        self.rules = [
            r for r in (rule_cls(r) for r in rules)
            if r.regex and r.matching_supported(_params)
        ]

        self.skip_unsupported_rules = skip_unsupported_rules

        basic_rules = [r for r in self.rules if not r.options]
        advanced_rules = [r for r in self.rules if r.options]

        self.blacklist, self.whitelist = self._split_bw(basic_rules)
        self.blacklist2, self.whitelist2 = self._split_bw(advanced_rules)

        _combined = partial(_combined_regex, use_re2=use_re2, max_mem=max_mem)

        self.blacklist_re = _combined([r.regex for r in self.blacklist])
        self.whitelist_re = _combined([r.regex for r in self.whitelist])

    def should_block(self, url, params=None):
        if self.whitelist_re and self.whitelist_re.search(url):
            return False

        params = params or {}

        # TODO: group rules with similar options and match them in bigger steps

        whitelist2 = self.whitelist2
        blacklist2 = self.blacklist2
        if self.skip_unsupported_rules:
            whitelist2 = [rule for rule in self.whitelist2 if rule.matching_supported(params)]
            blacklist2 = [rule for rule in self.blacklist2 if rule.matching_supported(params)]

        for rule in whitelist2:
            if rule.match_url(url, params):
                return False

        if self.blacklist_re and self.blacklist_re.search(url):
            return True

        for rule in blacklist2:
            if rule.match_url(url, params):
                return True

        return False

    @classmethod
    def _split_bw(cls, rules):
        blacklist = [r for r in rules if not r.is_exception]
        whitelist = [r for r in rules if r.is_exception]
        return blacklist, whitelist


def _domain_variants(domain):
    """
    >>> list(_domain_variants("foo.bar.example.com"))
    ['foo.bar.example.com', 'bar.example.com', 'example.com']
    """
    parts = domain.split('.')
    for i in range(len(parts), 1, -1):
        yield ".".join(parts[-i:])


def _combined_regex(regexes, flags=re.IGNORECASE, use_re2=False, max_mem=None):
    """
    Return a compiled regex combined (using OR) from a list of ``regexes``.
    If there is nothing to combine, None is returned.

    re2 library (https://github.com/axiak/pyre2) often can match and compile
    large regexes much faster than stdlib re module (10x is not uncommon),
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
    return re.compile(regex_str, flags=flags)
