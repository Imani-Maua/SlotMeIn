from dataclasses import dataclass, field
from datetime import datetime
from app.core.utils.enums import TemplateRole

@dataclass
class shiftSpecification:
    start_time: datetime
    end_time: datetime
    shift_name: str
    role_name: TemplateRole
    role_count: int