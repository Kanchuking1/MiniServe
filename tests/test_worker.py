"""
Tests for worker log file: logger writes Processing/Done (and already-processed) to the log file.
"""

import importlib
import re

import pytest


def _reload_worker_with_log_file(log_path: str, monkeypatch: pytest.MonkeyPatch | None = None):
    """Set WORKER_LOG_FILE and reload worker.worker so the logger uses the temp file."""
    if monkeypatch is not None:
        monkeypatch.setenv("WORKER_LOG_FILE", log_path)
    else:
        import os
        os.environ["WORKER_LOG_FILE"] = log_path
    import worker.worker as wm
    importlib.reload(wm)
    return wm


@pytest.fixture
def worker_with_temp_log(tmp_path, monkeypatch):
    """Worker module configured to log to a temp file. Restores env after test."""
    log_file = tmp_path / "worker.log"
    wm = _reload_worker_with_log_file(str(log_file), monkeypatch)
    yield wm, log_file


class TestWorkerLogFile:
    def test_log_file_exists_after_processing_and_done(self, worker_with_temp_log):
        wm, log_file = worker_with_temp_log
        wm.logger.info("Processing job_id=%s", "test-job-1")
        wm.logger.info("Done job_id=%s", "test-job-1")
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "Processing job_id=test-job-1" in content
        assert "Done job_id=test-job-1" in content

    def test_log_file_contains_info_level_and_message(self, worker_with_temp_log):
        wm, log_file = worker_with_temp_log
        wm.logger.info("Processing job_id=%s", "job-xyz")
        content = log_file.read_text(encoding="utf-8")
        assert "[INFO]" in content
        assert "Processing job_id=job-xyz" in content
        # Optional: timestamp pattern (e.g. 2025-02-27 12:34:56,789)
        assert re.search(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}", content) is not None

    def test_log_file_already_processed_message(self, worker_with_temp_log):
        wm, log_file = worker_with_temp_log
        wm.logger.info("Job %s already processed", "already-done-id")
        content = log_file.read_text(encoding="utf-8")
        assert "Job already-done-id already processed" in content

    def test_log_file_in_subdirectory_created(self, tmp_path, monkeypatch):
        """When WORKER_LOG_FILE is logs/worker.log, the directory is created."""
        log_dir = tmp_path / "logs"
        log_file = log_dir / "worker.log"
        assert not log_dir.exists()
        wm = _reload_worker_with_log_file(str(log_file), monkeypatch)
        wm.logger.info("Processing job_id=%s", "subdir-job")
        assert log_dir.exists()
        assert log_file.exists()
        assert "Processing job_id=subdir-job" in log_file.read_text(encoding="utf-8")
