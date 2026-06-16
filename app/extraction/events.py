from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import uuid


@dataclass
class PipelineEvent:
    event_type: str
    document_id: str
    processing_run_id: str | None
    pipeline_version: str
    actor: str = "system"
    payload: dict = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def as_dict(self) -> dict:
        return asdict(self)
