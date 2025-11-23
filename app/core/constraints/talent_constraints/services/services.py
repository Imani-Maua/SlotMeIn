from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.utils.crud import CRUDBase
from app.database.models import TalentConstraint, Talent, ConstraintRule
from app.core.constraints.talent_constraints.schema import ConstraintIn, ConstraintUpdate, ConstraintOut
from app.core.constraints.talent_constraints.services.validators import validate_constraint_input, constraint_exists
from app.core.constraints.talent_constraints.utils import search_filters


class TalentConstraintService(CRUDBase[TalentConstraint, ConstraintIn, ConstraintUpdate]):

    def __init__(self):
        super().__init__(TalentConstraint)
    
    def create_constraint(self, db: Session, data: ConstraintIn):
       
        talent = db.query(Talent).filter(Talent.id == data.talent_id).first()
        constraint = db.query(TalentConstraint).filter(TalentConstraint.talent_id == data.talent_id,TalentConstraint.type == data.type).first()
        validate_constraint_input(talent=talent, constraint=constraint)
        created_constraint: TalentConstraint = self.create(db=db, obj_in=data)
        return ConstraintOut.model_validate(created_constraint)

   
    def delete_constraint(self, db: Session, constraint_id: int):
        constraint = db.query(TalentConstraint).filter(TalentConstraint.id == constraint_id).first()
        constraint_exists(constraint)
        self.delete(db=db, id=constraint_id)

def get_constraint(db: Session, id: int):
    
    constraint = db.query(TalentConstraint).join(TalentConstraint.talent).join(TalentConstraint.rules).filter(TalentConstraint.id == id).first()
    constraint_exists(constraint)
    return ConstraintOut.model_validate(constraint)

def get_all_constraints(db: Session,
                        constraint_id: int| None = None,
                        talent_id: int| None = None,
                        tal_role: str | None = None,
                        name: str | None = None,
                        contract_type: str | None = None,
                        is_active: bool| None = None):
    query = db.query(TalentConstraint).join(Talent).join(ConstraintRule)
    constraints = search_filters(query=query, 
                                 constraint_id=constraint_id,
                                 talent_id=talent_id,
                                 tal_role=tal_role,
                                 name=name,
                                 contract_type=contract_type,
                                 is_active=is_active)
    constraint_exists(constraints)
    return [ConstraintOut.model_validate(constraint) for constraint in constraints]

        
        
        

    
    