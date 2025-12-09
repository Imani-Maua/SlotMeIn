
from sqlalchemy.orm import Session
from app.core.schedule.shifts.service import ShiftSlotBuilder
from app.core.schedule.allocator.service import ScheduleBuilder
from app.core.schedule.talents.schema import talentAvailability
from app.core.schedule.shifts.schema import shiftSpecification
from app.core.schedule.allocator.engine.generators import TalentByRole




def prepare_shift_slots(db: Session) -> dict[int, shiftSpecification]:
    service = ShiftSlotBuilder(db=db)
    return service.build_week_slots()


def build_schedule(talent_objects: dict[int, talentAvailability],
                              assignable_shifts: dict[int, shiftSpecification],
                              talents_to_assign: dict[str, list[TalentByRole]]):
    
    service = ScheduleBuilder(talent_availability=talent_objects,
                                        assignable_shifts=assignable_shifts,
                                        talents_to_assign=talents_to_assign)
    return service.generate_schedule()












    



        
        
