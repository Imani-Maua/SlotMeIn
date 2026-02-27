from dataclasses import dataclass, field
from datetime import datetime
from app.core.utils.enums import Role

@dataclass
class shiftSpecification:
    template_id: int
    start_time: datetime
    end_time: datetime
    shift_name: str
    role_name: Role
    role_count: int