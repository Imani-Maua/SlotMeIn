from app.core.utils.enums import Shifts


def get_break_duration(shift_name:str):

    shift_name = shift_name.lower()
    break_duration = {
        Shifts.AM.value: 0.75,
        Shifts.PM.value: 0.5,
        Shifts.LOUNGE.value: 0.5
    }

    return break_duration.get(shift_name)