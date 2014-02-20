Changes
=======

0.2 (2014-03-20)
----------------

This release provides much faster `AdblockRules.should_block()` method
for rules without options and rules with 'domain' option.

* better combined regex for option-less rules that makes re2 library
  always use DFA without falling back to NFA;
* an index for rules with domains;
* ``params`` method arguments are renamed to ``options`` for consistency.

0.1.1 (2014-03-11)
------------------

By default ``AdblockRules`` autodetects re2 library and uses
it if a compatible version is detected.

0.1 (2014-03-03)
----------------

Initial release.
