from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Boolean, ForeignKey, Text, Enum, JSON, Numeric
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum
from datetime import datetime, time


class SkillTag(str, enum.Enum):
    MEDICATION = "medication"
    EMERGENCY = "emergency"
    CLEANING = "cleaning"
    RECEPTION = "reception"
    CAT_CARE = "cat_care"
    NIGHT_SHIFT = "night_shift"


class ShiftType(str, enum.Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    NIGHT = "night"
    CUSTOM = "custom"


class LeaveType(str, enum.Enum):
    ANNUAL = "annual"
    SICK = "sick"
    PERSONAL = "personal"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    OTHER = "other"


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class AttendanceStatus(str, enum.Enum):
    ON_TIME = "on_time"
    LATE = "late"
    EARLY_LEAVE = "early_leave"
    ABSENT = "absent"
    LEAVE = "leave"
    DAY_OFF = "day_off"


class AlertType(str, enum.Enum):
    NO_CHECK_IN = "no_check_in"
    NO_CHECK_OUT = "no_check_out"
    LATE_ARRIVAL = "late_arrival"
    EARLY_DEPARTURE = "early_departure"


class Employee(BaseModel):
    __tablename__ = "employees"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    employee_no = Column(String(50), unique=True, index=True, nullable=False)
    department = Column(String(100))
    position = Column(String(100))
    hire_date = Column(Date)
    weekly_rest_days = Column(Integer, default=2)
    max_consecutive_days = Column(Integer, default=5)
    preferred_shift_type = Column(Enum(ShiftType, values_callable=lambda x: [e.value for e in x]))
    unavailable_days = Column(JSON, default=list)
    skills = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    remark = Column(Text)

    user = relationship("User", back_populates="employee")
    schedules = relationship("Schedule", back_populates="employee")
    leave_requests = relationship("LeaveRequest", back_populates="employee")
    shift_swaps = relationship("ShiftSwap", foreign_keys="ShiftSwap.employee_id", back_populates="employee")
    shift_swaps_target = relationship("ShiftSwap", foreign_keys="ShiftSwap.target_employee_id", back_populates="target_employee")
    preferences = relationship("ShiftPreference", back_populates="employee")
    attendances = relationship("Attendance", back_populates="employee")
    alerts = relationship("AttendanceAlert", back_populates="employee")


class Shift(BaseModel):
    __tablename__ = "shifts"

    name = Column(String(50), nullable=False)
    shift_type = Column(Enum(ShiftType, values_callable=lambda x: [e.value for e in x]), default=ShiftType.CUSTOM, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    min_staff = Column(Integer, default=1, nullable=False)
    max_staff = Column(Integer)
    required_skills = Column(JSON, default=list)
    color = Column(String(20), default="#409EFF")
    is_active = Column(Boolean, default=True)
    remark = Column(Text)

    schedules = relationship("Schedule", back_populates="shift")
    preferences = relationship("ShiftPreference", back_populates="shift")


class SchedulingRule(BaseModel):
    __tablename__ = "scheduling_rules"

    name = Column(String(100), nullable=False)
    weekly_rest_days = Column(Integer, default=2, nullable=False)
    max_consecutive_days = Column(Integer, default=5, nullable=False)
    daily_max_hours = Column(Numeric(precision=4, scale=1), default=8)
    weekly_max_hours = Column(Numeric(precision=4, scale=1), default=40)
    min_break_hours_between_shifts = Column(Numeric(precision=4, scale=1), default=12)
    night_shift_premium = Column(Numeric(precision=4, scale=2), default=1.5)
    weekend_premium = Column(Numeric(precision=4, scale=2), default=1.2)
    holiday_premium = Column(Numeric(precision=4, scale=2), default=2.0)
    preference_weight = Column(Integer, default=10)
    skill_weight = Column(Integer, default=20)
    workload_weight = Column(Integer, default=30)
    history_weight = Column(Integer, default=15)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    remark = Column(Text)


class Schedule(BaseModel):
    __tablename__ = "schedules"

    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    shift_id = Column(Integer, ForeignKey("shifts.id", ondelete="RESTRICT"), nullable=False)
    schedule_date = Column(Date, nullable=False)
    is_confirmed = Column(Boolean, default=False)
    is_swapped = Column(Boolean, default=False)
    original_employee_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"))
    remark = Column(Text)

    employee = relationship("Employee", back_populates="schedules", foreign_keys=[employee_id])
    original_employee = relationship("Employee", foreign_keys=[original_employee_id])
    shift = relationship("Shift", back_populates="schedules")
    attendance = relationship("Attendance", back_populates="schedule", uselist=False)

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class LeaveRequest(BaseModel):
    __tablename__ = "leave_requests"

    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    leave_type = Column(Enum(LeaveType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    start_time = Column(Time, default=time(9, 0))
    end_time = Column(Time, default=time(18, 0))
    days = Column(Numeric(precision=4, scale=1), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(RequestStatus, values_callable=lambda x: [e.value for e in x]), default=RequestStatus.PENDING, nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    approval_comment = Column(Text)
    approved_at = Column(DateTime)

    employee = relationship("Employee", back_populates="leave_requests")
    approver = relationship("User")


class ShiftSwap(BaseModel):
    __tablename__ = "shift_swaps"

    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    target_employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    request_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=False)
    request_shift_id = Column(Integer, ForeignKey("shifts.id", ondelete="RESTRICT"), nullable=False)
    target_shift_id = Column(Integer, ForeignKey("shifts.id", ondelete="RESTRICT"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(RequestStatus, values_callable=lambda x: [e.value for e in x]), default=RequestStatus.PENDING, nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    approval_comment = Column(Text)
    approved_at = Column(DateTime)

    employee = relationship("Employee", back_populates="shift_swaps", foreign_keys=[employee_id])
    target_employee = relationship("Employee", back_populates="shift_swaps_target", foreign_keys=[target_employee_id])
    request_shift = relationship("Shift", foreign_keys=[request_shift_id])
    target_shift = relationship("Shift", foreign_keys=[target_shift_id])
    approver = relationship("User")


class ShiftPreference(BaseModel):
    __tablename__ = "shift_preferences"

    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    shift_id = Column(Integer, ForeignKey("shifts.id", ondelete="CASCADE"), nullable=False)
    preference_date = Column(Date)
    preference_level = Column(Integer, default=1)
    is_recurring = Column(Boolean, default=False)
    recurring_days = Column(JSON, default=list)
    remark = Column(Text)

    employee = relationship("Employee", back_populates="preferences")
    shift = relationship("Shift", back_populates="preferences")


class Attendance(BaseModel):
    __tablename__ = "attendances"

    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("schedules.id", ondelete="SET NULL"))
    attendance_date = Column(Date, nullable=False)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    status = Column(Enum(AttendanceStatus, values_callable=lambda x: [e.value for e in x]), default=AttendanceStatus.ABSENT, nullable=False)
    work_hours = Column(Numeric(precision=4, scale=2), default=0)
    overtime_hours = Column(Numeric(precision=4, scale=2), default=0)
    late_minutes = Column(Integer, default=0)
    early_leave_minutes = Column(Integer, default=0)
    remark = Column(Text)

    employee = relationship("Employee", back_populates="attendances")
    schedule = relationship("Schedule", back_populates="attendance")
    alerts = relationship("AttendanceAlert", back_populates="attendance")


class AttendanceAlert(BaseModel):
    __tablename__ = "attendance_alerts"

    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    attendance_id = Column(Integer, ForeignKey("attendances.id", ondelete="CASCADE"))
    alert_type = Column(Enum(AlertType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    alert_time = Column(DateTime, default=datetime.now, nullable=False)
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    read_at = Column(DateTime)

    employee = relationship("Employee", back_populates="alerts")
    attendance = relationship("Attendance", back_populates="alerts")
