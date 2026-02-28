from fastapi import HTTPException, status
from datetime import timedelta
from app.core.shift_template.schema import TemplateIn, TemplateUpdate
from app.database.models import ShiftPeriod, ShiftTemplate




def validate_shift_template(data: TemplateIn, period: ShiftPeriod):
    minimum_shift_length = timedelta(hours=4)
    if not period:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Period not found")
    if data.shift_start > data.shift_end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Start time cannot be after end time")
    if data.shift_start == data.shift_end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Start time cannot be the same as end time")
    if data.shift_start < period.start_time or data.shift_start > period.end_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Please select a template start time that falls within the shift period.")
    if data.shift_end > period.end_time or data.shift_end < period.start_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Please select a template end time that falls within the shift period.")
    # Convert times to total minutes for comparison
    start_mins = data.shift_start.hour * 60 + data.shift_start.minute
    end_mins = data.shift_end.hour * 60 + data.shift_end.minute
    
    if end_mins - start_mins < 240: # 4 hours = 240 minutes
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="A shift cannot be less than 4 hours")


def validate_shift_template_update(data: TemplateUpdate, template: ShiftTemplate):
     
    has_start_time = bool(data.shift_start)
    has_end_time = bool(data.shift_end)

    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Template not found")
    
    if has_start_time and (data.shift_start < template.period.start_time or data.shift_start > template.period.end_time):

        minimum_shift_length = timedelta(hours=4)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Enter a start time between {template.period.start_time} and {template.period.end_time}")
    
    if has_end_time and (data.shift_end < template.period.start_time or data.shift_end > template.period.end_time):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Enter an end time between {template.period.start_time} and {template.period.end_time}")

    if not has_start_time and not has_end_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Must enter at least one field")
    
    new_start = data.shift_start if has_start_time else template.shift_start
    new_end = data.shift_end if has_end_time else template.shift_end

    if new_start > new_end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Start time cannot be after end time")

    start_mins = new_start.hour * 60 + new_start.minute
    end_mins = new_end.hour * 60 + new_end.minute

    if end_mins - start_mins < 240:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="A shift cannot be less than 4 hours")
    
    
def template_exists(template: ShiftTemplate):
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift template not found")



    




    
