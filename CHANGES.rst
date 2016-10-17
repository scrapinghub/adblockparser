Changes
=======

0.7 (2016-10-17)
----------------

* Fixed parsing issue with recent easylist.txt;
* fixed a link to easylist (thanks https://github.com/limonte).

0.6 (2016-09-10)
----------------

* Added support for regex rules (thanks https://github.com/mlyko).

0.5 (2016-03-04)
----------------

* Fixed an issue with blank lines in filter files
  (thanks https://github.com/skrypka);
* fixed an issue with applying rules with 'domain' option
  when domain doesn't have a dot (e.g. 'localhost');
* Python 2.6 and Python 3.2 support is dropped;
  adblockparser likely still work in these interpreters,
  but this is no longer checked by tests.

0.4 (2015-03-29)
----------------

* AdblockRule now caches the compiled regexes (thanks
  https://github.com/mozbugbox);
* Fixed an issue with "domain" option handling
  (thanks https://github.com/nbraem for the bug report and a test case);
* cleanups and test improvements.

0.3 (2014-07-11)
----------------

* Switch to setuptools;
* better ``__repr__`` for ``AdblockRule``;
* Python 3.4 support is confirmed;
* testing improvements.

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
