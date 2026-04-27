"""Add UNIQUE constraint on post_tags (post_id, tag_id) and clean duplicate rows

Revision ID: f1a2b3c4d5e6
Revises: e8f9a0b1c2d3
Create Date: 2026-04-28 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "e8f9a0b1c2d3"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Remove any duplicate (post_id, tag_id) rows, keeping the one with the
    # lowest ctid (i.e. the first inserted row per pair).
    bind.execute(sa.text("""
        DELETE FROM post_tags
        WHERE ctid NOT IN (
            SELECT MIN(ctid)
            FROM post_tags
            GROUP BY post_id, tag_id
        )
    """))

    # Add the UNIQUE constraint only if it doesn't already exist (idempotent).
    existing_constraints = {
        c["name"]
        for c in inspector.get_unique_constraints("post_tags")
    }
    if "uq_post_tags_post_tag" not in existing_constraints:
        with op.batch_alter_table("post_tags") as batch_op:
            batch_op.create_unique_constraint(
                "uq_post_tags_post_tag", ["post_id", "tag_id"]
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_constraints = {
        c["name"]
        for c in inspector.get_unique_constraints("post_tags")
    }
    if "uq_post_tags_post_tag" in existing_constraints:
        with op.batch_alter_table("post_tags") as batch_op:
            batch_op.drop_constraint("uq_post_tags_post_tag", type_="unique")
