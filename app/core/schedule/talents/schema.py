from dataclasses import dataclass, field
from datetime import datetime, date, time
import enum


class Role(enum.Enum):
    leader = "leader"
    server = "server"
    bartender = "bartender"
    hostess = "hostess"
    runner = "runner"

@dataclass
class talentAvailability:
    talent_id: int
    constraint: bool
    role: Role
    shift_name: list[str]
    window: dict[date, list[tuple[time, time]]] 
    weeklyhours: float

@dataclass
class TalentRecord:
    talent_id: int
    role: str
    weeklyhours: float
    constraint_status: bool
    days: list[str]         # canonical names
    shifts: list[str]       # canonical shift names
