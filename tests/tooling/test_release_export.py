"""Public proof export must not disclose validator provider configuration secrets."""

from scripts.export_studionet import summarize_step


def test_export_whitelists_model_metadata_and_preserves_real_vote_counts():
    raw = {
        "status_name": "FINALIZED", "result_name": "MAJORITY_AGREE",
        "consensus_data": {
            "votes": {"validator-a": "agree", "validator-b": "idle"},
            "leader_receipt": [{"execution_result": "SUCCESS", "node_config": {
                "address": "leader", "primary_model": {"provider": "example", "model": "model-a",
                "plugin_config": {"api_key": "DO_NOT_PUBLISH"}, "config": {"token": "DO_NOT_PUBLISH"}}}}],
            "validators": [{"vote": "idle", "node_config": {}}],
        },
    }
    entry = {"receipt": raw, "transaction_hash": "0xexample", "request": {"expected_error": None}}
    public = summarize_step("case", entry)
    assert public["votes"] == {"validator-a": "agree", "validator-b": "idle"}
    assert public["consensus_result"] == "MAJORITY_AGREE"
    assert public["participants"][0]["configured_models"]["primary_model"] == {"provider": "example", "model": "model-a"}
    assert "DO_NOT_PUBLISH" not in str(public) and "plugin_config" not in str(public)
