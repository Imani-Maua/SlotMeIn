from enum import Enum


class Role(Enum):
    MANAGER = "manager"
    LEADER = "leader"
    BARTENDER = "bartender"
    SERVER = "server"
    RUNNER = "runner"
    HOSTESS = "hostess"


class ContractType(Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    STUDENT = "student"


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

class UserRole(str, Enum):
    superuser = "superuser"
    admin = "admin"
    manager = "manager"
    user = "user"

class TokenType(Enum):
    invite = "invite"
    access = "access"