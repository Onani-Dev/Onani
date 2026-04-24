"""Add external post flag and recursive external library option

Revision ID: e8f9a0b1c2d3
Revises: d6e7f8a9b0c1
Create Date: 2026-04-24 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e8f9a0b1c2d3"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    post_columns = {col["name"] for col in inspector.get_columns("posts")}
    post_indexes = {ix["name"] for ix in inspector.get_indexes("posts")}

    with op.batch_alter_table("posts") as batch_op:
        if "is_external" not in post_columns:
            batch_op.add_column(
                sa.Column("is_external", sa.Boolean(), nullable=False, server_default=sa.text("false"))
            )
        if "ix_posts_is_external" not in post_indexes:
            batch_op.create_index("ix_posts_is_external", ["is_external"], unique=False)

    lib_columns = {col["name"] for col in sa.inspect(bind).get_columns("external_libraries")}
    with op.batch_alter_table("external_libraries") as batch_op:
        if "recursive" not in lib_columns:
            batch_op.add_column(
                sa.Column("recursive", sa.Boolean(), nullable=False, server_default=sa.text("true"))
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    lib_columns = {col["name"] for col in inspector.get_columns("external_libraries")}
    with op.batch_alter_table("external_libraries") as batch_op:
        if "recursive" in lib_columns:
            batch_op.drop_column("recursive")

    post_columns = {col["name"] for col in sa.inspect(bind).get_columns("posts")}
    post_indexes = {ix["name"] for ix in sa.inspect(bind).get_indexes("posts")}
    with op.batch_alter_table("posts") as batch_op:
        if "ix_posts_is_external" in post_indexes:
            batch_op.drop_index("ix_posts_is_external")
        if "is_external" in post_columns:
            batch_op.drop_column("is_external")
