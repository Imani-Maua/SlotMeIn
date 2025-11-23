from fastapi import HTTPException, status
from datetime import time
from app.core.shift_period.schema import ShiftPeriodIn, ShiftPeriodUpdate
from app.database.models import ShiftPeriod
from app.core.utils.enums import Shifts

def validate_shift_period(data: ShiftPeriodIn, period:ShiftPeriod):
        if period and period.shift_name == data.shift_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail="Shift period already exists")

        if data.start_time > data.end_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail="Start time cannot be after end time")
        
        if data.start_time == data.end_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail="Start time cannot be the same as end time")

def validate_shift_period_update(data: ShiftPeriodUpdate, period: ShiftPeriod):
    has_start_time = bool(data.start_time)
    has_end_time = bool(data.end_time)


    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Period not found")
    if not has_start_time and not has_end_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Must enter at least one field")
    
    if has_end_time and not has_start_time and data.end_time < period.start_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="End time cannot be before start time")
    
    if has_start_time and not has_end_time and data.start_time > period.end_time:
    
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Start time cannot be after end time")
    
    if has_start_time and has_end_time and data.start_time > data.end_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Start time cannot be after end time")


def validate_shift_period_delete(period: ShiftPeriod):
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift period not found")



class ShiftPeriodTimeFrame:

    SHIFT_TIMEFRAME = {
            Shifts.AM.value: {"start_time": time(6,0), 
                                  "end_time": time(16,0)},
            Shifts.PM.value: {"start_time": time(15, 00), 
                                  "end_time": time(23, 59)},
            Shifts.LOUNGE.value:{"start_time": time(11,0), 
                                      "end_time": time(23, 59)}
                                      }
    @classmethod
    def expected_timeframe(cls, data: ShiftPeriodIn) -> dict:
        shift_name = data.shift_name
        return cls.SHIFT_TIMEFRAME.get(shift_name)
    
    @classmethod
    def validate_shift_period(cls, data: ShiftPeriodIn):

        shift_name = data.shift_name
        start_time = data.start_time
        end_time = data.end_time

        timeframe: dict = cls.expected_timeframe(data)
        if timeframe is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail=f"Unknown shift type: {shift_name}")
        
        if start_time != timeframe["start_time"] or end_time != timeframe["end_time"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"{shift_name} must be from {timeframe['start_time']} and {timeframe['end_time']}")
        

def period_exists(period: ShiftPeriod):
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift template not found")
        
        
        

        
        