"""Initial vacancies table creation

Revision ID: 001_initial
Revises: 
Create Date: 2026-04-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создание таблицы vacancies
    op.create_table(
        'vacancies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('employer', sa.String(), nullable=True),
        sa.Column('salary_from', sa.Integer(), nullable=True),
        sa.Column('salary_to', sa.Integer(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('area', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('published_at', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создание индексов
    op.create_index('idx_created_at', 'vacancies', ['created_at'])
    op.create_index('idx_published_at', 'vacancies', ['published_at'])


def downgrade() -> None:
    # Удаление индексов и таблицы
    op.drop_index('idx_published_at', table_name='vacancies')
    op.drop_index('idx_created_at', table_name='vacancies')
    op.drop_table('vacancies')
