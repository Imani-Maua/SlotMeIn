from sqlalchemy.orm import Session
from app.core.utils.enums import TemplateRole
from collections import defaultdict
from app.database.models import ShiftPeriod





class StaffingService:
    

    def __init__(self, db: Session):
        self.db = db
        self.periods = self._load_periods()
        self.staffing_rules = self._define_staffing_rules()
    
    def _load_periods(self) -> list[ShiftPeriod]:
     period = self.db.query(ShiftPeriod).join(ShiftPeriod.templates).all()
     if not period:
          raise ValueError("Period does not exist") 
     return period


    def _define_staffing_rules(self) -> dict[str, str]:
     return {
    "low": ["Monday", "Tuesday"],
    "med": ["Wednesday", "Thursday"],
    "high": ["Friday", "Saturday", "Sunday"]}


    def determine_staffing_level(self, day: str, staffing_rules: dict) -> str:
        if day in staffing_rules["low"]:
            return "low"
        elif day in staffing_rules["high"]:
            return "high"
        else:
            return "med"
    
    def staffing_configuration(self, role: str) -> dict:


        STAFFING_CONFIGURATION_RULES = {
            TemplateRole.MANAGER.value : {"low": 1, "med": 1, "high": 1},
            TemplateRole.LEADER.value: {"low": 1, "med": 2, "high": 3},
            TemplateRole.BARTENDER.value: {"low": 1, "med": 2, "high": 3},
            TemplateRole.SERVER.value: {"low": 2, "med": 3, "high": 4},
            TemplateRole.RUNNER.value: {"low": 1, "med": 2, "high": 3},
            TemplateRole.HOSTESS.value: {"low": 1, "med": 1, "high": 2}
        }

        role_staffing = STAFFING_CONFIGURATION_RULES.get(role)
        if not role_staffing:
            raise ModuleNotFoundError(f"Unknown role: {role}")
        
        return role_staffing


    def generate_roles_per_shift(self) -> dict[int, dict[str, dict]]:
     
        period_roles = defaultdict(dict)
        

        for period in self.periods:
            self.periods: list[ShiftPeriod]
            roles = {}
            for template in period.templates:
                roles[template.role] = {
                    "count": 0,
                    "shift_name": period.shift_name,
                    "start_time": template.shift_start,
                    "end_time": template.shift_end,
                    "template_id": template.id
                }

            period_roles[period.id] = roles
    
        return period_roles
    
    def apply_staffing_to_periods(self, period_roles: dict, day:str) -> dict[int, dict[str, dict]]:
     
     staffing_rules = self._define_staffing_rules()
     staffing_level = self.determine_staffing_level(day=day, staffing_rules=staffing_rules)

     staffed_periods = defaultdict(dict)

    

     for period_id, roles_dict in period_roles.items():
          roles_dict: dict
          staffed_roles = {}

          for role, role_data in roles_dict.items():
            staffing_config = self.staffing_configuration(role)
            count = staffing_config[staffing_level]

            staffed_roles[role] = {
                "count": count,
                "shift_name": role_data["shift_name"],
                "start_time": role_data["start_time"],
                "end_time": role_data["end_time"],
                "template_id": role_data["template_id"]
            }

            staffed_periods[period_id] = staffed_roles

     return staffed_periods
    
    
     
     
