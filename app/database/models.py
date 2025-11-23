from datetime import date, time, datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Integer, Boolean, Numeric, Date, Time, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass

class Talent(Base):
    __tablename__ = "talents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    firstname: Mapped[Optional[str]] = mapped_column(String(50))
    lastname: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(100))
    tal_role: Mapped[str] = mapped_column(String(50))
    contract_type: Mapped[str] = mapped_column(String(50), default="full-time")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    hours: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)

    requests: Mapped[List["Request"]] = relationship(back_populates="talent", cascade="all, delete-orphan")
    constraints: Mapped[List["TalentConstraint"]] = relationship(back_populates="talent", cascade="all, delete-orphan")
    scheduled_shifts: Mapped[List["ScheduledShift"]] = relationship(back_populates="talent", cascade="all, delete-orphan")



class TalentConstraint(Base):
    __tablename__ = "talent_constraints"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    talent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("talents.id", ondelete="CASCADE"))
    type: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    talent: Mapped[Optional["Talent"]] = relationship(back_populates="constraints")
    rules: Mapped[List["ConstraintRule"]] = relationship(back_populates="constraint", cascade="all, delete-orphan")



class ConstraintRule(Base):
    __tablename__ = "constraint_rules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    constraint_id: Mapped[Optional[int]] = mapped_column(ForeignKey("talent_constraints.id", ondelete="CASCADE"))
    day: Mapped[Optional[str]] = mapped_column(String(50))
    shifts: Mapped[Optional[str]] = mapped_column(String(50))

    constraint: Mapped[Optional["TalentConstraint"]] = relationship(back_populates="rules")



class ShiftPeriod(Base):
    __tablename__ = "shift_periods"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    shift_name: Mapped[Optional[str]] = mapped_column(String(50))
    start_time: Mapped[Optional[time]] = mapped_column(Time)
    end_time: Mapped[Optional[time]] = mapped_column(Time)



    templates: Mapped[List["ShiftTemplate"]] = relationship(back_populates="period", cascade="all, delete-orphan")


class ShiftTemplate(Base):
    __tablename__ = "shift_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    period_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shift_periods.id", ondelete="CASCADE"))
    shift_start: Mapped[Optional[time]] = mapped_column(Time)
    shift_end: Mapped[Optional[time]] = mapped_column(Time)
    role: Mapped[Optional[str]] = mapped_column(String(50))
    


    period: Mapped[Optional["ShiftPeriod"]] = relationship(back_populates="templates")



class ScheduledShift(Base):
    __tablename__ = "scheduled_shifts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    talent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("talents.id", ondelete="CASCADE"))
    date_of: Mapped[Optional[date]] = mapped_column(Date)
    start_time: Mapped[Optional[time]] = mapped_column(Time)
    end_time: Mapped[Optional[time]] = mapped_column(Time)
    shift_hours: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    schedule_id: Mapped[Optional[int]] = mapped_column(ForeignKey("schedules.id", ondelete="CASCADE"))

   
    talent: Mapped[Optional["Talent"]] = relationship(back_populates="scheduled_shifts")
    schedule: Mapped[Optional["Schedule"]] = relationship(back_populates="scheduled_shifts")

class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True,index=True)
    week_start: Mapped[date] = mapped_column(Date)
    week_end: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String, default="draft")

    scheduled_shifts: Mapped[List["ScheduledShift"]] = relationship(back_populates="schedule", cascade="all, delete-orphan")

class Request(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    talent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("talents.id", ondelete="CASCADE"))
    req_date: Mapped[date] = mapped_column(Date)
    status: Mapped[Optional[str]] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate= func.now(), nullable=False)
    holiday_type: Mapped[str] = mapped_column(String(10), default="paid")


    talent: Mapped[Optional["Talent"]] = relationship(back_populates="requests")