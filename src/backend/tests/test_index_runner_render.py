r"""The deployed per-Index runner must be parseable Python no matter what
the real DATA_PATH/VAULT_PATH look like.

On 2026-09-06 three live Index cron jobs (index-adnoc/masdar/taqa) had
each failed 12 runs in a row because their deployed script contained a
raw `Path('C:\Users\...')` -- `\U` reads as a truncated unicode escape,
so the script never even compiled. These tests pin the escaping.
"""
import ast

import pytest

from app.business.core.index.index_manager import IndexManager, IndexRunnerTemplateError
from app.data_access import indexes as indexes_data

_WINDOWS_DATA_PATH = r"C:\Users\someone\OneDrive - Org\myData\Brain\config"
_WINDOWS_VAULT_PATH = r"C:\Users\someone\OneDrive - Org\myData\Brain\second-brain"


class _Settings:
    def __init__(self, data_path: str, vault_path: str) -> None:
        self.second_brain_data_path = data_path
        self.vault_path = vault_path


def _render(monkeypatch, index_id: str, data_path: str, vault_path: str) -> str:
    monkeypatch.setattr(
        "app.business.core.index.index_manager.settings",
        _Settings(data_path, vault_path),
    )
    return IndexManager()._render_stub(index_id)


def test_a_windows_path_renders_a_script_that_actually_parses(monkeypatch) -> None:
    rendered = _render(monkeypatch, "adnoc", _WINDOWS_DATA_PATH, _WINDOWS_VAULT_PATH)

    ast.parse(rendered)


def test_the_baked_in_paths_survive_the_round_trip(monkeypatch) -> None:
    """Parseable is not enough -- the script must also still point at the
    real folders once Python has read the literals back."""
    rendered = _render(monkeypatch, "adnoc", _WINDOWS_DATA_PATH, _WINDOWS_VAULT_PATH)
    tree = ast.parse(rendered)

    baked: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        name = node.targets[0].id
        value = node.value
        if isinstance(value, ast.Constant):
            baked[name] = value.value
        elif isinstance(value, ast.Call) and value.args and isinstance(value.args[0], ast.Constant):
            baked[name] = value.args[0].value

    assert baked["INDEX_ID"] == "adnoc"
    assert baked["DATA_PATH"] == _WINDOWS_DATA_PATH
    assert baked["VAULT_PATH"] == _WINDOWS_VAULT_PATH


def test_a_quote_in_the_path_cannot_break_out_of_the_literal(monkeypatch) -> None:
    """repr() is what makes this safe; a naive f-string would not be."""
    rendered = _render(monkeypatch, "odd", r"C:\it's\a path", r"C:\vault")

    ast.parse(rendered)


def test_a_placeholder_nothing_substitutes_is_refused(monkeypatch) -> None:
    """The failure this guards: someone adds a placeholder to the template
    and forgets the substitution, so the deployed script raises NameError
    inside a cron worker where nobody reads the output."""
    monkeypatch.setattr(
        "app.business.core.index.index_manager.indexes_data.read_index_runner_template",
        lambda: "INDEX_ID = __INDEX_ID__\nPROFILE = __PROFILE_ID__\n",
    )
    monkeypatch.setattr(
        "app.business.core.index.index_manager.settings",
        _Settings(_WINDOWS_DATA_PATH, _WINDOWS_VAULT_PATH),
    )

    with pytest.raises(IndexRunnerTemplateError, match="__PROFILE_ID__"):
        IndexManager()._render_stub("odd")


def test_pythons_own_dunders_are_not_mistaken_for_placeholders(monkeypatch) -> None:
    """The real template uses `__file__`; treating that as an unsubstituted
    placeholder would refuse every legitimate render."""
    monkeypatch.setattr(
        "app.business.core.index.index_manager.indexes_data.read_index_runner_template",
        lambda: "from pathlib import Path\nHERE = Path(__file__).parent\nINDEX_ID = __INDEX_ID__\n",
    )
    monkeypatch.setattr(
        "app.business.core.index.index_manager.settings",
        _Settings(_WINDOWS_DATA_PATH, _WINDOWS_VAULT_PATH),
    )

    ast.parse(IndexManager()._render_stub("odd"))


def test_a_template_that_renders_unparseable_python_is_refused(monkeypatch) -> None:
    """The 2026-09-06 bug itself: substitute raw instead of via repr() and
    the result is a SyntaxError nobody sees until the cron job runs."""
    monkeypatch.setattr(
        "app.business.core.index.index_manager.indexes_data.read_index_runner_template",
        lambda: "INDEX_ID = __INDEX_ID__\nBROKEN = (\n",
    )
    monkeypatch.setattr(
        "app.business.core.index.index_manager.settings",
        _Settings(_WINDOWS_DATA_PATH, _WINDOWS_VAULT_PATH),
    )

    with pytest.raises(IndexRunnerTemplateError, match="not valid Python"):
        IndexManager()._render_stub("odd")


def test_the_shipped_template_is_valid_python_on_its_own() -> None:
    """Placeholders sit in literal positions, so the template itself must
    parse -- that is what makes it reviewable and lintable as real code."""
    ast.parse(indexes_data.read_index_runner_template())
