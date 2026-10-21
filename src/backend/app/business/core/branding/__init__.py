"""This install's own name and logo (operator, 2026-10-21).

Configuration, not a catalogue: one record, no id, no list, and
deliberately no export -- an install's identity is the last thing that
should travel in a bundle to another machine.

Readable without signing in, because the sign-in screen itself renders
the name and the logo. Writing needs an Admin. That asymmetry is the
whole security model here and is enforced on the routes, not in this
package.

`BrandingManager` is the sole gateway; raw I/O is
`app/data_access/branding.py`.
"""
