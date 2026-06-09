"""
智能排班服务模块
实现基于多因素加权评分的排班算法，考虑员工技能、偏好、工作时长、历史排班等因素
"""
import logging
from datetime import date, datetime, timedelta, time
from decimal import Decimal
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.models import (
    Employee,
    Shift,
    SchedulingRule,
    Schedule,
    LeaveRequest,
    ShiftPreference,
    RequestStatus,
    ShiftType,
)

logger = logging.getLogger(__name__)


class SchedulingAlgorithm:
    """智能排班算法类"""

    def __init__(self, db: AsyncSession, rule: SchedulingRule):
        self.db = db
        self.rule = rule
        self.shifts: List[Shift] = []
        self.employees: List[Employee] = []
        self.leave_requests: List[LeaveRequest] = []
        self.preferences: List[ShiftPreference] = []
        self.existing_schedules: List[Schedule] = []
        self.workload_tracker: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
            'total_hours': Decimal('0'),
            'consecutive_days': 0,
            'last_work_date': None,
            'rest_days_this_week': 0,
            'shift_counts': defaultdict(int),
            'night_shift_count': 0,
        })

    async def initialize(self, start_date: date, end_date: date, employee_ids: Optional[List[int]] = None):
        """初始化算法所需数据"""
        query = select(Shift).where(Shift.is_active == True)
        result = await self.db.execute(query)
        self.shifts = result.scalars().all()

        emp_query = select(Employee).where(Employee.is_active == True)
        if employee_ids:
            emp_query = emp_query.where(Employee.id.in_(employee_ids))
        emp_result = await self.db.execute(emp_query)
        self.employees = emp_result.scalars().all()

        leave_query = select(LeaveRequest).where(
            and_(
                LeaveRequest.status == RequestStatus.APPROVED,
                LeaveRequest.start_date <= end_date,
                LeaveRequest.end_date >= start_date,
            )
        )
        leave_result = await self.db.execute(leave_query)
        self.leave_requests = leave_result.scalars().all()

        pref_query = select(ShiftPreference).where(
            or_(
                and_(
                    ShiftPreference.is_recurring == False,
                    ShiftPreference.preference_date.between(start_date, end_date)
                ),
                ShiftPreference.is_recurring == True
            )
        )
        pref_result = await self.db.execute(pref_query)
        self.preferences = pref_result.scalars().all()

        hist_start = start_date - timedelta(days=30)
        hist_query = select(Schedule).where(
            and_(
                Schedule.schedule_date.between(hist_start, end_date),
                Schedule.employee_id.in_([e.id for e in self.employees])
            )
        )
        hist_result = await self.db.execute(hist_query)
        self.existing_schedules = hist_result.scalars().all()

        for schedule in self.existing_schedules:
            if schedule.schedule_date < start_date:
                self._update_workload_tracker(schedule)

    def _update_workload_tracker(self, schedule: Schedule):
        """更新工作量追踪器"""
        emp_id = schedule.employee_id
        tracker = self.workload_tracker[emp_id]
        shift = next((s for s in self.shifts if s.id == schedule.shift_id), None)
        
        if not shift:
            return

        hours = self._calculate_shift_hours(shift)
        tracker['total_hours'] += hours
        
        if schedule.schedule_date.weekday() < 5:
            if tracker['last_work_date'] is None or \
               schedule.schedule_date == tracker['last_work_date'] + timedelta(days=1):
                tracker['consecutive_days'] += 1
            else:
                tracker['consecutive_days'] = 1
        tracker['last_work_date'] = schedule.schedule_date
        
        tracker['shift_counts'][schedule.shift_id] += 1
        
        if shift.shift_type == ShiftType.NIGHT:
            tracker['night_shift_count'] += 1

    def _calculate_shift_hours(self, shift: Shift) -> Decimal:
        """计算班次时长"""
        start_dt = datetime.combine(date.today(), shift.start_time)
        end_dt = datetime.combine(date.today(), shift.end_time)
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)
        hours = (end_dt - start_dt).total_seconds() / 3600
        return Decimal(str(round(hours, 2)))

    def _is_on_leave(self, employee_id: int, schedule_date: date) -> bool:
        """检查员工是否在请假"""
        for leave in self.leave_requests:
            if leave.employee_id == employee_id and \
               leave.start_date <= schedule_date <= leave.end_date:
                return True
        return False

    def _is_unavailable(self, employee: Employee, schedule_date: date) -> bool:
        """检查员工是否不可用"""
        weekday = schedule_date.weekday()
        return weekday in employee.unavailable_days

    def _get_preference_score(self, employee_id: int, shift_id: int, schedule_date: date) -> int:
        """获取偏好评分"""
        score = 0
        weekday = schedule_date.weekday()
        
        for pref in self.preferences:
            if pref.employee_id != employee_id:
                continue
            
            if pref.is_recurring:
                if weekday in pref.recurring_days and pref.shift_id == shift_id:
                    score += pref.preference_level * 10
            else:
                if pref.preference_date == schedule_date and pref.shift_id == shift_id:
                    score += pref.preference_level * 10
        
        employee = next((e for e in self.employees if e.id == employee_id), None)
        if employee and employee.preferred_shift_type:
            shift = next((s for s in self.shifts if s.id == shift_id), None)
            if shift and shift.shift_type == employee.preferred_shift_type:
                score += 5
        
        return score

    def _get_skill_score(self, employee: Employee, shift: Shift) -> int:
        """获取技能匹配评分"""
        if not shift.required_skills:
            return self.rule.skill_weight
        
        employee_skills = set(employee.skills)
        required_skills = set(shift.required_skills)
        matched = employee_skills & required_skills
        
        if not required_skills:
            return self.rule.skill_weight
        
        match_ratio = len(matched) / len(required_skills)
        return int(self.rule.skill_weight * match_ratio)

    def _get_workload_score(self, employee_id: int, shift: Shift, schedule_date: date) -> int:
        """获取工作量评分（避免过度劳累）"""
        tracker = self.workload_tracker[employee_id]
        employee = next((e for e in self.employees if e.id == employee_id), None)
        
        if not employee:
            return 0
        
        score = self.rule.workload_weight
        
        shift_hours = self._calculate_shift_hours(shift)
        weekly_hours = self._get_weekly_hours(employee_id, schedule_date)
        
        if weekly_hours + shift_hours > self.rule.weekly_max_hours:
            score -= self.rule.workload_weight
        
        if tracker['consecutive_days'] >= employee.max_consecutive_days:
            score -= self.rule.workload_weight
        
        week_start = schedule_date - timedelta(days=schedule_date.weekday())
        week_end = week_start + timedelta(days=6)
        rest_days = self._get_rest_days_this_week(employee_id, week_start, week_end)
        if rest_days >= employee.weekly_rest_days and schedule_date.weekday() < 5:
            score -= self.rule.workload_weight // 2
        
        if shift.shift_type == ShiftType.NIGHT and tracker['night_shift_count'] > 2:
            score -= self.rule.workload_weight // 3
        
        if tracker['last_work_date'] == schedule_date - timedelta(days=1):
            prev_shift = self._get_shift_for_date(employee_id, schedule_date - timedelta(days=1))
            if prev_shift:
                prev_hours = self._calculate_shift_hours(prev_shift)
                total_hours = prev_hours + shift_hours
                if total_hours > self.rule.daily_max_hours * 1.5:
                    score -= self.rule.workload_weight // 2
        
        return max(0, score)

    def _get_history_score(self, employee_id: int, shift_id: int) -> int:
        """获取历史排班评分（均衡分配）"""
        tracker = self.workload_tracker[employee_id]
        shift_counts = tracker['shift_counts']
        
        if not shift_counts:
            return self.rule.history_weight
        
        total_shifts = sum(shift_counts.values())
        avg_shifts = total_shifts / max(len(self.shifts), 1)
        current_count = shift_counts.get(shift_id, 0)
        
        if current_count < avg_shifts * 0.8:
            return self.rule.history_weight
        elif current_count > avg_shifts * 1.2:
            return self.rule.history_weight // 3
        
        return self.rule.history_weight // 2

    def _get_weekly_hours(self, employee_id: int, current_date: date) -> Decimal:
        """获取本周已工作时长"""
        week_start = current_date - timedelta(days=current_date.weekday())
        total = Decimal('0')
        
        for schedule in self.existing_schedules:
            if schedule.employee_id == employee_id and \
               week_start <= schedule.schedule_date <= current_date:
                shift = next((s for s in self.shifts if s.id == schedule.shift_id), None)
                if shift:
                    total += self._calculate_shift_hours(shift)
        
        return total

    def _get_rest_days_this_week(self, employee_id: int, week_start: date, week_end: date) -> int:
        """获取本周已休息天数"""
        work_days = set()
        for schedule in self.existing_schedules:
            if schedule.employee_id == employee_id and \
               week_start <= schedule.schedule_date <= week_end:
                work_days.add(schedule.schedule_date)
        
        return 7 - len(work_days)

    def _get_shift_for_date(self, employee_id: int, schedule_date: date) -> Optional[Shift]:
        """获取指定日期的班次"""
        for schedule in self.existing_schedules:
            if schedule.employee_id == employee_id and schedule.schedule_date == schedule_date:
                return next((s for s in self.shifts if s.id == schedule.shift_id), None)
        return None

    def _calculate_score(self, employee: Employee, shift: Shift, schedule_date: date) -> Tuple[int, List[str]]:
        """计算综合评分"""
        reasons = []
        
        if self._is_on_leave(employee.id, schedule_date):
            return -1000, ['员工当天请假']
        
        if self._is_unavailable(employee, schedule_date):
            return -1000, ['员工当天不可用']
        
        tracker = self.workload_tracker[employee.id]
        if tracker['consecutive_days'] >= employee.max_consecutive_days:
            return -1000, [f'连续上班已达{employee.max_consecutive_days}天上限']
        
        shift_hours = self._calculate_shift_hours(shift)
        weekly_hours = self._get_weekly_hours(employee.id, schedule_date)
        if weekly_hours + shift_hours > self.rule.weekly_max_hours:
            return -1000, ['本周工时将超出上限']
        
        preference_score = self._get_preference_score(employee.id, shift.id, schedule_date)
        skill_score = self._get_skill_score(employee, shift)
        workload_score = self._get_workload_score(employee.id, shift, schedule_date)
        history_score = self._get_history_score(employee.id, shift.id)
        
        total_score = preference_score + skill_score + workload_score + history_score
        
        if preference_score > 0:
            reasons.append(f'偏好匹配(+{preference_score})')
        if skill_score > 0:
            reasons.append(f'技能匹配(+{skill_score})')
        if workload_score > 0:
            reasons.append(f'工作量适中(+{workload_score})')
        if history_score > 0:
            reasons.append(f'历史均衡(+{history_score})')
        
        return total_score, reasons

    def _check_staffing_needs(self, schedules: Dict[date, Dict[int, List[int]]], 
                               schedule_date: date, shift_id: int) -> bool:
        """检查是否满足人员需求"""
        shift = next((s for s in self.shifts if s.id == shift_id), None)
        if not shift:
            return False
        
        assigned = len(schedules.get(schedule_date, {}).get(shift_id, []))
        return assigned >= shift.min_staff

    async def generate(self, start_date: date, end_date: date) -> Tuple[List[Schedule], List[Dict[str, Any]]]:
        """生成排班表"""
        generated_schedules: List[Schedule] = []
        warnings: List[Dict[str, Any]] = []
        schedule_map: Dict[date, Dict[int, List[int]]] = defaultdict(lambda: defaultdict(list))

        for existing in self.existing_schedules:
            if existing.schedule_date >= start_date:
                schedule_map[existing.schedule_date][existing.shift_id].append(existing.employee_id)

        current_date = start_date
        while current_date <= end_date:
            for shift in self.shifts:
                if not shift.is_active:
                    continue

                current_assignments = schedule_map[current_date][shift.id]
                
                if len(current_assignments) >= shift.min_staff and \
                   (shift.max_staff is None or len(current_assignments) >= shift.max_staff):
                    continue

                candidates = []
                for employee in self.employees:
                    if employee.id in current_assignments:
                        continue
                    
                    has_shift_this_day = any(
                        employee.id in emp_list 
                        for emp_list in schedule_map[current_date].values()
                    )
                    if has_shift_this_day:
                        continue

                    score, reasons = self._calculate_score(employee, shift, current_date)
                    if score >= 0:
                        candidates.append((score, employee, reasons))

                candidates.sort(key=lambda x: x[0], reverse=True)

                needed = shift.min_staff - len(current_assignments)
                if shift.max_staff:
                    needed = min(needed, shift.max_staff - len(current_assignments))

                selected = candidates[:needed]
                
                if len(selected) < needed:
                    warnings.append({
                        'date': current_date.isoformat(),
                        'shift_id': shift.id,
                        'shift_name': shift.name,
                        'needed': needed,
                        'available': len(selected),
                        'message': f'{current_date} {shift.name} 人员不足，需要{needed}人，仅找到{len(selected)}人'
                    })

                for score, employee, reasons in selected:
                    schedule = Schedule(
                        employee_id=employee.id,
                        shift_id=shift.id,
                        schedule_date=current_date,
                        is_confirmed=False,
                        remark=f'智能排班生成，评分: {score}'
                    )
                    generated_schedules.append(schedule)
                    schedule_map[current_date][shift.id].append(employee.id)
                    
                    self._update_workload_tracker(schedule)
                    self.existing_schedules.append(schedule)

            current_date += timedelta(days=1)

        return generated_schedules, warnings


async def check_schedule_conflict(
    db: AsyncSession,
    employee_id: int,
    shift_id: int,
    schedule_date: date,
    exclude_schedule_id: Optional[int] = None
) -> Tuple[bool, List[Dict[str, Any]]]:
    """检查排班冲突"""
    conflicts = []

    query = select(Schedule).where(
        and_(
            Schedule.employee_id == employee_id,
            Schedule.schedule_date == schedule_date,
        )
    )
    if exclude_schedule_id:
        query = query.where(Schedule.id != exclude_schedule_id)
    
    result = await db.execute(query)
    existing = result.scalars().all()
    
    if existing:
        conflicts.append({
            'type': 'duplicate_shift',
            'message': '该员工当天已有排班',
            'existing_schedule': existing[0].id
        })

    leave_query = select(LeaveRequest).where(
        and_(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status == RequestStatus.APPROVED,
            LeaveRequest.start_date <= schedule_date,
            LeaveRequest.end_date >= schedule_date,
        )
    )
    leave_result = await db.execute(leave_query)
    leave = leave_result.scalar_one_or_none()
    
    if leave:
        conflicts.append({
            'type': 'leave_conflict',
            'message': f'该员工当天请假（{leave.leave_type}）',
            'leave_request_id': leave.id
        })

    emp_query = select(Employee).where(Employee.id == employee_id)
    emp_result = await db.execute(emp_query)
    employee = emp_result.scalar_one_or_none()
    
    if employee and schedule_date.weekday() in employee.unavailable_days:
        conflicts.append({
            'type': 'unavailable_day',
            'message': '该员工当天为不可用日期'
        })

    return len(conflicts) > 0, conflicts


async def calculate_attendance_stats(
    db: AsyncSession,
    start_date: date,
    end_date: date,
    employee_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """计算考勤统计数据"""
    from app.models import Attendance, AttendanceStatus, LeaveType

    query = select(
        Attendance.employee_id,
        func.count(Attendance.id).label('total_days'),
        func.sum(func.case(
            (Attendance.status == AttendanceStatus.ON_TIME, 1),
            else_=0
        )).label('on_time_days'),
        func.sum(func.case(
            (Attendance.status == AttendanceStatus.LATE, 1),
            else_=0
        )).label('late_count'),
        func.sum(func.case(
            (Attendance.status == AttendanceStatus.EARLY_LEAVE, 1),
            else_=0
        )).label('early_leave_count'),
        func.sum(func.case(
            (Attendance.status == AttendanceStatus.ABSENT, 1),
            else_=0
        )).label('absent_count'),
        func.sum(func.case(
            (Attendance.status == AttendanceStatus.LEAVE, 1),
            else_=0
        )).label('leave_days'),
        func.sum(Attendance.work_hours).label('total_work_hours'),
        func.sum(Attendance.overtime_hours).label('total_overtime_hours'),
        func.sum(Attendance.late_minutes).label('total_late_minutes'),
        func.sum(Attendance.early_leave_minutes).label('total_early_minutes'),
    ).where(
        Attendance.attendance_date.between(start_date, end_date)
    ).group_by(Attendance.employee_id)

    if employee_id:
        query = query.where(Attendance.employee_id == employee_id)

    result = await db.execute(query)
    rows = result.all()

    leave_query = select(
        LeaveRequest.employee_id,
        LeaveRequest.leave_type,
        func.sum(LeaveRequest.days).label('days')
    ).where(
        and_(
            LeaveRequest.status == RequestStatus.APPROVED,
            LeaveRequest.start_date.between(start_date, end_date)
        )
    ).group_by(LeaveRequest.employee_id, LeaveRequest.leave_type)

    if employee_id:
        leave_query = leave_query.where(LeaveRequest.employee_id == employee_id)

    leave_result = await db.execute(leave_query)
    leave_rows = leave_result.all()

    leave_by_employee: Dict[int, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in leave_rows:
        leave_by_employee[row.employee_id][row.leave_type.value] = float(row.days)

    emp_query = select(Employee)
    if employee_id:
        emp_query = emp_query.where(Employee.id == employee_id)
    emp_result = await db.execute(emp_query)
    employees = {e.id: e for e in emp_result.scalars().all()}

    stats = []
    for row in rows:
        emp = employees.get(row.employee_id)
        if not emp:
            continue
        
        user = emp.user
        stats.append({
            'employee_id': row.employee_id,
            'employee_name': user.nickname if user and user.nickname else f'员工{row.employee_id}',
            'employee_no': emp.employee_no,
            'department': emp.department,
            'total_work_days': row.total_days - (row.leave_days or 0),
            'total_work_hours': row.total_work_hours or Decimal('0'),
            'total_overtime_hours': row.total_overtime_hours or Decimal('0'),
            'late_count': row.late_count or 0,
            'early_leave_count': row.early_leave_count or 0,
            'absent_count': row.absent_count or 0,
            'leave_days': Decimal(str(row.leave_days or 0)),
            'leave_type_counts': dict(leave_by_employee.get(row.employee_id, {})),
        })

    return stats
