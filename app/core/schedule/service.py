from app.core.schedule.utils import prepare_shift_slots, build_schedule
from app.core.schedule.allocator.allocator.engine.generators import TalentByRole
from app.core.utils.exceptions import ValidationError, DatabaseError, NotFoundError, AppBaseException
import asyncpg


class ScheduleEngine:

    def __init__(self, asyncpg, session, start_date):
        self.asyncpg = asyncpg
        self.session = session
        self.start_date = start_date

    
    def final_schedule(self):
        try:
            talent_roles = TalentByRole.group_talents(self.talents)
            shifts = prepare_shift_slots(self.session)
            schedule = build_schedule(self.talents, shifts, talent_roles)
            return schedule
        
        except ValueError as e:
            raise ValidationError(f"Invalid input: {e}")
        except asyncpg.PostgresError as e:
            raise DatabaseError("A database error has occurred during schedule generation. Please try again")
        except KeyError as e:
            raise NotFoundError(f"Missing key during schedule generation: {e}")
        except Exception as e:
            raise AppBaseException(f"Internal Server error during schedule generation: {e}")



    

