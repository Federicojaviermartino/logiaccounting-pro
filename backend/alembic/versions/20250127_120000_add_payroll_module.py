"""Add payroll module

Revision ID: phase40_payroll
Revises: phase39_budgeting
Create Date: 2025-01-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'phase40_payroll'
down_revision = 'phase39_budgeting'  # Update to your last migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Employees table
    op.create_table(
        'employees',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('employee_number', sa.String(20), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('middle_name', sa.String(100)),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('preferred_name', sa.String(100)),
        sa.Column('date_of_birth', sa.Date),
        sa.Column('gender', sa.Enum('male', 'female', 'other', 'prefer_not_to_say', name='gender')),
        sa.Column('marital_status', sa.Enum('single', 'married', 'divorced', 'widowed', 'domestic_partner', name='maritalstatus')),
        sa.Column('nationality', sa.String(50)),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('personal_email', sa.String(255)),
        sa.Column('phone', sa.String(30)),
        sa.Column('mobile', sa.String(30)),
        sa.Column('address_line1', sa.String(255)),
        sa.Column('address_line2', sa.String(255)),
        sa.Column('city', sa.String(100)),
        sa.Column('state', sa.String(100)),
        sa.Column('postal_code', sa.String(20)),
        sa.Column('country', sa.String(2), default='US'),
        sa.Column('ssn_last_four', sa.String(4)),
        sa.Column('federal_filing_status', sa.String(30)),
        sa.Column('federal_allowances', sa.Integer, default=0),
        sa.Column('state_filing_status', sa.String(30)),
        sa.Column('state_allowances', sa.Integer, default=0),
        sa.Column('additional_withholding', sa.Numeric(10, 2), default=0),
        sa.Column('tax_info_eu', postgresql.JSONB),
        sa.Column('department_id', postgresql.UUID(as_uuid=True)),
        sa.Column('job_title', sa.String(100)),
        sa.Column('manager_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('employees.id')),
        sa.Column('cost_center_id', postgresql.UUID(as_uuid=True)),
        sa.Column('location', sa.String(100)),
        sa.Column('hire_date', sa.Date, nullable=False),
        sa.Column('termination_date', sa.Date),
        sa.Column('termination_reason', sa.Text),
        sa.Column('employment_status', sa.Enum('active', 'on_leave', 'suspended', 'terminated', 'retired', name='employmentstatus'), default='active'),
        sa.Column('employment_type', sa.Enum('full_time', 'part_time', 'contract', 'temporary', 'intern', name='employmenttype'), default='full_time'),
        sa.Column('bank_name', sa.String(100)),
        sa.Column('bank_account_type', sa.String(20)),
        sa.Column('bank_routing_number', sa.String(20)),
        sa.Column('bank_account_last_four', sa.String(4)),
        sa.Column('emergency_contact_name', sa.String(200)),
        sa.Column('emergency_contact_phone', sa.String(30)),
        sa.Column('emergency_contact_relationship', sa.String(50)),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'employee_number', name='uq_employee_number'),
        sa.UniqueConstraint('customer_id', 'email', name='uq_employee_email'),
    )
    op.create_index('idx_employees_customer', 'employees', ['customer_id'])
    op.create_index('idx_employees_status', 'employees', ['customer_id', 'employment_status'])

    # Employee Contracts
    op.create_table(
        'employee_contracts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contract_number', sa.String(30), nullable=False),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date),
        sa.Column('job_title', sa.String(100), nullable=False),
        sa.Column('job_description', sa.Text),
        sa.Column('department_id', postgresql.UUID(as_uuid=True)),
        sa.Column('compensation_type', sa.Enum('salary', 'hourly', 'commission', 'mixed', name='compensationtype'), default='salary'),
        sa.Column('annual_salary', sa.Numeric(12, 2)),
        sa.Column('hourly_rate', sa.Numeric(8, 2)),
        sa.Column('commission_rate', sa.Numeric(5, 2)),
        sa.Column('commission_base', sa.Numeric(12, 2)),
        sa.Column('pay_frequency', sa.Enum('weekly', 'biweekly', 'semimonthly', 'monthly', name='payfrequency'), default='biweekly'),
        sa.Column('standard_hours_per_week', sa.Numeric(4, 1), default=40),
        sa.Column('standard_hours_per_day', sa.Numeric(3, 1), default=8),
        sa.Column('overtime_eligibility', sa.Enum('exempt', 'non_exempt', name='overtimeeligibility'), default='non_exempt'),
        sa.Column('overtime_rate_multiplier', sa.Numeric(3, 2), default=1.5),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('probation_end_date', sa.Date),
        sa.Column('probation_completed', sa.Boolean, default=False),
        sa.Column('vacation_days_annual', sa.Numeric(4, 1), default=15),
        sa.Column('sick_days_annual', sa.Numeric(4, 1), default=10),
        sa.Column('personal_days_annual', sa.Numeric(4, 1), default=3),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('termination_reason', sa.Text),
        sa.Column('additional_terms', postgresql.JSONB),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('employee_id', 'contract_number', name='uq_contract_number'),
    )
    op.create_index('idx_employee_contracts_employee', 'employee_contracts', ['employee_id'])

    # Deduction Types
    op.create_table(
        'deduction_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('category', sa.Enum('tax', 'insurance', 'retirement', 'garnishment', 'union', 'other', name='deductioncategory'), nullable=False),
        sa.Column('calculation_method', sa.Enum('fixed', 'percentage', 'percentage_of_net', 'tiered', 'custom', name='calculationmethod'), default='fixed'),
        sa.Column('default_amount', sa.Numeric(10, 2)),
        sa.Column('default_percentage', sa.Numeric(5, 4)),
        sa.Column('annual_limit', sa.Numeric(12, 2)),
        sa.Column('per_period_limit', sa.Numeric(10, 2)),
        sa.Column('employer_match', sa.Boolean, default=False),
        sa.Column('employer_match_percentage', sa.Numeric(5, 4)),
        sa.Column('employer_match_limit', sa.Numeric(12, 2)),
        sa.Column('pre_tax', sa.Boolean, default=False),
        sa.Column('expense_account_id', postgresql.UUID(as_uuid=True)),
        sa.Column('liability_account_id', postgresql.UUID(as_uuid=True)),
        sa.Column('applies_to_all', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('sort_order', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'code', name='uq_deduction_type_code'),
    )

    # Employee Deductions
    op.create_table(
        'employee_deductions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('deduction_type_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('deduction_types.id'), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2)),
        sa.Column('percentage', sa.Numeric(5, 4)),
        sa.Column('ytd_employee_amount', sa.Numeric(12, 2), default=0),
        sa.Column('ytd_employer_amount', sa.Numeric(12, 2), default=0),
        sa.Column('start_date', sa.DateTime),
        sa.Column('end_date', sa.DateTime),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('employee_id', 'deduction_type_id', name='uq_employee_deduction'),
    )

    # Benefit Types
    op.create_table(
        'benefit_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('category', sa.String(30), nullable=False),
        sa.Column('employee_cost', sa.Numeric(10, 2), default=0),
        sa.Column('employer_cost', sa.Numeric(10, 2), default=0),
        sa.Column('coverage_type', sa.String(30)),
        sa.Column('expense_account_id', postgresql.UUID(as_uuid=True)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'code', name='uq_benefit_type_code'),
    )

    # Employee Benefits
    op.create_table(
        'employee_benefits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('benefit_type_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('benefit_types.id'), nullable=False),
        sa.Column('coverage_type', sa.String(30)),
        sa.Column('employee_cost', sa.Numeric(10, 2)),
        sa.Column('employer_cost', sa.Numeric(10, 2)),
        sa.Column('enrollment_date', sa.DateTime, default=sa.func.now()),
        sa.Column('effective_date', sa.DateTime, nullable=False),
        sa.Column('termination_date', sa.DateTime),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )

    # Pay Periods
    op.create_table(
        'pay_periods',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('period_number', sa.Integer, nullable=False),
        sa.Column('period_year', sa.Integer, nullable=False),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('pay_date', sa.Date, nullable=False),
        sa.Column('frequency', sa.String(20), nullable=False),
        sa.Column('status', sa.Enum('open', 'processing', 'completed', 'closed', name='payperiodstatus'), default='open'),
        sa.Column('total_gross', sa.Numeric(14, 2), default=0),
        sa.Column('total_deductions', sa.Numeric(14, 2), default=0),
        sa.Column('total_net', sa.Numeric(14, 2), default=0),
        sa.Column('total_employer_taxes', sa.Numeric(14, 2), default=0),
        sa.Column('employee_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'period_year', 'period_number', 'frequency', name='uq_pay_period'),
    )

    # Payroll Runs
    op.create_table(
        'payroll_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('pay_period_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pay_periods.id'), nullable=False),
        sa.Column('run_number', sa.String(30), nullable=False),
        sa.Column('run_type', sa.String(20), default='regular'),
        sa.Column('status', sa.Enum('draft', 'calculating', 'pending_approval', 'approved', 'processing_payments', 'completed', 'voided', name='payrollrunstatus'), default='draft'),
        sa.Column('run_date', sa.DateTime, default=sa.func.now()),
        sa.Column('calculated_at', sa.DateTime),
        sa.Column('approved_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('total_gross_pay', sa.Numeric(14, 2), default=0),
        sa.Column('total_deductions', sa.Numeric(14, 2), default=0),
        sa.Column('total_net_pay', sa.Numeric(14, 2), default=0),
        sa.Column('total_employer_taxes', sa.Numeric(14, 2), default=0),
        sa.Column('total_employer_benefits', sa.Numeric(14, 2), default=0),
        sa.Column('employee_count', sa.Integer, default=0),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('journal_entry_id', postgresql.UUID(as_uuid=True)),
        sa.Column('notes', sa.Text),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'run_number', name='uq_payroll_run_number'),
    )

    # Payroll Lines
    op.create_table(
        'payroll_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('payroll_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payroll_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('employees.id'), nullable=False),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('employee_contracts.id'), nullable=False),
        sa.Column('employee_number', sa.String(20), nullable=False),
        sa.Column('employee_name', sa.String(200), nullable=False),
        sa.Column('regular_hours', sa.Numeric(6, 2), default=0),
        sa.Column('overtime_hours', sa.Numeric(6, 2), default=0),
        sa.Column('holiday_hours', sa.Numeric(6, 2), default=0),
        sa.Column('pto_hours', sa.Numeric(6, 2), default=0),
        sa.Column('sick_hours', sa.Numeric(6, 2), default=0),
        sa.Column('regular_rate', sa.Numeric(10, 4), nullable=False),
        sa.Column('overtime_rate', sa.Numeric(10, 4), default=0),
        sa.Column('regular_pay', sa.Numeric(12, 2), default=0),
        sa.Column('overtime_pay', sa.Numeric(12, 2), default=0),
        sa.Column('holiday_pay', sa.Numeric(12, 2), default=0),
        sa.Column('pto_pay', sa.Numeric(12, 2), default=0),
        sa.Column('sick_pay', sa.Numeric(12, 2), default=0),
        sa.Column('bonus', sa.Numeric(12, 2), default=0),
        sa.Column('commission', sa.Numeric(12, 2), default=0),
        sa.Column('other_earnings', sa.Numeric(12, 2), default=0),
        sa.Column('gross_pay', sa.Numeric(12, 2), default=0),
        sa.Column('total_deductions', sa.Numeric(12, 2), default=0),
        sa.Column('federal_tax', sa.Numeric(10, 2), default=0),
        sa.Column('state_tax', sa.Numeric(10, 2), default=0),
        sa.Column('local_tax', sa.Numeric(10, 2), default=0),
        sa.Column('social_security', sa.Numeric(10, 2), default=0),
        sa.Column('medicare', sa.Numeric(10, 2), default=0),
        sa.Column('net_pay', sa.Numeric(12, 2), default=0),
        sa.Column('employer_social_security', sa.Numeric(10, 2), default=0),
        sa.Column('employer_medicare', sa.Numeric(10, 2), default=0),
        sa.Column('employer_futa', sa.Numeric(10, 2), default=0),
        sa.Column('employer_suta', sa.Numeric(10, 2), default=0),
        sa.Column('employer_benefits', sa.Numeric(10, 2), default=0),
        sa.Column('total_employer_cost', sa.Numeric(12, 2), default=0),
        sa.Column('ytd_gross', sa.Numeric(14, 2), default=0),
        sa.Column('ytd_federal_tax', sa.Numeric(12, 2), default=0),
        sa.Column('ytd_state_tax', sa.Numeric(12, 2), default=0),
        sa.Column('ytd_social_security', sa.Numeric(12, 2), default=0),
        sa.Column('ytd_medicare', sa.Numeric(12, 2), default=0),
        sa.Column('ytd_net', sa.Numeric(14, 2), default=0),
        sa.Column('payment_method', sa.String(20), default='direct_deposit'),
        sa.Column('payment_status', sa.String(20), default='pending'),
        sa.Column('check_number', sa.String(20)),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.UniqueConstraint('payroll_run_id', 'employee_id', name='uq_payroll_line_employee'),
    )

    # Payroll Line Deductions
    op.create_table(
        'payroll_line_deductions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('payroll_line_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payroll_lines.id', ondelete='CASCADE'), nullable=False),
        sa.Column('deduction_type_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('deduction_types.id'), nullable=False),
        sa.Column('deduction_code', sa.String(20), nullable=False),
        sa.Column('deduction_name', sa.String(100), nullable=False),
        sa.Column('category', sa.String(30), nullable=False),
        sa.Column('employee_amount', sa.Numeric(10, 2), default=0),
        sa.Column('employer_amount', sa.Numeric(10, 2), default=0),
        sa.Column('ytd_employee', sa.Numeric(12, 2), default=0),
        sa.Column('ytd_employer', sa.Numeric(12, 2), default=0),
    )

    # Time Off Requests
    op.create_table(
        'time_off_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('employees.id'), nullable=False),
        sa.Column('request_number', sa.String(30), nullable=False),
        sa.Column('time_off_type', sa.Enum('vacation', 'sick', 'personal', 'bereavement', 'jury_duty', 'military', 'maternity', 'paternity', 'unpaid', 'other', name='timeofftype'), nullable=False),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('hours_requested', sa.Numeric(6, 2), nullable=False),
        sa.Column('start_time', sa.String(10)),
        sa.Column('end_time', sa.String(10)),
        sa.Column('reason', sa.Text),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', 'cancelled', name='timeoffstatus'), default='pending'),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('reviewed_at', sa.DateTime),
        sa.Column('review_notes', sa.Text),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'request_number', name='uq_time_off_request_number'),
    )

    # Time Off Balances
    op.create_table(
        'time_off_balances',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('time_off_type', sa.Enum('vacation', 'sick', 'personal', 'bereavement', 'jury_duty', 'military', 'maternity', 'paternity', 'unpaid', 'other', name='timeofftype'), nullable=False),
        sa.Column('annual_entitlement', sa.Numeric(6, 2), default=0),
        sa.Column('carryover_from_previous', sa.Numeric(6, 2), default=0),
        sa.Column('hours_used', sa.Numeric(6, 2), default=0),
        sa.Column('hours_pending', sa.Numeric(6, 2), default=0),
        sa.Column('adjustments', sa.Numeric(6, 2), default=0),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('employee_id', 'year', 'time_off_type', name='uq_time_off_balance'),
    )


def downgrade() -> None:
    op.drop_table('time_off_balances')
    op.drop_table('time_off_requests')
    op.drop_table('payroll_line_deductions')
    op.drop_table('payroll_lines')
    op.drop_table('payroll_runs')
    op.drop_table('pay_periods')
    op.drop_table('employee_benefits')
    op.drop_table('benefit_types')
    op.drop_table('employee_deductions')
    op.drop_table('deduction_types')
    op.drop_table('employee_contracts')
    op.drop_table('employees')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS timeoffstatus')
    op.execute('DROP TYPE IF EXISTS timeofftype')
    op.execute('DROP TYPE IF EXISTS payrollrunstatus')
    op.execute('DROP TYPE IF EXISTS payperiodstatus')
    op.execute('DROP TYPE IF EXISTS calculationmethod')
    op.execute('DROP TYPE IF EXISTS deductioncategory')
    op.execute('DROP TYPE IF EXISTS overtimeeligibility')
    op.execute('DROP TYPE IF EXISTS payfrequency')
    op.execute('DROP TYPE IF EXISTS compensationtype')
    op.execute('DROP TYPE IF EXISTS employmenttype')
    op.execute('DROP TYPE IF EXISTS employmentstatus')
    op.execute('DROP TYPE IF EXISTS maritalstatus')
    op.execute('DROP TYPE IF EXISTS gender')
