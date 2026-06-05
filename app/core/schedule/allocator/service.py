from app.core.schedule.shifts.schema import shiftSpecification
from app.core.schedule.talents.schema import talentAvailability
from app.core.schedule.allocator.entities import assignment
from app.core.schedule.allocator.engine.utils import get_break_duration
from ortools.sat.python import cp_model
from datetime import timedelta, date, datetime


MIN_REST_HOURS = 11
MAX_CONSECUTIVE_DAYS = 6
SCALE = 100 #cp-sat works with integers only

#hours beyond contracted hours * this factor get penalised steeply
OVERWORK_THRESHOLD = 1.15

#Objective weights


FILL_WEIGHT = 200 #reward per filled slot
UNDERWORK_PENALTY = 80     #Penalty per centihour below contracted hours
MILD_OVERWORK_PENALTY = 20 #Penalty per centihour in acceptable overwork band
STEEP_OVERWORK_PENALTY = 100 #penalty per centihour in excessive overwork band 
