import pytest
from datetime import datetime, timedelta
from app.core.schedule.shifts.schema import shiftSpecification
from app.core.schedule.allocator.entities import assignment
from app.core.utils.enums import Role
from app.core.schedule.talents.schema import talentAvailability

@pytest.fixture
def make_shift():
    def _factory(start_time: datetime, end_time:datetime, role_count: int = 1):
        return shiftSpecification(
            template_id=1,
            start_time=start_time,
            end_time=end_time,
            shift_name="am",
            role_name= Role.SERVER,
            role_count=role_count
        )

    return _factory


@pytest.fixture
def make_assignment():
    def _factory(talent_id: int, shift_id: int, shift: shiftSpecification):
        return assignment(
            talent_id=talent_id,
            shift_id=shift_id,
            shift=shift
        )
    return _factory


@pytest.fixture
def make_context():
    def _factory(talent_id: int, shift: shiftSpecification, assignments: list[assignment], availability:talentAvailability = None):
        return {
            "talent_id": talent_id,
            "shift": shift,
            "availability": availability,
            "assignments": assignments
        }
    
    return _factory


@pytest.fixture
def make_availability():
    def _factory(talent_id:int, constraint: bool, role: Role, shift_name: str, window:dict, weeklyhours: float):
        return talentAvailability(
            talent_id=talent_id,
            constraint= constraint,
            role= role,
            shift_name=shift_name,
            window=window, 
            weeklyhours= weeklyhours
        )
    return _factory


@pytest.fixture
def start_of_week():
    today = datetime.now().date()
    return today - timedelta(days=(today.weekday() + 1) % 7)