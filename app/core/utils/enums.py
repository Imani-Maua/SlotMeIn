from enum import Enum


class Role(Enum):
    MANAGER = "manager" 
    ASSISTANT_MANAGER = "assistant manager"
    SUPERVISOR = "supervisor"
    BARTENDER = "bartender"
    SERVER = "server"
    RUNNER = "runner"
    HOSTESS = "hostess"
    JOB_FORCE = "job force"


class ContractType(Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    STUDENT = "student"


class TemplateRole(Enum):
    MANAGER = "manager" 
    LEADER = "leader"
    BARTENDER = "bartender"
    SERVER = "server"
    RUNNER = "runner"
    HOSTESS = "hostess"
    JOB_FORCE = "job force"

    
class Shifts(Enum):
    AM = "am"
    PM = "pm"
    LOUNGE = "lounge"



class Status(Enum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"

class Holiday(Enum):
    PAID = "paid"
    UNPAID = "unpaid"

class Days(Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class ConstraintType(Enum):
    AVAILABILITY = "availability"
    SHIFT_RESTRICTION = "shift restriction"
    COMBINATION = "combination"