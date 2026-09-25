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


def _user_columns():
    return {col["name"] for col in sa.inspect(op.get_bind()).get_columns("users")}


def upgrade():
    # A fresh install runs `flask init-db` (create_all) before `db upgrade`,
    # so the column may already exist.
    if "otp_last_step" not in _user_columns():
        op.add_column("users", sa.Column("otp_last_step", sa.BigInteger(), nullable=True))


def downgrade():
    if "otp_last_step" in _user_columns():
        op.drop_column("users", "otp_last_step")
