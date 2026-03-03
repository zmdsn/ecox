"""add report extra fields and constraints

Revision ID: 0f2e0e69102d
Revises: 49314d74133d
Create Date: 2026-03-03 10:03:46.764657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision: str = '0f2e0e69102d'
down_revision: Union[str, Sequence[str], None] = '49314d74133d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add columns to stock_profit_sheet
    op.add_column('stock_profit_sheet', sa.Column('extra_data', JSON(), nullable=True))
    op.add_column('stock_profit_sheet', sa.Column('update_time', sa.DateTime(), nullable=True))

    # Add columns to stock_balance_sheet
    op.add_column('stock_balance_sheet', sa.Column('extra_data', JSON(), nullable=True))
    op.add_column('stock_balance_sheet', sa.Column('update_time', sa.DateTime(), nullable=True))

    # Add columns to stock_cash_flow_sheet
    op.add_column('stock_cash_flow_sheet', sa.Column('extra_data', JSON(), nullable=True))
    op.add_column('stock_cash_flow_sheet', sa.Column('update_time', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop columns
    op.drop_column('stock_cash_flow_sheet', 'update_time')
    op.drop_column('stock_cash_flow_sheet', 'extra_data')
    op.drop_column('stock_balance_sheet', 'update_time')
    op.drop_column('stock_balance_sheet', 'extra_data')
    op.drop_column('stock_profit_sheet', 'update_time')
    op.drop_column('stock_profit_sheet', 'extra_data')
