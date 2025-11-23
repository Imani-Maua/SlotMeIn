from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta, date
from app.core.talents.schema import TalentIn, TalentUpdate
from app.database.models import Talent



def validate_talent_create(data: TalentIn, talent: Talent):
        if data.start_date > date.today() + timedelta(days=7):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                 detail="Start date too far in the future")
        
        if data.start_date < date.today():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Start date cannot be in the past")
        
        if talent:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                 detail="A talent with this email already exists")
        if not data.firstname.strip() or not data.lastname.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                 detail="Name cannot be empty")



def validate_talent_update(data: TalentUpdate, talent: Talent):
        if not talent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent not found")

        if data.is_active is True:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Reactivation is not allowed. Please create a new talent profile.")
        
        if data.firstname is not None and not data.firstname.strip():
            return

        if data.lastname is not None and not data.lastname.strip():
            return


def talent_exists(talent: Talent):
    if not talent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent not found")
     

