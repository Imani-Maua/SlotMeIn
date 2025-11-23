from fastapi import HTTPException, status
from app.core.shift_template.schema import TemplateIn, TemplateUpdate
from app.database.models import ShiftPeriod, ShiftTemplate




def validate_shift_template(data: TemplateIn, period: ShiftPeriod):
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


def validate_shift_template_update(data: TemplateUpdate, template: ShiftTemplate):
     
    has_start_time = bool(data.shift_start)
    has_end_time = bool(data.shift_end)

    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Template not found")
    
    if has_start_time and (data.shift_start < template.period.start_time or data.shift_start > template.period.end_time):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Enter a start time between {template.period.start_time} and {template.period.end_time}")
    
    if has_end_time and (data.shift_end < template.period.start_time or data.shift_end > template.period.end_time):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Enter an end time between {template.period.start_time} and {template.period.end_time}")

    if not has_start_time and not has_end_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Must enter at least one field")
    
    if has_end_time and not has_start_time and data.shift_end < template.shift_start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="End time cannot be before start time")
    
    if has_start_time and not has_end_time and data.shift_start > template.shift_end:
    
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Start time cannot be after end time")
    
    if has_start_time and has_end_time and data.shift_start > data.shift_end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Start time cannot be after end time")
    
    
def template_exists(template: ShiftTemplate):
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift template not found")



    




    
