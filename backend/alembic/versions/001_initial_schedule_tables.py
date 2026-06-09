"""initial schedule tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE skilltag AS ENUM ('medication', 'emergency', 'cleaning', 'reception', 'cat_care', 'night_shift');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE shifttype AS ENUM ('morning', 'afternoon', 'night', 'custom');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE leavetype AS ENUM ('annual', 'sick', 'personal', 'maternity', 'paternity', 'other');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE requeststatus AS ENUM ('pending', 'approved', 'rejected', 'cancelled');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE attendancestatus AS ENUM ('on_time', 'late', 'early_leave', 'absent', 'leave', 'day_off');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE alerttype AS ENUM ('no_check_in', 'no_check_out', 'late_arrival', 'early_departure');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create employees table
    op.create_table(
        'employees',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('employee_no', sa.String(length=50), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('position', sa.String(length=100), nullable=True),
        sa.Column('hire_date', sa.Date(), nullable=True),
        sa.Column('weekly_rest_days', sa.Integer(), server_default='2', nullable=False),
        sa.Column('max_consecutive_days', sa.Integer(), server_default='5', nullable=False),
        sa.Column('preferred_shift_type', postgresql.ENUM('morning', 'afternoon', 'night', 'custom', name='shifttype'), nullable=True),
        sa.Column('unavailable_days', postgresql.JSON(astext_type=sa.Text()), server_default='[]', nullable=True),
        sa.Column('skills', postgresql.JSON(astext_type=sa.Text()), server_default='[]', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='employees_user_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_no'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_employees_employee_no'), 'employees', ['employee_no'], unique=True)

    # Create shifts table
    op.create_table(
        'shifts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('shift_type', postgresql.ENUM('morning', 'afternoon', 'night', 'custom', name='shifttype'), server_default='custom', nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('min_staff', sa.Integer(), server_default='1', nullable=False),
        sa.Column('max_staff', sa.Integer(), nullable=True),
        sa.Column('required_skills', postgresql.JSON(astext_type=sa.Text()), server_default='[]', nullable=True),
        sa.Column('color', sa.String(length=20), server_default='#409EFF', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create scheduling_rules table
    op.create_table(
        'scheduling_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('weekly_rest_days', sa.Integer(), server_default='2', nullable=False),
        sa.Column('max_consecutive_days', sa.Integer(), server_default='5', nullable=False),
        sa.Column('daily_max_hours', sa.Numeric(precision=4, scale=1), server_default='8.0', nullable=False),
        sa.Column('weekly_max_hours', sa.Numeric(precision=4, scale=1), server_default='40.0', nullable=False),
        sa.Column('min_break_hours_between_shifts', sa.Numeric(precision=4, scale=1), server_default='12.0', nullable=False),
        sa.Column('night_shift_premium', sa.Numeric(precision=4, scale=2), server_default='1.5', nullable=False),
        sa.Column('weekend_premium', sa.Numeric(precision=4, scale=2), server_default='1.2', nullable=False),
        sa.Column('holiday_premium', sa.Numeric(precision=4, scale=2), server_default='2.0', nullable=False),
        sa.Column('preference_weight', sa.Integer(), server_default='10', nullable=False),
        sa.Column('skill_weight', sa.Integer(), server_default='20', nullable=False),
        sa.Column('workload_weight', sa.Integer(), server_default='30', nullable=False),
        sa.Column('history_weight', sa.Integer(), server_default='15', nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create schedules table
    op.create_table(
        'schedules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('shift_id', sa.Integer(), nullable=False),
        sa.Column('schedule_date', sa.Date(), nullable=False),
        sa.Column('is_confirmed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_swapped', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('original_employee_id', sa.Integer(), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], name='schedules_employee_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['original_employee_id'], ['employees.id'], name='schedules_original_employee_id_fkey', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['shift_id'], ['shifts.id'], name='schedules_shift_id_fkey', ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_schedules_employee_date', 'schedules', ['employee_id', 'schedule_date'], unique=False)

    # Create leave_requests table
    op.create_table(
        'leave_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('leave_type', postgresql.ENUM('annual', 'sick', 'personal', 'maternity', 'paternity', 'other', name='leavetype'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), server_default='09:00:00', nullable=False),
        sa.Column('end_time', sa.Time(), server_default='18:00:00', nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'approved', 'rejected', 'cancelled', name='requeststatus'), server_default='pending', nullable=False),
        sa.Column('approver_id', sa.Integer(), nullable=True),
        sa.Column('approval_remark', sa.Text(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], name='leave_requests_employee_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create shift_swaps table
    op.create_table(
        'shift_swaps',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('target_employee_id', sa.Integer(), nullable=False),
        sa.Column('schedule_date', sa.Date(), nullable=False),
        sa.Column('shift_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'approved', 'rejected', 'cancelled', name='requeststatus'), server_default='pending', nullable=False),
        sa.Column('approver_id', sa.Integer(), nullable=True),
        sa.Column('approval_remark', sa.Text(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], name='shift_swaps_employee_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shift_id'], ['shifts.id'], name='shift_swaps_shift_id_fkey', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['target_employee_id'], ['employees.id'], name='shift_swaps_target_employee_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create shift_preferences table
    op.create_table(
        'shift_preferences',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('shift_id', sa.Integer(), nullable=True),
        sa.Column('shift_type', postgresql.ENUM('morning', 'afternoon', 'night', 'custom', name='shifttype'), nullable=True),
        sa.Column('preference_type', sa.String(length=20), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('priority', sa.Integer(), server_default='0', nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], name='shift_preferences_employee_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shift_id'], ['shifts.id'], name='shift_preferences_shift_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create attendances table
    op.create_table(
        'attendances',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=True),
        sa.Column('attendance_date', sa.Date(), nullable=False),
        sa.Column('check_in_time', sa.Time(), nullable=True),
        sa.Column('check_out_time', sa.Time(), nullable=True),
        sa.Column('status', postgresql.ENUM('on_time', 'late', 'early_leave', 'absent', 'leave', 'day_off', name='attendancestatus'), server_default='on_time', nullable=False),
        sa.Column('late_minutes', sa.Integer(), nullable=True),
        sa.Column('early_leave_minutes', sa.Integer(), nullable=True),
        sa.Column('overtime_minutes', sa.Integer(), nullable=True),
        sa.Column('work_hours', sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], name='attendances_employee_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['schedule_id'], ['schedules.id'], name='attendances_schedule_id_fkey', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_attendances_employee_date', 'attendances', ['employee_id', 'attendance_date'], unique=True)

    # Create attendance_alerts table
    op.create_table(
        'attendance_alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('attendance_id', sa.Integer(), nullable=True),
        sa.Column('alert_type', postgresql.ENUM('no_check_in', 'no_check_out', 'late_arrival', 'early_departure', name='alerttype'), nullable=False),
        sa.Column('alert_message', sa.String(length=500), nullable=False),
        sa.Column('alert_time', sa.DateTime(), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['attendance_id'], ['attendances.id'], name='attendance_alerts_attendance_id_fkey', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], name='attendance_alerts_employee_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create trigger function for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create triggers for updated_at
    for table in ['employees', 'shifts', 'scheduling_rules', 'schedules', 
                  'leave_requests', 'shift_swaps', 'shift_preferences', 
                  'attendances', 'attendance_alerts']:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    # Drop triggers
    for table in ['employees', 'shifts', 'scheduling_rules', 'schedules', 
                  'leave_requests', 'shift_swaps', 'shift_preferences', 
                  'attendances', 'attendance_alerts']:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")
    
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop tables
    op.drop_table('attendance_alerts')
    op.drop_index('ix_attendances_employee_date', table_name='attendances')
    op.drop_table('attendances')
    op.drop_table('shift_preferences')
    op.drop_table('shift_swaps')
    op.drop_table('leave_requests')
    op.drop_index('ix_schedules_employee_date', table_name='schedules')
    op.drop_table('schedules')
    op.drop_table('scheduling_rules')
    op.drop_table('shifts')
    op.drop_index(op.f('ix_employees_employee_no'), table_name='employees')
    op.drop_table('employees')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS alerttype")
    op.execute("DROP TYPE IF EXISTS attendancestatus")
    op.execute("DROP TYPE IF EXISTS requeststatus")
    op.execute("DROP TYPE IF EXISTS leavetype")
    op.execute("DROP TYPE IF EXISTS shifttype")
    op.execute("DROP TYPE IF EXISTS skilltag")
