"""add reply_to_id to mails

Revision ID: a1b2c3d4e5f6
Revises: 00b36bf3be30
Create Date: 2026-06-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '00b36bf3be30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('mails', sa.Column('reply_to_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('mails', 'reply_to_id')
