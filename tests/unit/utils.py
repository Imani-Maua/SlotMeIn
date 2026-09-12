from app.core.schedule.allocator.service import CSPScheduler
from datetime import date, datetime
from app.core.schedule.talents.schema import talentAvailability
from app.core.utils.enums import Role
from app.core.schedule.shifts.schema import shiftSpecification
from app.core.schedule.allocator.entities import assignment

MON = date(2026, 9, 14)
TUE = date(2026, 9, 15)


def _window(d: date, hour_start=8, hour_end=23) -> dict:
    return {d: [(datetime(d.year, d.month, d.day, hour_start), datetime(d.year, d.month, d.day, hour_end))]}


def _talent(tid, role=Role.SERVER, shifts=None, weeklyhours=40.0, constraint=False, dates=None) -> talentAvailability:
    if shifts is None:
        shifts = ["am"]
    if dates is None:
        dates = [MON]
    window = {}
    for d in dates:
        window[d] = [(datetime(d.year, d.month, d.day, 8), datetime(d.year, d.month, d.day, 23))]
    return talentAvailability(talent_id=tid, constraint=constraint, role=role,
                              shift_name=shifts, window=window, weeklyhours=weeklyhours)


def _shift(sid, role=Role.SERVER, role_count=1, d=MON, shift_name="am",
           hour_start=9, hour_end=17) -> shiftSpecification:
    return shiftSpecification(
        template_id=sid,
        start_time=datetime(d.year, d.month, d.day, hour_start),
        end_time=datetime(d.year, d.month, d.day, hour_end),
        shift_name=shift_name,
        role_name=role,
        role_count=role_count,
    )


def _run(availability, shifts, history=None) -> list[assignment]:
    scheduler = CSPScheduler(
        availability=availability,
        assignable_shifts=shifts,
        talents_to_assign=None,
        history=history or [],
    )
    return scheduler.generate_schedule()