from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import StaffingRule
from app.core.schedule.staffing.schema import StaffingRuleResponse, StaffingRuleUpdate

staffing_rules = APIRouter(tags=["staffing_rules"])


@staffing_rules.get("/", response_model=list[StaffingRuleResponse])
def get_all_staffing_rules(db: Session = Depends(get_db)):
    return db.query(StaffingRule).order_by(StaffingRule.role, StaffingRule.tier).all()


@staffing_rules.patch("/{role}/{tier}", response_model=StaffingRuleResponse)
def update_staffing_rule(
    role: str,
    tier: str,
    body: StaffingRuleUpdate,
    db: Session = Depends(get_db),
):
    rule = db.query(StaffingRule).filter_by(role=role, tier=tier).first()
    if rule is None:
        rule = StaffingRule(role=role, tier=tier, count=body.count)
        db.add(rule)
    else:
        rule.count = body.count
    db.commit()
    db.refresh(rule)
    return rule
