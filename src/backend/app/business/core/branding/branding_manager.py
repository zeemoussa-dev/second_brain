"""The sole gateway onto this install's branding -- the name it calls
itself and its logo (operator, 2026-10-21: "the Option to Change the
Name from The Second Brain to Something else and add a Logo").

**The product's own name is the default, not a stored value.** A fresh
install has no branding record and renders "Second Brain"; that is a
fallback in one place here, never a row written at setup. The
difference matters when the product is renamed: an install that never
chose a name follows the product, and one that chose "Second Brain"
deliberately keeps it.

**Configuration, not a catalogue.** One record, no id, no list, no
export -- an install's own identity is the last thing that should
travel in a bundle to another machine.

**The logo is validated on the way in, by its bytes as well as its
name.** A file called `logo.png` carrying something else is the whole
point of checking: this file is served back to every browser that
loads the app, including before anyone has signed in.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.data_access import branding as branding_data

DEFAULT_APP_NAME = "Second Brain"
MAX_LOGO_BYTES = 1024 * 1024

# Extension -> the magic bytes a real file of that type starts with.
# SVG is text and has no single signature, so it is checked separately.
_IMAGE_SIGNATURES: dict[str, tuple[bytes, ...]] = {
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".gif": (b"GIF87a", b"GIF89a"),
    ".webp": (b"RIFF",),
}
_CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}


class BrandingError(Exception):
    """A refusal the operator should read verbatim."""


#: Theme modes an install may choose. No "system" option: branding is one look
#: for the whole install (operator's own choice, 2026-10-24), and "whatever
#: each visitor's OS happens to say" is the opposite of that.
THEME_MODES = ("dark", "light")
DEFAULT_THEME_MODE = "dark"

#: The three fonts the picker offers. The id is what is stored and what the
#: frontend puts in `data-font`; the stylesheet owns the actual stacks, so a
#: font is added by adding a file, a rule and one entry here.
FONT_CHOICES = ("inter", "plex", "source")
DEFAULT_FONT = "inter"

#: Shipped copper. The default lives here as well as in CSS because the API
#: answers it to callers that never load the stylesheet.
DEFAULT_ACCENT = "#c58b5f"


@dataclass(frozen=True)
class Branding:
    app_name: str
    has_logo: bool
    is_customised: bool
    theme_mode: str
    font: str
    accent_color: str


class BrandingManager:
    def get(self) -> Branding:
        """Never raises for an absent or unreadable record: branding is
        rendered on the sign-in screen, before anything else works, and
        an install whose branding file was hand-edited into invalid JSON
        must still be reachable to fix it. A broken record falls back to
        the product name, which is visibly wrong and therefore
        self-reporting."""
        name = DEFAULT_APP_NAME
        customised = False
        record = self._record()
        stored = str(record.get("app_name") or "").strip()
        if stored:
            name = stored
            customised = True
        return Branding(
            app_name=name,
            has_logo=branding_data.find_logo() is not None,
            is_customised=customised,
            # Each falls back on its own: a record written before the theme
            # existed, or hand-edited with one key removed, still describes a
            # complete, renderable theme rather than a half of one.
            theme_mode=self._one_of(record.get("theme_mode"), THEME_MODES, DEFAULT_THEME_MODE),
            font=self._one_of(record.get("font"), FONT_CHOICES, DEFAULT_FONT),
            accent_color=self._accent_or_default(record.get("accent_color")),
        )

    def set_app_name(self, app_name: str) -> Branding:
        """An empty name resets to the product's own rather than being
        refused -- "clear it" is the only way back, and a form whose
        empty state is an error has no reset."""
        cleaned = app_name.strip()
        if len(cleaned) > 60:
            raise BrandingError(
                f"That name is {len(cleaned)} characters; it has to fit the sidebar and the "
                "browser tab, so 60 is the limit. Nothing was changed."
            )
        self._merge({"app_name": cleaned})
        return self.get()

    def set_theme(
        self,
        theme_mode: str | None = None,
        font: str | None = None,
        accent_color: str | None = None,
    ) -> Branding:
        """Each part is optional, and only what is passed is written: the
        Branding page saves one control at a time, and a PUT carrying three
        fields would let a stale form overwrite a colour somebody else just
        changed with whatever it last read."""
        patch: dict[str, str] = {}
        if theme_mode is not None:
            if theme_mode not in THEME_MODES:
                raise BrandingError(
                    f"{theme_mode!r} is not a theme. Choose one of: {', '.join(THEME_MODES)}. "
                    "Nothing was changed."
                )
            patch["theme_mode"] = theme_mode
        if font is not None:
            if font not in FONT_CHOICES:
                raise BrandingError(
                    f"{font!r} is not one of this install's fonts. Choose one of: "
                    f"{', '.join(FONT_CHOICES)}. Nothing was changed."
                )
            patch["font"] = font
        if accent_color is not None:
            patch["accent_color"] = self._valid_accent(accent_color)
        if patch:
            self._merge(patch)
        return self.get()

    @staticmethod
    def _record() -> dict:
        """The stored record, or an empty one. Never raises for an absent or
        unreadable file: branding is rendered on the sign-in screen, before
        anything else works, and an install whose branding file was
        hand-edited into invalid JSON must still be reachable to fix it."""
        if not branding_data.branding_exists():
            return {}
        try:
            record = branding_data.read_branding_json()
        except (ValueError, OSError):
            return {}
        return record if isinstance(record, dict) else {}

    def _merge(self, patch: dict) -> None:
        """Writes `patch` over what is stored. A plain write would drop every
        other key -- renaming the install would have reset its theme, and
        picking a font would have reset its name."""
        branding_data.write_branding_json({**self._record(), **patch})

    @staticmethod
    def _one_of(value: object, allowed: tuple[str, ...], fallback: str) -> str:
        text = str(value or "").strip().lower()
        return text if text in allowed else fallback

    @classmethod
    def _accent_or_default(cls, value: object) -> str:
        try:
            return cls._valid_accent(str(value or ""))
        except BrandingError:
            return DEFAULT_ACCENT

    @staticmethod
    def _valid_accent(value: str) -> str:
        """`#rgb` or `#rrggbb`, normalised to six lowercase digits.

        Narrow on purpose. This string is written into a CSS custom property on
        the document element, so anything accepted here is injected into the
        page's styles -- `red; background: url(...)` would be a stylesheet
        injection, not a colour."""
        cleaned = value.strip().lower()
        if len(cleaned) == 4 and cleaned.startswith("#"):
            cleaned = "#" + "".join(character * 2 for character in cleaned[1:])
        valid = (
            len(cleaned) == 7
            and cleaned.startswith("#")
            and all(character in "0123456789abcdef" for character in cleaned[1:])
        )
        if not valid:
            raise BrandingError(
                f"{value!r} is not a colour. Give a hex value like #c58b5f. Nothing was changed."
            )
        return cleaned

    def set_logo(self, filename: str, content: bytes) -> Branding:
        suffix = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
        if suffix not in _CONTENT_TYPES:
            raise BrandingError(
                f"{filename!r} is not an image this app can serve. Use one of: "
                f"{', '.join(sorted(_CONTENT_TYPES))}. Nothing was changed."
            )
        if not content:
            raise BrandingError("That file is empty; nothing was changed.")
        if len(content) > MAX_LOGO_BYTES:
            raise BrandingError(
                f"That file is {len(content) // 1024} KB and the limit is "
                f"{MAX_LOGO_BYTES // 1024} KB -- it is a logo, not an illustration. "
                "Nothing was changed."
            )
        self._refuse_if_not_really(suffix, content, filename)
        branding_data.write_logo(suffix, content)
        return self.get()

    def clear_logo(self) -> Branding:
        branding_data.delete_logo()
        return self.get()

    def logo_file(self) -> tuple[str, str] | None:
        """`(path, content_type)` for the route that serves it, or None.
        The content type comes from the extension on disk rather than
        from anything a caller sent, so a mislabelled upload cannot
        change what this says the bytes are."""
        path = branding_data.find_logo()
        if path is None:
            return None
        return str(path), _CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")

    @staticmethod
    def _refuse_if_not_really(suffix: str, content: bytes, filename: str) -> None:
        """Checks the bytes, not just the name. This file is served to
        every browser that loads the app, signed in or not, so an
        upload called `logo.png` that is actually something else is the
        case worth refusing rather than the one worth trusting.

        SVG has no magic number -- it is XML -- so it is checked for
        actually being XML, and for not carrying a script. An SVG is
        rendered by the browser as a document, which makes a scripted
        one an injection into every page of the app.
        """
        if suffix == ".svg":
            head = content[:4096].lstrip().lower()
            if not (head.startswith(b"<?xml") or head.startswith(b"<svg")):
                raise BrandingError(
                    f"{filename!r} is named .svg but does not start like an SVG. "
                    "Nothing was changed."
                )
            lowered = content.lower()
            if b"<script" in lowered or b"javascript:" in lowered:
                raise BrandingError(
                    "That SVG contains a script. An SVG logo is rendered as a document on "
                    "every page of this app, so a scripted one is refused. Nothing was "
                    "changed."
                )
            return
        signatures = _IMAGE_SIGNATURES.get(suffix, ())
        if signatures and not content.startswith(signatures):
            raise BrandingError(
                f"{filename!r} is named {suffix} but its contents are not a {suffix[1:].upper()} "
                "file. Nothing was changed."
            )
