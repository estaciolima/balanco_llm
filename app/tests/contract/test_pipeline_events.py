from extraction.events import PipelineEvent


def test_pipeline_event_has_expected_envelope():
    event = PipelineEvent(
        event_type="document.processing.started",
        document_id="doc-1",
        processing_run_id="run-1",
        pipeline_version="2026.06",
        payload={"started_at": "now"},
    ).as_dict()

    assert set(event) == {
        "event_id",
        "event_type",
        "occurred_at",
        "document_id",
        "processing_run_id",
        "pipeline_version",
        "actor",
        "payload",
    }
