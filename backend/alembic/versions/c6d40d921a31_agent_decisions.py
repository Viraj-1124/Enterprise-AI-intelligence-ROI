"""Add agent optimization decisions and observed results."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c6d40d921a31"
down_revision: Union[str, None] = "b02347262317"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_decisions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("task_id", sa.String(), sa.ForeignKey("tasks.id"), nullable=True),
        sa.Column("task_type", sa.String(), nullable=False),
        sa.Column("complexity", sa.String(), nullable=False),
        sa.Column("required_quality", sa.Float(), nullable=False),
        sa.Column("selected_provider", sa.String(), nullable=False),
        sa.Column("selected_model", sa.String(), nullable=False),
        sa.Column("predicted_input_tokens", sa.Integer()),
        sa.Column("predicted_output_tokens", sa.Integer()),
        sa.Column("predicted_cost", sa.Float()),
        sa.Column("predicted_latency_ms", sa.Integer()),
        sa.Column("predicted_quality", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sa.JSON()),
        sa.Column("actual_input_tokens", sa.Integer()),
        sa.Column("actual_output_tokens", sa.Integer()),
        sa.Column("actual_cost", sa.Float()),
        sa.Column("actual_latency_ms", sa.Integer()),
        sa.Column("actual_quality", sa.Float()),
        sa.Column("outcome", sa.String()),
        sa.Column("verification_required", sa.Boolean()),
        sa.Column("rework_required", sa.Boolean()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_agent_decisions_task_id", "agent_decisions", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_decisions_task_id", table_name="agent_decisions")
    op.drop_table("agent_decisions")
