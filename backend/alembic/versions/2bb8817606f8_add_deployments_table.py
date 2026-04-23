"""add deployments table

Revision ID: 2bb8817606f8
Revises: 05aaf96c1348
Create Date: 2026-04-17 21:59:48.801651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bb8817606f8'
down_revision: Union[str, Sequence[str], None] = '05aaf96c1348'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create deployments table
    op.create_table(
        'deployments',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('architecture_id', sa.CHAR(36), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'GENERATING', 'INITIALIZING', 'PLANNING',
                                     'APPLYING', 'SUCCESS', 'FAILED', 'DESTROYING', 'DESTROYED',
                                     name='deploymentstatus'), nullable=False),
        sa.Column('terraform_version', sa.String(50), nullable=True),
        sa.Column('generated_files', sa.JSON(), nullable=True),
        sa.Column('plan_output', sa.Text(), nullable=True),
        sa.Column('apply_output', sa.Text(), nullable=True),
        sa.Column('terraform_outputs', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('deployed_by', sa.String(255), nullable=False),
        sa.Column('workspace_path', sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['architecture_id'], ['architectures.id'], ),
    )

    # Create indexes
    op.create_index(op.f('ix_deployments_id'), 'deployments', ['id'], unique=False)
    op.create_index(op.f('ix_deployments_architecture_id'), 'deployments', ['architecture_id'], unique=False)
    op.create_index(op.f('ix_deployments_status'), 'deployments', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(op.f('ix_deployments_status'), table_name='deployments')
    op.drop_index(op.f('ix_deployments_architecture_id'), table_name='deployments')
    op.drop_index(op.f('ix_deployments_id'), table_name='deployments')

    # Drop table
    op.drop_table('deployments')
