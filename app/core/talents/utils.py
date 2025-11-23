from sqlalchemy.orm import Query
from sqlalchemy import or_
from app.core.talents.schema import ContractType
from app.database.models import Talent

def set_contract_hours(contract_type: str):
    contract_hours = {
        ContractType.FULL_TIME.value: 40,
        ContractType.PART_TIME.value: 30,
        ContractType.STUDENT.value: 24
    }

    return contract_hours.get(contract_type)

def search_filters(query: Query,
                   name: str | None = None,
                    tal_role: str | None = None,
                    contract_type: str | None = None,
                    is_active: bool | None = None):
    if tal_role:
            query = query.filter(Talent.tal_role == tal_role) 
    if contract_type:
        query = query.filter(Talent.contract_type == contract_type)
        
    if is_active is not None:
        query = query.filter(Talent.is_active == is_active)
        
    if name:
        name_pattern = f"%{name.lower()}%"
        query = query.filter(
                or_(Talent.firstname.ilike(name_pattern),
                    Talent.lastname.ilike(name_pattern),
                    (Talent.firstname + " " + Talent.lastname).ilike(name_pattern))
            )
        
    return query.all()



    