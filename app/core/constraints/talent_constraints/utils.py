from sqlalchemy.orm import Query
from sqlalchemy import or_
from app.database.models import Talent, TalentConstraint


def search_filters(query: Query,
                   constraint_id: int| None = None,
                        talent_id: int| None = None,
                        tal_role: str | None = None,
                        name: str | None = None,
                        contract_type: str | None = None,
                        is_active: bool| None = None):
    if constraint_id:
        query = query.filter(TalentConstraint.id == constraint_id)
    
    if talent_id:
        query = query.filter(Talent.id == talent_id)
    
    if tal_role:
        query = query.filter(Talent.tal_role)
    
    if name:
        name_pattern = f"%{name.lower()}%"
        query = query.filter(
            or_(Talent.firstname.ilike(name_pattern),
                Talent.lastname.ilike(name_pattern),
                (Talent.firstname + " " + Talent.lastname).ilike(name_pattern))
        )
    
    if contract_type:
        query = query.filter(Talent.contract_type == contract_type)
    
    if is_active is not None:
        query = query.filter(Talent.is_active == is_active)
    
    return query.all()
