# _templates

Rendered by `_scripts/sitegen.py`. These files are the SINGLE copy of every
shared element. They are written by `sitegen.py extract` from the constants in
that script, so edit the script, not these files.

A change here rebuilds all pages: `sitegen.py build`. Verify with
`sitegen.py build --check`, which must report 0 drift before any commit that
is meant to be a no-op.
