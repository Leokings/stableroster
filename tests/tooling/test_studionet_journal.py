"""Offline tests: fake client only, no wallet loading or network access."""

import copy
import json
from types import SimpleNamespace

import pytest

from tests.studionet_journal import StudioJournal


SUCCESS = {"status_name": "FINALIZED", "result_name": "AGREE",
           "consensus_data": {"leader_receipt": [{"execution_result": "SUCCESS"}]}}
FAILURE = {"status_name": "FINALIZED", "result_name": "AGREE",
           "consensus_data": {"leader_receipt": [{"execution_result": "ERROR",
                                                 "error": "[EXPECTED] already_exists"}]}}


class FakeClient:
    chain = SimpleNamespace(id=61999)
    provider = SimpleNamespace(url="https://studio.genlayer.com/api")

    def __init__(self, path):
        self.path = path
        self.broadcasts = 0
        self.waits = 0
        self.timeout = False
        self.uncertain = False
        self.receipt = copy.deepcopy(SUCCESS)

    def deploy_contract(self, **_):
        self.broadcasts += 1
        if self.uncertain:
            raise TimeoutError("test response lost after possible broadcast")
        return "0x" + "ab" * 32

    write_contract = deploy_contract

    def wait_for_transaction_receipt(self, transaction_hash, **_):
        self.waits += 1
        saved = json.loads(self.path.read_text())
        assert saved["steps"]["deploy"]["transaction_hash"] == transaction_hash
        assert saved["steps"]["deploy"]["status"] in ("SUBMITTED", "PENDING")
        if self.timeout:
            raise TimeoutError("test finality timeout")
        return self.receipt


@pytest.fixture
def setup(tmp_path):
    source = tmp_path / "contract.py"
    source.write_text("# public test source\n", encoding="utf-8")
    path = tmp_path / "journal.json"
    accounts = [SimpleNamespace(address="0x" + "12" * 20)]
    client = FakeClient(path)

    def journal(**overrides):
        return StudioJournal("example", source, accounts, client=client, path=path, **overrides)

    return source, path, accounts[0], client, journal


def test_hash_is_persisted_before_wait_and_finalized_step_is_not_resent(setup):
    _, path, owner, client, journal = setup
    with journal() as run:
        run.transaction("deploy", owner, [])
    with journal() as run:
        run.transaction("deploy", owner, [])
    assert client.broadcasts == client.waits == 1
    assert json.loads(path.read_text())["steps"]["deploy"]["status"] == "FINALIZED_SUCCESS"


def test_timeout_resumes_same_hash_and_same_parameters(setup):
    _, path, owner, client, journal = setup
    client.timeout = True
    with journal() as run:
        assert run.parameter("deadline", lambda: 123) == 123
        with pytest.raises(TimeoutError):
            run.transaction("deploy", owner, [])
    assert json.loads(path.read_text())["steps"]["deploy"]["status"] == "PENDING"
    client.timeout = False
    with journal() as run:
        assert run.parameter("deadline", lambda: 999) == 123
        run.transaction("deploy", owner, [])
    assert client.broadcasts == 1 and client.waits == 2


def test_changed_source_cannot_resume_old_proof(setup):
    source, _, owner, _, journal = setup
    with journal() as run:
        run.transaction("deploy", owner, [])
    source.write_text("# changed source\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="journal_binding_mismatch"):
        with journal():
            pass


def test_changed_arguments_cannot_reuse_a_receipt(setup):
    _, _, owner, client, journal = setup
    with journal() as run:
        run.transaction("deploy", owner, [])
    with journal() as run:
        with pytest.raises(RuntimeError, match="journal_request_mismatch"):
            run.transaction("deploy", owner, ["different"])
    assert client.broadcasts == 1


def test_uncertain_broadcast_is_never_automatically_resent(setup):
    _, _, owner, client, journal = setup
    client.uncertain = True
    with journal() as run:
        with pytest.raises(TimeoutError):
            run.transaction("deploy", owner, [])
    with journal() as run:
        with pytest.raises(RuntimeError, match="submission_uncertain"):
            run.transaction("deploy", owner, [])
    assert client.broadcasts == 1


@pytest.mark.parametrize("expected_error", [None, "already_exists"])
def test_finalized_error_is_not_mistaken_for_success(setup, expected_error):
    _, path, owner, client, journal = setup
    client.receipt = copy.deepcopy(FAILURE)
    for _ in range(2):
        with journal() as run:
            if expected_error is None:
                with pytest.raises(AssertionError, match="finalized_execution_failed"):
                    run.transaction("deploy", owner, [], expected_error=expected_error)
            else:
                run.transaction("deploy", owner, [], expected_error=expected_error)
    assert json.loads(path.read_text())["steps"]["deploy"]["status"] == "FINALIZED_ERROR"
    assert client.broadcasts == 1


def test_journal_lock_rejects_concurrent_runs(setup):
    _, _, _, _, journal = setup
    with journal():
        with pytest.raises(RuntimeError, match="journal_locked"):
            with journal():
                pass


def test_wrong_network_is_rejected_before_broadcast(setup):
    _, _, _, client, journal = setup
    client.provider = SimpleNamespace(url="http://127.0.0.1:4000/api")
    with pytest.raises(RuntimeError, match="wrong_live_network"):
        journal()
    assert client.broadcasts == 0


def test_finish_requires_matching_source_proof(setup):
    _, path, owner, _, journal = setup
    with journal() as run:
        run.transaction("deploy", owner, [])
        with pytest.raises(AssertionError):
            run.finish({"source_sha256": "wrong", "deployed_source_sha256": "wrong"}, {})
        digest = run.binding["source_sha256"]
        run.finish({"source_sha256": digest, "deployed_source_sha256": digest}, {"case": "example"})
    assert json.loads(path.read_text())["status"] == "VERIFIED"


def test_default_checkpoint_survives_gltest_artifact_cleanup(tmp_path):
    source = tmp_path / "repo" / "contracts" / "contract.py"
    source.parent.mkdir(parents=True)
    source.write_text("# public test source\n", encoding="utf-8")
    client = FakeClient(tmp_path / "unused.json")
    run = StudioJournal("example", source, [SimpleNamespace(address="0x" + "12" * 20)], client=client)
    assert run.path.parent.name == ".studionet-runs"
    assert ".artifacts" not in run.path.parts


def test_readback_is_saved_only_for_a_finalized_step(setup):
    _, path, owner, _, journal = setup
    with journal() as run:
        run.transaction("deploy", owner, [])
        run.readback("deploy", {"value": 17})
        run.readback("deploy", {"value": 18})
    assert json.loads(path.read_text())["steps"]["deploy"]["final_state_readback"] == {"value": 17}
    assert json.loads(path.read_text())["steps"]["deploy"]["resumed_readbacks"] == [{"value": 18}]


def test_rpc_timeouts_are_finite_preserve_explicit_values_and_install_once(monkeypatch):
    import requests
    from tests.studionet_support import install_rpc_timeouts
    observed = []

    def fake(session, method, url, **kwargs):
        observed.append(kwargs["timeout"])
        return "offline"

    monkeypatch.setattr(requests.sessions.Session, "request", fake)
    install_rpc_timeouts()
    installed = requests.sessions.Session.request
    install_rpc_timeouts()
    assert requests.sessions.Session.request is installed
    with requests.Session() as session:
        assert session.get("https://studio.genlayer.com/api") == "offline"
        session.get("https://studio.genlayer.com/api", timeout=None)
        session.get("https://studio.genlayer.com/api", timeout=2)
    assert observed == [(10, 45), (10, 45), 2]
