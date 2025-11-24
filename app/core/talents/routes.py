from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import Annotated, Union, List
from app.core.talents.services.service import TalentService, get_talent, get_all_talents
from app.core.talents.schema import TalentIn, TalentUpdate, TalentRead
from app.database.session import session

from app.database.models import Talent


talents = APIRouter(tags=["Talents"])



@talents.post("/create")
def create_talent(db:Annotated[Session, Depends(session)],
                        data: Annotated[TalentIn,Body()],
                     
                       ):
    talents = TalentService().create_talent(db=db, data=data)
    return talents
  
@talents.put("/update/{talent_id}")
def update_talent(db: Annotated[Session, Depends(session)],
                        talent_id: int,
                        data: Annotated[TalentUpdate, Body()],
                     
                        ):
    talent = TalentService().update_talent(db, talent_id, data)
    return talent

@talents.get("/retrieve_talents")
def retirve_all_talents(db: Annotated[Session, Depends(session)], name: str | None = None, 
                          tal_role: str | None = None,
                          contract_type: str | None = None,
                          is_active: bool | None = None) -> list[TalentRead]:

    return get_all_talents(db, name=name,tal_role=tal_role,contract_type=contract_type,is_active=is_active)

@talents.get("/retrieve_talent/{talent_id}", response_model=TalentRead)
def retieve_a_talent(db: Annotated[Session, Depends(session)], talent_id:int):
    return get_talent(db=db,id=talent_id)
