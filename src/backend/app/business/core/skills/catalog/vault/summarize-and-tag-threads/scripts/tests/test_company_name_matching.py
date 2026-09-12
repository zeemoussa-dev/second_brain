"""A company named with its legal form still finds its hub -- and the PARENT
never absorbs a name that belongs to an affiliate.

A reader quoting a contract wrote "Mubadala Health LLC": it matched no hub,
while the same reader's plain "Mubadala" matched the parent. The affiliate's
own thread was then filed under the parent (operator, 2026-09-12: "we have
that issue with Companies that are Multi Word and Have the Parent company
Share the first name").
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def hub(vault: Path, root: str, name: str, *, parent: str | None = None, aliases=()) -> None:
    base = vault / "Work" / root
    folder = (base / parent / "Affiliates" / name) if parent else (base / name)
    folder.mkdir(parents=True)
    alias_line = ("aliases: [" + ", ".join(f'"{a}"' for a in aliases) + "]\n") if aliases else ""
    (folder / f"{name}.md").write_text(
        f'---\ntype: "{"Customer" if root == "Customers" else "Partner"}"\n'
        f'name: "{name}"\n{alias_line}---\n', encoding="utf-8")


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(tmp_path / "config"))
    hub(tmp_path, "Customers", "Mubadala")
    hub(tmp_path, "Customers", "Mubadala Health", parent="Mubadala")
    hub(tmp_path, "Customers", "TAQA")
    hub(tmp_path, "Customers", "TAQA Distribution", parent="TAQA")
    return tmp_path


def test_a_legal_form_is_not_part_of_the_name():
    import apply_thread_extract as a
    assert a.normalise_company("Mubadala Health LLC") == "mubadala health"
    assert a.normalise_company("Khazna Data Center Limited") == "khazna data center"
    assert a.normalise_company("BAYANAT G I Q - P.S.C - O.P.C") == "bayanat g i q"
    assert a.normalise_company("e&") == "e&", "a real name is never emptied"


def test_an_affiliates_legal_name_resolves_to_the_affiliate(vault):
    import apply_thread_extract as a
    index = a._company_index(vault)
    assert index[a.normalise_company("Mubadala Health LLC")] == "customer/mubadala-health"
    assert index["mubadala health"] == "customer/mubadala-health"


def test_the_parent_keeps_its_own_name(vault):
    """Stripping a legal form must never fold an affiliate into its parent."""
    import apply_thread_extract as a
    index = a._company_index(vault)
    assert index["mubadala"] == "customer/mubadala"
    assert index["taqa"] == "customer/taqa"
    assert index["taqa distribution"] == "customer/taqa-distribution"


def test_a_legal_name_is_no_longer_reported_as_unknown(vault):
    import apply_thread_extract as a
    assert a.record_unknown_companies(vault, ["Mubadala Health LLC"], "conv-1", "T") == []
    assert a.record_unknown_companies(vault, ["Nowhere Holdings"], "conv-1", "T") == ["Nowhere Holdings"]
