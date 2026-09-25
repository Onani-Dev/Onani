# -*- coding: utf-8 -*-
"""Regression tests for the scan start/stop race fixes (audit be-H1/H2/M2).

These exercise the conditional-update (compare-and-swap) logic directly,
since reproducing genuine thread-level concurrency in a single-process test
client isn't practical — the CAS is what makes the outcome deterministic
regardless of interleaving, so testing it directly is the meaningful check.
"""
import tempfile
from unittest.mock import MagicMock, patch

import pytest


class TestDuplicateScanRace:
    """be-H2: two POSTs must not both start a scan."""

    def test_second_post_is_rejected_once_first_has_claimed_the_row(self, admin_client, app):
        from onani.models import ExternalLibrary
        from onani import db as _db

        client, admin = admin_client
        with tempfile.TemporaryDirectory() as tmpdir:
            with app.app_context():
                lib = ExternalLibrary(name="RaceLib", path=tmpdir, owner_id=admin.id)
                _db.session.add(lib)
                _db.session.commit()
                lib_id = lib.id

            # Once the first POST has claimed the row, its task looks
            # genuinely active — this is what a real concurrent second POST
            # (arriving just after the first commits) would observe.
            mock_result = MagicMock()
            mock_result.state = "STARTED"
            with patch("onani.routes.api.v1.libraries.scan_library.apply_async"), \
                 patch("onani.routes.api.v1.libraries.scan_library.AsyncResult", return_value=mock_result):
                first = client.post(f"/api/v1/libraries/{lib_id}/scan")
                second = client.post(f"/api/v1/libraries/{lib_id}/scan")

            assert first.status_code == 202
            assert second.status_code == 409

    def test_concurrent_updates_only_one_cas_wins(self, app, make_user):
        """Simulate two racing requests by issuing the same conditional UPDATE
        twice against a row that was idle when both "read" it — only the
        first UPDATE should actually flip the row."""
        from sqlalchemy import text
        from onani.models import ExternalLibrary
        from onani import db as _db

        with app.app_context():
            user = make_user(username="race_cas_user", password="testpassword")
            lib = ExternalLibrary(name="CasLib", path="/tmp/cas", owner_id=user.id)
            _db.session.add(lib)
            _db.session.commit()
            lib_id = lib.id

            old_task_id = lib.last_scan_task_id  # None — both requests read this
            sql = text(
                "UPDATE external_libraries "
                "SET last_scan_status = 'SCANNING', last_scan_task_id = :tid "
                "WHERE id = :id AND (last_scan_task_id = :old_tid OR "
                "(last_scan_task_id IS NULL AND :old_tid IS NULL))"
            )

            result_a = _db.session.execute(sql, {"tid": "task-a", "id": lib_id, "old_tid": old_task_id})
            _db.session.commit()
            result_b = _db.session.execute(sql, {"tid": "task-b", "id": lib_id, "old_tid": old_task_id})
            _db.session.commit()

            assert result_a.rowcount == 1
            assert result_b.rowcount == 0

            fresh = ExternalLibrary.query.get(lib_id)
            assert fresh.last_scan_task_id == "task-a"


class TestStopScanRace:
    """be-H1: a stopped scan must not resurrect itself via a straggling commit."""

    def test_stop_does_not_clobber_a_newer_scan(self, app, make_user):
        """If a DELETE reads task A but a new scan (task B) has already
        replaced it by the time DELETE writes, the row must still show B."""
        from onani.models import ExternalLibrary
        from onani import db as _db

        with app.app_context():
            user = make_user(username="race_stop_user", password="testpassword")
            lib = ExternalLibrary(
                name="StopRaceLib", path="/tmp/stopl", owner_id=user.id,
                last_scan_status="SCANNING", last_scan_task_id="task-a",
            )
            _db.session.add(lib)
            _db.session.commit()
            lib_id = lib.id

            # DELETE read task-a, but before it writes, a new scan starts
            # and reclaims the row as task-b.
            lib.last_scan_task_id = "task-b"
            _db.session.commit()

            from sqlalchemy import text
            _db.session.execute(
                text(
                    "UPDATE external_libraries "
                    "SET last_scan_status = 'IDLE', last_scan_task_id = NULL "
                    "WHERE id = :id AND (last_scan_task_id = :tid OR last_scan_task_id IS NULL)"
                ),
                {"id": lib_id, "tid": "task-a"},
            )
            _db.session.commit()

            fresh = ExternalLibrary.query.get(lib_id)
            assert fresh.last_scan_task_id == "task-b"
            assert fresh.last_scan_status == "SCANNING"

    def test_task_finalize_is_a_noop_after_stop(self, app, make_user):
        """A scan task's own status commits must not resurrect SCANNING once
        the row has been stopped (last_scan_task_id cleared/reassigned)."""
        from onani.models import ExternalLibrary
        from onani import db as _db
        from onani.tasks.library import _fenced_status_update

        with app.app_context():
            user = make_user(username="race_finalize_user", password="testpassword")
            lib = ExternalLibrary(
                name="FinalizeRaceLib", path="/tmp/finrace", owner_id=user.id,
                last_scan_status="SCANNING", last_scan_task_id="task-a",
            )
            _db.session.add(lib)
            _db.session.commit()
            lib_id = lib.id

            # Simulate a stop: DELETE clears the row.
            lib.last_scan_status = "IDLE"
            lib.last_scan_task_id = None
            _db.session.commit()

            # task-a's straggling finalize commit tries to write SUCCESS —
            # should be rejected since it no longer owns the row.
            applied = _fenced_status_update(lib_id, "task-a", last_scan_status="SUCCESS")
            assert applied is False

            fresh = ExternalLibrary.query.get(lib_id)
            assert fresh.last_scan_status == "IDLE"

    def test_task_finalize_applies_when_still_owner(self, app, make_user):
        from onani.models import ExternalLibrary
        from onani import db as _db
        from onani.tasks.library import _fenced_status_update

        with app.app_context():
            user = make_user(username="race_owner_user", password="testpassword")
            lib = ExternalLibrary(
                name="OwnerLib", path="/tmp/owner", owner_id=user.id,
                last_scan_status="SCANNING", last_scan_task_id="task-a",
            )
            _db.session.add(lib)
            _db.session.commit()
            lib_id = lib.id

            applied = _fenced_status_update(lib_id, "task-a", last_scan_status="SUCCESS")
            assert applied is True

            fresh = ExternalLibrary.query.get(lib_id)
            assert fresh.last_scan_status == "SUCCESS"


class TestStaleScanReclaim:
    """A crashed worker's stale SCANNING row can still be reclaimed."""

    def test_post_reclaims_stale_scanning_row(self, admin_client, app):
        from onani.models import ExternalLibrary
        from onani import db as _db

        client, admin = admin_client
        with tempfile.TemporaryDirectory() as tmpdir:
            with app.app_context():
                lib = ExternalLibrary(
                    name="StaleLib", path=tmpdir, owner_id=admin.id,
                    last_scan_status="SCANNING", last_scan_task_id="crashed-task",
                )
                _db.session.add(lib)
                _db.session.commit()
                lib_id = lib.id

            mock_result = MagicMock()
            mock_result.state = "PENDING"  # unknown to broker == crashed
            with patch("onani.routes.api.v1.libraries.scan_library.AsyncResult", return_value=mock_result), \
                 patch("onani.routes.api.v1.libraries.scan_library.apply_async"):
                resp = client.post(f"/api/v1/libraries/{lib_id}/scan")

            assert resp.status_code == 202
            with app.app_context():
                fresh = ExternalLibrary.query.get(lib_id)
                assert fresh.last_scan_task_id != "crashed-task"
