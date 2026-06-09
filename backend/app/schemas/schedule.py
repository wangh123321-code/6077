from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.schedule import (
    ShiftType,
    LeaveType,
    RequestStatus,
    AttendanceStatus,
    AlertType,
    SkillTag,
)


class ScheduleBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EmployeeBase(ScheduleBase):
    employee_no: str = Field(..., description="员工编号", max_length=50)
    department: Optional[str] = Field(None, description="部门", max_length=100)
    position: Optional[str] = Field(None, description="职位", max_length=100)
    hire_date: Optional[date] = Field(None, description="入职日期")
    weekly_rest_days: int = Field(2, description="每周休息天数", ge=0, le=7)
    max_consecutive_days: int = Field(5, description="连续上班最大天数", ge=1, le=14)
    preferred_shift_type: Optional[ShiftType] = Field(None, description="偏好班次类型")
    unavailable_days: List[int] = Field(default_factory=list, description="不可用日期（星期几，0-6）")
    skills: List[str] = Field(default_factory=list, description="技能标签列表")
    is_active: bool = Field(True, description="是否在职")
    remark: Optional[str] = Field(None, description="备注")


class EmployeeCreate(EmployeeBase):
    user_id: int = Field(..., description="关联用户ID")


class EmployeeUpdate(ScheduleBase):
    department: Optional[str] = Field(None, description="部门", max_length=100)
    position: Optional[str] = Field(None, description="职位", max_length=100)
    hire_date: Optional[date] = Field(None, description="入职日期")
    weekly_rest_days: Optional[int] = Field(None, description="每周休息天数", ge=0, le=7)
    max_consecutive_days: Optional[int] = Field(None, description="连续上班最大天数", ge=1, le=14)
    preferred_shift_type: Optional[ShiftType] = Field(None, description="偏好班次类型")
    unavailable_days: Optional[List[int]] = Field(None, description="不可用日期（星期几，0-6）")
    skills: Optional[List[str]] = Field(None, description="技能标签列表")
    is_active: Optional[bool] = Field(None, description="是否在职")
    remark: Optional[str] = Field(None, description="备注")


class EmployeeUserInfo(ScheduleBase):
    id: int
    phone: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None


class EmployeeResponse(EmployeeBase):
    id: int
    user_id: int
    user: Optional[EmployeeUserInfo] = None
    created_at: datetime
    updated_at: datetime


class EmployeeListItem(ScheduleBase):
    id: int
    employee_no: str
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: bool
    user: Optional[EmployeeUserInfo] = None


class ShiftBase(ScheduleBase):
    name: str = Field(..., description="班次名称", max_length=50)
    shift_type: ShiftType = Field(ShiftType.CUSTOM, description="班次类型")
    start_time: time = Field(..., description="开始时间")
    end_time: time = Field(..., description="结束时间")
    min_staff: int = Field(1, description="最少人数", ge=1)
    max_staff: Optional[int] = Field(None, description="最大人数", ge=1)
    required_skills: List[str] = Field(default_factory=list, description="所需技能")
    color: str = Field("#409EFF", description="班次颜色", max_length=20)
    is_active: bool = Field(True, description="是否启用")
    remark: Optional[str] = Field(None, description="备注")

    @field_validator('end_time')
    def check_time_order(cls, v, values):
        if 'start_time' in values.data and v <= values.data['start_time']:
            # 允许跨夜班（如24:00-08:00）
            if not (v == time(0, 0) or values.data['start_time'] >= time(20, 0)):
                raise ValueError('结束时间必须晚于开始时间')
        return v


class ShiftCreate(ShiftBase):
    pass


class ShiftUpdate(ScheduleBase):
    name: Optional[str] = Field(None, description="班次名称", max_length=50)
    shift_type: Optional[ShiftType] = Field(None, description="班次类型")
    start_time: Optional[time] = Field(None, description="开始时间")
    end_time: Optional[time] = Field(None, description="结束时间")
    min_staff: Optional[int] = Field(None, description="最少人数", ge=1)
    max_staff: Optional[int] = Field(None, description="最大人数", ge=1)
    required_skills: Optional[List[str]] = Field(None, description="所需技能")
    color: Optional[str] = Field(None, description="班次颜色", max_length=20)
    is_active: Optional[bool] = Field(None, description="是否启用")
    remark: Optional[str] = Field(None, description="备注")


class ShiftResponse(ShiftBase):
    id: int
    created_at: datetime
    updated_at: datetime


class SchedulingRuleBase(ScheduleBase):
    name: str = Field(..., description="规则名称", max_length=100)
    weekly_rest_days: int = Field(2, description="每周休息天数", ge=0, le=7)
    max_consecutive_days: int = Field(5, description="连续上班最大天数", ge=1, le=14)
    daily_max_hours: Decimal = Field(Decimal("8.0"), description="每日最大工时", max_digits=4, decimal_places=1)
    weekly_max_hours: Decimal = Field(Decimal("40.0"), description="每周最大工时", max_digits=4, decimal_places=1)
    min_break_hours_between_shifts: Decimal = Field(Decimal("12.0"), description="班次间最小休息时间", max_digits=4, decimal_places=1)
    night_shift_premium: Decimal = Field(Decimal("1.5"), description="夜班倍数", max_digits=4, decimal_places=2)
    weekend_premium: Decimal = Field(Decimal("1.2"), description="周末倍数", max_digits=4, decimal_places=2)
    holiday_premium: Decimal = Field(Decimal("2.0"), description="节假日倍数", max_digits=4, decimal_places=2)
    preference_weight: int = Field(10, description="偏好权重", ge=0, le=100)
    skill_weight: int = Field(20, description="技能权重", ge=0, le=100)
    workload_weight: int = Field(30, description="工作量权重", ge=0, le=100)
    history_weight: int = Field(15, description="历史排班权重", ge=0, le=100)
    is_default: bool = Field(False, description="是否默认规则")
    is_active: bool = Field(True, description="是否启用")
    remark: Optional[str] = Field(None, description="备注")


class SchedulingRuleCreate(SchedulingRuleBase):
    pass


class SchedulingRuleUpdate(ScheduleBase):
    name: Optional[str] = Field(None, description="规则名称", max_length=100)
    weekly_rest_days: Optional[int] = Field(None, description="每周休息天数", ge=0, le=7)
    max_consecutive_days: Optional[int] = Field(None, description="连续上班最大天数", ge=1, le=14)
    daily_max_hours: Optional[Decimal] = Field(None, description="每日最大工时", max_digits=4, decimal_places=1)
    weekly_max_hours: Optional[Decimal] = Field(None, description="每周最大工时", max_digits=4, decimal_places=1)
    min_break_hours_between_shifts: Optional[Decimal] = Field(None, description="班次间最小休息时间", max_digits=4, decimal_places=1)
    night_shift_premium: Optional[Decimal] = Field(None, description="夜班倍数", max_digits=4, decimal_places=2)
    weekend_premium: Optional[Decimal] = Field(None, description="周末倍数", max_digits=4, decimal_places=2)
    holiday_premium: Optional[Decimal] = Field(None, description="节假日倍数", max_digits=4, decimal_places=2)
    preference_weight: Optional[int] = Field(None, description="偏好权重", ge=0, le=100)
    skill_weight: Optional[int] = Field(None, description="技能权重", ge=0, le=100)
    workload_weight: Optional[int] = Field(None, description="工作量权重", ge=0, le=100)
    history_weight: Optional[int] = Field(None, description="历史排班权重", ge=0, le=100)
    is_default: Optional[bool] = Field(None, description="是否默认规则")
    is_active: Optional[bool] = Field(None, description="是否启用")
    remark: Optional[str] = Field(None, description="备注")


class SchedulingRuleResponse(SchedulingRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ScheduleCreateRequest(ScheduleBase):
    employee_id: int = Field(..., description="员工ID")
    shift_id: int = Field(..., description="班次ID")
    schedule_date: date = Field(..., description="排班日期")
    is_confirmed: bool = Field(False, description="是否确认")
    remark: Optional[str] = Field(None, description="备注")


class ScheduleUpdateRequest(ScheduleBase):
    shift_id: Optional[int] = Field(None, description="班次ID")
    is_confirmed: Optional[bool] = Field(None, description="是否确认")
    remark: Optional[str] = Field(None, description="备注")


class ScheduleSwapRequest(ScheduleBase):
    from_employee_id: int = Field(..., description="原员工ID")
    to_employee_id: int = Field(..., description="目标员工ID")
    schedule_date: date = Field(..., description="排班日期")
    shift_id: int = Field(..., description="班次ID")
    reason: Optional[str] = Field(None, description="调班原因")


class ScheduleResponse(ScheduleBase):
    id: int
    employee_id: int
    shift_id: int
    schedule_date: date
    is_confirmed: bool
    is_swapped: bool
    original_employee_id: Optional[int] = None
    remark: Optional[str] = None
    employee: Optional[EmployeeResponse] = None
    shift: Optional[ShiftResponse] = None
    created_at: datetime
    updated_at: datetime


class ScheduleGenerateRequest(ScheduleBase):
    start_date: date = Field(..., description="排班开始日期")
    end_date: date = Field(..., description="排班结束日期")
    rule_id: Optional[int] = Field(None, description="排班规则ID，不传使用默认规则")
    employee_ids: Optional[List[int]] = Field(None, description="参与排班的员工ID列表，不传使用所有在职员工")


class ScheduleConflictCheckRequest(ScheduleBase):
    employee_id: int = Field(..., description="员工ID")
    shift_id: int = Field(..., description="班次ID")
    schedule_date: date = Field(..., description="排班日期")
    exclude_schedule_id: Optional[int] = Field(None, description="排除的排班ID（用于更新时检查）")


class ScheduleConflictResponse(ScheduleBase):
    has_conflict: bool
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    message: str


class LeaveRequestBase(ScheduleBase):
    leave_type: LeaveType = Field(..., description="请假类型")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    start_time: time = Field(time(9, 0), description="开始时间")
    end_time: time = Field(time(18, 0), description="结束时间")
    reason: str = Field(..., description="请假原因", min_length=1, max_length=1000)


class LeaveRequestCreate(LeaveRequestBase):
    pass


class LeaveRequestApprove(ScheduleBase):
    status: RequestStatus = Field(..., description="审批状态")
    approval_comment: Optional[str] = Field(None, description="审批意见", max_length=500)


class LeaveRequestResponse(LeaveRequestBase):
    id: int
    employee_id: int
    days: Decimal
    status: RequestStatus
    approver_id: Optional[int] = None
    approval_comment: Optional[str] = None
    approved_at: Optional[datetime] = None
    employee: Optional[EmployeeResponse] = None
    created_at: datetime
    updated_at: datetime


class ShiftSwapBase(ScheduleBase):
    target_employee_id: int = Field(..., description="目标员工ID")
    request_date: date = Field(..., description="申请调班日期")
    target_date: date = Field(..., description="目标调班日期")
    request_shift_id: int = Field(..., description="申请班次ID")
    target_shift_id: int = Field(..., description="目标班次ID")
    reason: str = Field(..., description="调班原因", min_length=1, max_length=1000)


class ShiftSwapCreate(ShiftSwapBase):
    pass


class ShiftSwapApprove(ScheduleBase):
    status: RequestStatus = Field(..., description="审批状态")
    approval_comment: Optional[str] = Field(None, description="审批意见", max_length=500)


class ShiftSwapResponse(ShiftSwapBase):
    id: int
    employee_id: int
    status: RequestStatus
    approver_id: Optional[int] = None
    approval_comment: Optional[str] = None
    approved_at: Optional[datetime] = None
    employee: Optional[EmployeeResponse] = None
    target_employee: Optional[EmployeeResponse] = None
    request_shift: Optional[ShiftResponse] = None
    target_shift: Optional[ShiftResponse] = None
    created_at: datetime
    updated_at: datetime


class ShiftPreferenceBase(ScheduleBase):
    shift_id: int = Field(..., description="班次ID")
    preference_date: Optional[date] = Field(None, description="偏好日期")
    preference_level: int = Field(1, description="偏好等级（1-5）", ge=1, le=5)
    is_recurring: bool = Field(False, description="是否重复")
    recurring_days: List[int] = Field(default_factory=list, description="重复的星期（0-6）")
    remark: Optional[str] = Field(None, description="备注")


class ShiftPreferenceCreate(ShiftPreferenceBase):
    pass


class ShiftPreferenceUpdate(ScheduleBase):
    shift_id: Optional[int] = Field(None, description="班次ID")
    preference_date: Optional[date] = Field(None, description="偏好日期")
    preference_level: Optional[int] = Field(None, description="偏好等级（1-5）", ge=1, le=5)
    is_recurring: Optional[bool] = Field(None, description="是否重复")
    recurring_days: Optional[List[int]] = Field(None, description="重复的星期（0-6）")
    remark: Optional[str] = Field(None, description="备注")


class ShiftPreferenceResponse(ShiftPreferenceBase):
    id: int
    employee_id: int
    employee: Optional[EmployeeResponse] = None
    shift: Optional[ShiftResponse] = None
    created_at: datetime
    updated_at: datetime


class AttendanceCheckInRequest(ScheduleBase):
    check_in_time: Optional[datetime] = Field(None, description="打卡时间，不传使用当前时间")
    location: Optional[str] = Field(None, description="打卡位置", max_length=200)


class AttendanceCheckOutRequest(ScheduleBase):
    check_out_time: Optional[datetime] = Field(None, description="打卡时间，不传使用当前时间")
    location: Optional[str] = Field(None, description="打卡位置", max_length=200)


class AttendanceResponse(ScheduleBase):
    id: int
    employee_id: int
    schedule_id: Optional[int] = None
    attendance_date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: AttendanceStatus
    work_hours: Decimal
    overtime_hours: Decimal
    late_minutes: int
    early_leave_minutes: int
    remark: Optional[str] = None
    employee: Optional[EmployeeResponse] = None
    schedule: Optional[ScheduleResponse] = None
    created_at: datetime
    updated_at: datetime


class AttendanceAlertResponse(ScheduleBase):
    id: int
    employee_id: int
    attendance_id: Optional[int] = None
    alert_type: AlertType
    alert_time: datetime
    message: str
    is_read: bool
    is_sent: bool
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    employee: Optional[EmployeeResponse] = None


class AttendanceReportRequest(ScheduleBase):
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    employee_id: Optional[int] = Field(None, description="员工ID，不传查询所有")
    department: Optional[str] = Field(None, description="部门")


class AttendanceReportItem(ScheduleBase):
    employee_id: int
    employee_name: str
    employee_no: str
    department: Optional[str] = None
    total_work_days: int
    total_work_hours: Decimal
    total_overtime_hours: Decimal
    late_count: int
    early_leave_count: int
    absent_count: int
    leave_days: Decimal
    leave_type_counts: Dict[str, int] = Field(default_factory=dict)


class AttendanceReportResponse(ScheduleBase):
    start_date: date
    end_date: date
    total_employees: int
    items: List[AttendanceReportItem]
    summary: Dict[str, Any] = Field(default_factory=dict)


class ScheduleCalendarRequest(ScheduleBase):
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    employee_id: Optional[int] = Field(None, description="员工ID，不传查询所有")
    department: Optional[str] = Field(None, description="部门")


class ScheduleCalendarItem(ScheduleBase):
    date: date
    employee_id: int
    employee_name: str
    shift_id: Optional[int] = None
    shift_name: Optional[str] = None
    shift_type: Optional[ShiftType] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    color: Optional[str] = None
    is_day_off: bool = False
    is_leave: bool = False
    leave_type: Optional[LeaveType] = None


class ScheduleCalendarResponse(ScheduleBase):
    start_date: date
    end_date: date
    items: List[ScheduleCalendarItem]
    shift_info: List[ShiftResponse]
