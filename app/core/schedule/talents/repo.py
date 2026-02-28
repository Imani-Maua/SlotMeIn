from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.models import TalentData


class TalentRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def load_all_talent_rows(self) -> list[TalentData]:
        """
        Load all talent rows from the talent_data view.

        IMPORTANT: We use raw SQL instead of session.query(TalentData) because
        the talent_data view returns multiple rows per talent (one per constraint rule),
        all sharing the same `pk` value (= talent_id). SQLAlchemy's identity map
        deduplicates by primary key and silently drops the extra rows, meaning
        only the first constraint rule per talent would be returned.
        Using text() bypasses the identity map and returns ALL rows faithfully.
        """
        result = self.session.execute(text("""
            SELECT pk, talent_id, talent_name, tal_role, hours,
                   constraint_type, constraint_status, available_day, available_shifts
            FROM talent_data
        """))
        rows = result.mappings().all()

        # Convert to TalentData-like objects (namedtuple-like mapping access)
        talent_data_rows = []
        for row in rows:
            obj = TalentData()
            obj.pk = row["pk"]
            obj.talent_id = row["talent_id"]
            obj.talent_name = row["talent_name"]
            obj.tal_role = row["tal_role"]
            obj.hours = row["hours"]
            obj.constraint_type = row["constraint_type"]
            obj.constraint_status = row["constraint_status"]
            obj.available_day = row["available_day"]
            obj.available_shifts = row["available_shifts"]
            talent_data_rows.append(obj)

        return talent_data_rows