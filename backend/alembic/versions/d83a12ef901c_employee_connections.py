"""Add employee level OAuth account links."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d83a12ef901c"
down_revision: Union[str, None] = "c6d40d921a31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("agent_decisions") as batch_op:
        batch_op.add_column(sa.Column("employee_id", sa.String(), nullable=True))
        batch_op.create_foreign_key("fk_agent_decisions_employee_id", "employees", ["employee_id"], ["id"])
    op.create_index("ix_agent_decisions_employee_id", "agent_decisions", ["employee_id"])
    op.create_table(
        "employee_connections",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("employee_id", sa.String(), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("account_id", sa.String(), nullable=False),
        sa.Column("account_name", sa.String(), nullable=False),
        sa.Column("connected_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_employee_connections_employee_id", "employee_connections", ["employee_id"])


def downgrade() -> None:
    op.drop_index("ix_employee_connections_employee_id", table_name="employee_connections")
    op.drop_table("employee_connections")
    op.drop_index("ix_agent_decisions_employee_id", table_name="agent_decisions")
    with op.batch_alter_table("agent_decisions") as batch_op:
        batch_op.drop_constraint("fk_agent_decisions_employee_id", type_="foreignkey")
        batch_op.drop_column("employee_id")
