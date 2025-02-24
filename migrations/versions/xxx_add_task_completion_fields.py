"""add task completion fields

Revision ID: xxx
Revises: previous_revision
Create Date: 2024-02-24 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('task', sa.Column('completion_date', sa.DateTime(), nullable=True))
    op.add_column('task', sa.Column('auto_pending_days', sa.Integer(), nullable=True, server_default='30'))

def downgrade():
    op.drop_column('task', 'completion_date')
    op.drop_column('task', 'auto_pending_days') 