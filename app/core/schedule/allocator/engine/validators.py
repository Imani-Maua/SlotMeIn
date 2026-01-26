from abc import ABC, abstractmethod
from datetime import timedelta, date
from app.core.schedule.shifts.schema import shiftSpecification
from app.core.schedule.talents.schema import talentAvailability
from app.core.schedule.allocator.entities import assignment

class abstractValidator(ABC):
    @abstractmethod
    def can_assign_shift(self, context):
        """Determine whether a shift can be assigned based on specific validation rules.

        Args:
            context (dict): Dictionary containing relevant data for validation.

        Returns:
            bool: True if the shift can be assigned, False otherwise.
        """
        raise NotImplementedError
    

class context():
    
    @staticmethod
    def contextFinder(talent_id: int,
                       shift: dict[int,shiftSpecification], 
                       availability: dict[int, talentAvailability], 
                       assignments: list[assignment]):
        """Creates a standardized context dictionary for validators.

        Args:
            talent_id (int): ID of the talent being considered.
            shift (shiftSpecification): The shift to validate.
            availability (dict[int, talentAvailability]): Talent availability mapping.
            assignments (list[assignment]): Current assignments.

        Returns:
            dict: Context dictionary containing the above data.
        """
        context = {
            "talent_id": talent_id,
            "shift": shift,
            "availability": availability,
            "assignments": assignments
        }

        return context


class maxHoursValidator(abstractValidator):
    """Validator that ensures a talent's total assigned hours do not exceed their weekly limit."""

    def can_assign_shift(self, context: dict) -> bool:
        """Check if assigning the current shift exceeds the talent's weekly working hours.

        Args:
            context (dict): Context containing talent_id, shift, availability, and assignments.

        Returns:
            bool: True if the shift can be assigned without exceeding weekly hours, False otherwise.
        """
        talent_id: int = context["talent_id"]
        shift: shiftSpecification = context["shift"]
        availability: dict[int, talentAvailability] = context["availability"]
        assignments: list[assignment] = context["assignments"]

        duration = (shift.end_time - shift.start_time).total_seconds() / 3600
        existing_assignments = [a for a in assignments if a.talent_id == talent_id]
        total_hours = sum(
            (a.shift.end_time - a.shift.start_time).total_seconds() / 3600
            for a in existing_assignments
        )
        return total_hours + duration <= availability[talent_id].weeklyhours

class consecutiveValidator(abstractValidator):
    """Validator to ensure a talent does not work more than six consecutive days."""

    def can_assign_shift(self, context: dict) -> bool:
        """Check if assigning the shift would violate the maximum consecutive workdays rule.

        Args:
            context (dict): Context containing talent_id, shift, and assignments.

        Returns:
            bool: True if the talent can be assigned without exceeding six consecutive days, False otherwise.
        """
        talent_id: int = context["talent_id"]
        shift: shiftSpecification = context["shift"]
        assignments: list[assignment] = context["assignments"]

        def check(date, streak=1):
            if streak >= 6:
                return False
            
            prev_date = date - timedelta(days=1)
            for a in assignments:
                if a.talent_id == talent_id and a.shift.start_time.date() == prev_date:
                    return check(prev_date, streak + 1)
            return True
        
        return check(shift.start_time.date())

class restValidator(abstractValidator):
    """Validator to enforce a minimum rest period (11 hours) between shifts."""

    def get_yesterday_end_time(self, context: dict):
        """Get the end time of the talent's shift on the previous day.

        Args:
            context (dict): Context containing talent_id, shift, and assignments.

        Returns:
            datetime | None: End time of the previous day's shift, or None if none exists.
        """
        talent_id: int = context["talent_id"]
        shift: shiftSpecification = context["shift"]
        assignments: list[assignment] = context["assignments"]

        yesterday = shift.start_time.date() - timedelta(days=1)
        for a in assignments:
            if a.talent_id == talent_id and a.shift.start_time.date() == yesterday:
                return a.shift.end_time
        return None
    
    def can_assign_shift(self, context: dict) -> bool:
        """Check if the talent has had at least 11 hours of rest since the previous shift.

        Args:
            context (dict): Context containing talent_id, shift, and assignments.

        Returns:
            bool: True if the shift can be assigned without violating rest period rules, False otherwise.
        """
        shift: shiftSpecification = context["shift"]
        yesterday_end = self.get_yesterday_end_time(context)
        if yesterday_end and (shift.start_time - yesterday_end).total_seconds() / 3600 < 11:
            return False
        return True

class dailyAssignmentValidator(abstractValidator):
    """Validator to ensure a talent is not assigned to multiple shifts on the same date."""

    def __init__(self):
        self.assigned = set()

    
    def mark_assigned(self, context: dict):
        """Mark a talent as assigned for a specific date.

        Args:
            context (dict): Context containing talent_id and shift.
        """
        talent_id: int = context["talent_id"]
        shift: shiftSpecification = context["shift"]
        self.assigned.add((talent_id, shift.start_time.date()))

    def can_assign_shift(self, context: dict) -> bool:
        """Check if a talent has already been assigned to a shift on the same date.

        Args:
            context (dict): Context containing talent_id and shift.

        Returns:
            bool: True if the talent has not been assigned yet, False if already assigned.
        """
        talent_id: int = context["talent_id"]
        shift:  shiftSpecification = context["shift"]
        return not (talent_id, shift.start_time.date()) in self.assigned
    








