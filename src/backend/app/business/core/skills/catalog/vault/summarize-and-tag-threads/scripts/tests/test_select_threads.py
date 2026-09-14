"""The batch Enrichment is handed carries each Thread's id -- the only way the
agent is told to name a Thread, since a path it types from a title fails.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_each_selected_thread_carries_its_id(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(tmp_path / "config"))
    import select_threads as s
    folder = tmp_path / "Work" / "Threads" / "2026-06-08 Example"
    (folder / "messages").mkdir(parents=True)
    (folder / "2026-06-08 Example.md").write_text(
        '---\ntype: "Thread"\nid: "conv-7"\nlast_summarized_at: ""\n---\n', encoding="utf-8")
    (folder / "messages" / "m.md").write_text('---\ntype: "RawMessage"\n---\n', encoding="utf-8")
    selected = s.select(tmp_path, limit=5)["selected"]
    assert [t["thread_id"] for t in selected] == ["conv-7"]


def test_parallel_jobs_split_the_backlog_without_overlap(tmp_path, monkeypatch):
    """Five jobs asking for the oldest due Threads must not all get the same
    twenty: every Thread belongs to exactly one shard."""
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(tmp_path / "config"))
    import select_threads as s
    for index in range(40):
        folder = tmp_path / "Work" / "Threads" / f"2026-06-{index:02d} T"
        (folder / "messages").mkdir(parents=True)
        (folder / f"{folder.name}.md").write_text(
            f'---\ntype: "Thread"\nid: "conv-{index}"\nlast_summarized_at: ""\n---\n',
            encoding="utf-8")
        (folder / "messages" / "m.md").write_text('---\ntype: "RawMessage"\n---\n',
                                                  encoding="utf-8")
    shards = [{t["thread_id"] for t in s.select(tmp_path, limit=0, shard=k, shards=5)["selected"]}
              for k in range(5)]
    assert set().union(*shards) == {f"conv-{i}" for i in range(40)}
    assert sum(len(one) for one in shards) == 40, "no Thread is in two shards"
    assert all(shards), "every job gets work"
