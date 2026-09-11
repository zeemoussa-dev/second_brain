"""Parallel Enrichment jobs all add to one review file. Without a lock, two
jobs updating it at once each read it, each add their names, and the later
rename silently drops the other's.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_names_from_concurrent_jobs_are_all_kept(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(tmp_path / "config"))
    (tmp_path / "Work" / "Customers").mkdir(parents=True)
    import apply_thread_extract as a

    names = [f"Company {index}" for index in range(40)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda name: a.record_unknown_companies(
            tmp_path, [name], f"conv-{name}", name), names))

    store = json.loads((tmp_path / "config" / "data" / "UnknownCompanies.json")
                       .read_text(encoding="utf-8"))
    assert sorted(store) == sorted(names)
    assert not (tmp_path / "config" / "data" / "UnknownCompanies.json.lock").exists()


def test_a_lock_left_by_a_crashed_job_is_broken(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(tmp_path / "config"))
    import os
    import apply_thread_extract as a
    target = tmp_path / "config" / "data" / "UnknownCompanies.json"
    target.parent.mkdir(parents=True)
    lock = target.with_suffix(".json.lock")
    lock.write_text("", encoding="utf-8")
    old = lock.stat().st_mtime - 3600
    os.utime(lock, (old, old))
    with a._exclusive(target, timeout=2):
        pass
    assert not lock.exists()
