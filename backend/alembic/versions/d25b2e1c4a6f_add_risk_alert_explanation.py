"""add risk alert explanation

Revision ID: d25b2e1c4a6f
Revises: b97ddc59fb7a
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d25b2e1c4a6f"

down_revision: str | None = "b97ddc59fb7a"

branch_labels: str | Sequence[str] | None = None

depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "risk_alerts",
        sa.Column(
            "explanation_json",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "risk_alerts",
        "explanation_json",
    )
