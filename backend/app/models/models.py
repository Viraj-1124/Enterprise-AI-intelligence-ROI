"""
Core SQLAlchemy models.

Every table that can hold an assumption or an externally-sourced value
carries an explicit provenance concept (see app.analytics.provenance /
the `source` and `calculation_status` columns below) so the frontend never
has to guess whether a number was observed, estimated, imported, or is
simply unavailable.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from app.database.session import Base


def gen_id() -> str:
    return str(uuid.uuid4())


class Role(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    employee = "employee"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class DataSource(str, enum.Enum):
    connector = "connector"
    observed = "observed"
    imported = "imported"
    estimated = "estimated"
    unavailable = "unavailable"


class CalculationStatus(str, enum.Enum):
    calculated = "calculated"
    partial = "partial"
    unavailable = "unavailable"


class Department(Base):
    __tablename__ = "departments"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    employees = relationship("Employee", back_populates="department")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    department_id = Column(String, ForeignKey("departments.id"), nullable=True)
    role = Column(Enum(Role), nullable=False, default=Role.employee)
    # ASSUMPTION / CONFIGURATION VALUE -- used only for ROI estimation.
    hourly_cost = Column(Float, nullable=False, default=0.0)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", back_populates="employees")
    tasks = relationship("Task", back_populates="employee")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=gen_id)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    # ASSUMPTION: estimated time required without AI assistance.
    baseline_minutes = Column(Float, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    actual_minutes = Column(Float, nullable=True)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.pending)
    is_synthetic_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="tasks")
    sessions = relationship("WorkSession", back_populates="task")
    ai_usage_events = relationship("AIUsage", back_populates="task")
    outcome = relationship("TaskOutcome", back_populates="task", uselist=False)
    roi = relationship("ROIMetric", back_populates="task", uselist=False)


class WorkSession(Base):
    __tablename__ = "work_sessions"

    id = Column(String, primary_key=True, default=gen_id)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    tool = Column(String, nullable=False, default="other")
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="sessions")


class AIUsage(Base):
    __tablename__ = "ai_usage"

    id = Column(String, primary_key=True, default=gen_id)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    provider = Column(String, nullable=False)  # openai/anthropic/google/antigravity/other
    model = Column(String, nullable=True)
    session_id = Column(String, ForeignKey("work_sessions.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)
    source = Column(Enum(DataSource), nullable=False, default=DataSource.unavailable)
    usage_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="ai_usage_events")


class TaskOutcome(Base):
    __tablename__ = "task_outcomes"

    id = Column(String, primary_key=True, default=gen_id)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, unique=True)
    files_changed = Column(Integer, default=0)
    lines_added = Column(Integer, default=0)
    lines_removed = Column(Integer, default=0)
    commits = Column(Integer, default=0)
    tests_run = Column(Integer, default=0)
    tests_passed = Column(Integer, default=0)
    build_passed = Column(Boolean, nullable=True)
    output_generated = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="outcome")


class ROIMetric(Base):
    __tablename__ = "roi_metrics"

    id = Column(String, primary_key=True, default=gen_id)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, unique=True)
    time_saved_minutes = Column(Float, nullable=True)
    time_saved_percentage = Column(Float, nullable=True)
    estimated_labor_value = Column(Float, nullable=True)
    ai_cost = Column(Float, nullable=True)
    net_value = Column(Float, nullable=True)
    roi_percentage = Column(Float, nullable=True)
    roi_multiple = Column(Float, nullable=True)
    calculation_status = Column(Enum(CalculationStatus), nullable=False, default=CalculationStatus.unavailable)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    task = relationship("Task", back_populates="roi")


class ActivityEvent(Base):
    """Normalized event log backing the task activity timeline (Section 18)."""

    __tablename__ = "activity_events"

    id = Column(String, primary_key=True, default=gen_id)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String, nullable=False)
    source = Column(String, nullable=False)
    tool = Column(String, nullable=True)
    event_metadata = Column(JSON, nullable=True)


class AgentDecision(Base):
    """Auditable agent recommendation and observed result for learning."""

    __tablename__ = "agent_decisions"

    id = Column(String, primary_key=True, default=gen_id)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True, index=True)
    task_type = Column(String, nullable=False)
    complexity = Column(String, nullable=False)
    required_quality = Column(Float, nullable=False)
    selected_provider = Column(String, nullable=False)
    selected_model = Column(String, nullable=False)
    predicted_input_tokens = Column(Integer, nullable=True)
    predicted_output_tokens = Column(Integer, nullable=True)
    predicted_cost = Column(Float, nullable=True)
    predicted_latency_ms = Column(Integer, nullable=True)
    predicted_quality = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    rationale = Column(JSON, nullable=True)
    actual_input_tokens = Column(Integer, nullable=True)
    actual_output_tokens = Column(Integer, nullable=True)
    actual_cost = Column(Float, nullable=True)
    actual_latency_ms = Column(Integer, nullable=True)
    actual_quality = Column(Float, nullable=True)
    outcome = Column(String, nullable=True)
    verification_required = Column(Boolean, nullable=True)
    rework_required = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
