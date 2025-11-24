from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import Annotated
from app.core.constraints.talent_constraints.services.services import TalentConstraintService, get_all_constraints, get_constraint
from app.database.session import session
from app.core.constraints.talent_constraints.schema import ConstraintIn



talent_constraints = APIRouter(tags=["Talent Constraints"])



@talent_constraints.post("/create")
def create_constraint(db: Annotated[Session, Depends(session)],
                      data: Annotated[ConstraintIn, Body()]
                     
                      ):
    constraint = TalentConstraintService().create_constraint(db=db, data=data)
    return constraint

@talent_constraints.delete("/delete/{constraint_id}", status_code=204)
def delete_constraint(db: Annotated[Session, Depends(session)],
                              constraint_id: int
                            
                              ):
    TalentConstraintService().delete_constraint(db=db, constraint_id=constraint_id)

@talent_constraints.get("/retrieve_constraint/{constraint_id}")
def retrieve_constraint(db:Annotated[Session, Depends(session)], constraint_id: int):
    return get_constraint(db=db, id=constraint_id)

@talent_constraints.get("/retrieve_all_constraints")
def retrieve_all_constraints(db: Annotated[Session, Depends(session)],
                        constraint_id: int| None = None,
                        talent_id: int| None = None,
                        tal_role: str | None = None,
                        name: str | None = None,
                        contract_type: str | None = None,
                        is_active: bool| None = None):
    return get_all_constraints(db=db,
                               constraint_id=constraint_id,
                               talent_id=talent_id,
                               tal_role=tal_role,
                               name=name,
                               contract_type=contract_type,
                               is_active=is_active)


