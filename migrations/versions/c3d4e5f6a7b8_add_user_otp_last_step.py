"""Add users.otp_last_step (TOTP replay protection)

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-09-25 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c3d4e5f6a7b8"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("otp_last_step", sa.BigInteger(), nullable=True))


def downgrade():
    op.drop_column("users", "otp_last_step")
