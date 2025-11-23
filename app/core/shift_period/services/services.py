from sqlalchemy.orm import Session
from datetime import time
from app.core.utils.crud import CRUDBase
from app.core.shift_period.schema import ShiftPeriodIn,  ShiftPeriodUpdate, ShiftOut
from app.database.models import ShiftPeriod
from app.core.shift_period.services.validators import ShiftPeriodTimeFrame, validate_shift_period, validate_shift_period_update, validate_shift_period_delete, period_exists
from app.core.shift_period.utils import search_filters



class ShiftPeriodService(CRUDBase[ShiftPeriod, ShiftPeriodIn, ShiftPeriodUpdate]):

    def __init__(self):
        super().__init__(ShiftPeriod)

    def create_shift_period(self, db:Session, data: ShiftPeriodIn):
        
        shift_period = db.query(ShiftPeriod).filter(ShiftPeriod.shift_name == data.shift_name).first()
        ShiftPeriodTimeFrame().validate_shift_period(data=data)
        validate_shift_period(data=data, period=shift_period)
        created_shift_period = self.create(db=db, obj_in=data)
       
        return ShiftOut.model_validate(created_shift_period)

    def update_shift_period(self, db: Session, data: ShiftPeriodUpdate, period_id: int):
        shift_period = db.query(ShiftPeriod).filter(ShiftPeriod.id == period_id).first()
        validate_shift_period_update(data=data, period=shift_period)
        updated_shift = self.update(db=db, db_obj=shift_period, obj_in=data)
        return ShiftOut.model_validate(updated_shift)

    def delete_shift_period(self, db: Session, period_id: int):
        shift_period = db.query(ShiftPeriod).filter(ShiftPeriod.id == period_id).first()
        validate_shift_period_delete(shift_period)
        self.delete(db=db, id=period_id)

def get_period(db: Session, id: int):
    period = db.query(ShiftPeriod).filter(ShiftPeriod.id == id).first()
    period_exists(period)
    return ShiftOut.model_validate(period) 

def get_all_periods(db: Session,
                    shift_name: str | None = None,
                   start_time: time | None = None,
                   end_time: time | None = None):
    query = db.query(ShiftPeriod)
    templates = search_filters(query=query, shift_name=shift_name, start_time=start_time, end_time=end_time)
    period_exists(query)
    return [ShiftOut.model_validate(template) for template in templates]

        
