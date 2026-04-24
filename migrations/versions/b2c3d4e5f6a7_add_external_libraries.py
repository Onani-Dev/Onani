"""Add external_libraries and external_library_files tables

Revision ID: b2c3d4e5f6a7
Revises: a9b0c1d2e3f4
Create Date: 2026-04-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if 'external_libraries' not in table_names:
        op.create_table(
            'external_libraries',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('path', sa.String(), nullable=False),
            sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('default_rating', sa.String(length=1), nullable=False, server_default='q'),
            sa.Column('default_tags', sa.Text(), nullable=True),
            sa.Column('owner_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('last_scan_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_scan_status', sa.String(length=20), nullable=True),
            sa.Column('last_scan_task_id', sa.String(length=36), nullable=True),
            sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )

    lib_indexes = {ix['name'] for ix in inspector.get_indexes('external_libraries')} if 'external_libraries' in set(sa.inspect(bind).get_table_names()) else set()
    if 'ix_external_libraries_owner_id' not in lib_indexes:
        op.create_index('ix_external_libraries_owner_id', 'external_libraries', ['owner_id'])

    table_names = set(sa.inspect(bind).get_table_names())
    if 'external_library_files' not in table_names:
        op.create_table(
            'external_library_files',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('library_id', sa.Integer(), nullable=False),
            sa.Column('file_path', sa.Text(), nullable=False),
            sa.Column('sha256_hash', sa.String(length=64), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
            sa.Column('post_id', sa.Integer(), nullable=True),
            sa.Column('error', sa.Text(), nullable=True),
            sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('imported_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['library_id'], ['external_libraries.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('library_id', 'file_path', name='uq_library_file_path'),
        )

    file_indexes = {ix['name'] for ix in sa.inspect(bind).get_indexes('external_library_files')} if 'external_library_files' in set(sa.inspect(bind).get_table_names()) else set()
    if 'ix_external_library_files_library_id' not in file_indexes:
        op.create_index('ix_external_library_files_library_id', 'external_library_files', ['library_id'])
    if 'ix_external_library_files_sha256_hash' not in file_indexes:
        op.create_index('ix_external_library_files_sha256_hash', 'external_library_files', ['sha256_hash'])
    if 'ix_external_library_files_post_id' not in file_indexes:
        op.create_index('ix_external_library_files_post_id', 'external_library_files', ['post_id'])


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if 'external_library_files' in table_names:
        file_indexes = {ix['name'] for ix in inspector.get_indexes('external_library_files')}
        if 'ix_external_library_files_post_id' in file_indexes:
            op.drop_index('ix_external_library_files_post_id', table_name='external_library_files')
        if 'ix_external_library_files_sha256_hash' in file_indexes:
            op.drop_index('ix_external_library_files_sha256_hash', table_name='external_library_files')
        if 'ix_external_library_files_library_id' in file_indexes:
            op.drop_index('ix_external_library_files_library_id', table_name='external_library_files')
        op.drop_table('external_library_files')

    table_names = set(sa.inspect(bind).get_table_names())
    if 'external_libraries' in table_names:
        lib_indexes = {ix['name'] for ix in sa.inspect(bind).get_indexes('external_libraries')}
        if 'ix_external_libraries_owner_id' in lib_indexes:
            op.drop_index('ix_external_libraries_owner_id', table_name='external_libraries')
        op.drop_table('external_libraries')
