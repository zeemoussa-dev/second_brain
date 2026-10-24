"""The install's theme: mode, font and accent, stored with its branding
(operator, 2026-10-24: "I need to be able to Build a Theme as part of the
Branding, Light and Dark and the Option to choose the fonts from a Set of
Predefined ones ... and The Accent Color which will Affect the Side Panel").

The accent is the one with teeth. It is written into a CSS custom property on
the document element, so what the manager accepts is what gets injected into
every page's styles.
"""
from __future__ import annotations

import pytest

from app.business.core.branding.branding_manager import (
    DEFAULT_ACCENT,
    DEFAULT_FONT,
    DEFAULT_THEME_MODE,
    BrandingError,
    BrandingManager,
)
from app.config import settings


@pytest.fixture
def branding(monkeypatch, tmp_path) -> BrandingManager:
    """Its own data root per test: branding is ONE record for the install, so
    tests sharing a root would read each other's theme."""
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path)
    return BrandingManager()


def test_an_install_that_never_chose_has_a_complete_theme(branding) -> None:
    """Not a half-theme, and not None: every screen composes from these three
    values, so an absent record must still describe something renderable."""
    current = branding.get()

    assert current.theme_mode == DEFAULT_THEME_MODE
    assert current.font == DEFAULT_FONT
    assert current.accent_color == DEFAULT_ACCENT


def test_renaming_the_install_keeps_its_theme(branding) -> None:
    """The record is one JSON object. A plain write would drop every key it
    did not carry, so renaming would have silently reset the theme."""
    branding.set_theme(theme_mode="light", font="plex", accent_color="#336699")

    branding.set_app_name("Acme Knowledge")

    current = branding.get()
    assert current.app_name == "Acme Knowledge"
    assert (current.theme_mode, current.font, current.accent_color) == ("light", "plex", "#336699")


def test_choosing_a_font_keeps_the_name(branding) -> None:
    branding.set_app_name("Acme Knowledge")

    branding.set_theme(font="source")

    assert branding.get().app_name == "Acme Knowledge"
    assert branding.get().font == "source"


def test_each_part_is_saved_on_its_own(branding) -> None:
    """The page saves one control at a time; a body carrying all three would
    let a stale form put back what another admin just changed."""
    branding.set_theme(theme_mode="light")
    branding.set_theme(accent_color="#123456")

    current = branding.get()
    assert current.theme_mode == "light"
    assert current.accent_color == "#123456"
    assert current.font == DEFAULT_FONT


@pytest.mark.parametrize(
    "attempt",
    [
        "red; background: url(https://example.test/x)",
        "var(--color-danger)",
        "#12345",
        "rgb(1,2,3)",
        "javascript:alert(1)",
        "#gggggg",
    ],
)
def test_an_accent_that_is_not_a_hex_colour_is_refused(branding, attempt) -> None:
    """This string lands in a CSS custom property on <html>. Anything accepted
    here that is not a colour is a stylesheet injection."""
    with pytest.raises(BrandingError):
        branding.set_theme(accent_color=attempt)

    assert branding.get().accent_color == DEFAULT_ACCENT


def test_a_short_hex_is_accepted_and_normalised(branding) -> None:
    """#abc is a colour anyone may type; it is stored as the six digits the
    frontend's own luminance maths expects rather than refused."""
    branding.set_theme(accent_color="#ABC")

    assert branding.get().accent_color == "#aabbcc"


def test_a_theme_mode_that_does_not_exist_is_refused(branding) -> None:
    with pytest.raises(BrandingError):
        branding.set_theme(theme_mode="solarized")

    assert branding.get().theme_mode == DEFAULT_THEME_MODE


def test_a_font_that_is_not_shipped_is_refused(branding) -> None:
    """The stylesheet owns the three stacks. A stored id with no rule behind
    it would set `data-font` to something nothing matches, and the app would
    silently render the default while Settings claimed otherwise."""
    with pytest.raises(BrandingError):
        branding.set_theme(font="comic-sans")

    assert branding.get().font == DEFAULT_FONT


def test_a_record_from_before_the_theme_existed_still_renders(branding) -> None:
    """Every install upgrading into this has one: a branding.json with a name
    and nothing else."""
    from app.data_access import branding as branding_data

    branding_data.write_branding_json({"app_name": "Acme Knowledge"})

    current = branding.get()
    assert current.app_name == "Acme Knowledge"
    assert current.theme_mode == DEFAULT_THEME_MODE
    assert current.font == DEFAULT_FONT
    assert current.accent_color == DEFAULT_ACCENT


def test_a_hand_edited_record_falls_back_per_field(branding) -> None:
    """Not all-or-nothing: a file someone edited by hand, with one value
    mistyped, keeps every other value it got right."""
    from app.data_access import branding as branding_data

    branding_data.write_branding_json(
        {"app_name": "Acme", "theme_mode": "LIGHT", "font": "nonsense", "accent_color": "#336699"}
    )

    current = branding.get()
    assert current.theme_mode == "light", "a stored mode should not be case-sensitive"
    assert current.font == DEFAULT_FONT
    assert current.accent_color == "#336699"


def test_unreadable_branding_never_raises(branding, tmp_path) -> None:
    """Branding renders on the sign-in screen, before anything else works. An
    install whose record was hand-edited into invalid JSON has to stay
    reachable to fix it."""
    from app.data_access import branding as branding_data

    path = branding_data.branding_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json", encoding="utf-8")

    current = branding.get()
    assert current.theme_mode == DEFAULT_THEME_MODE
    assert current.accent_color == DEFAULT_ACCENT
