"""widen password column to 256 chars for hashing

Revision ID: ce712d2bae8f
Revises: 
Create Date: 2026-05-15 13:26:45.006571

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce712d2bae8f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('Users', schema=None) as batch_op:
        batch_op.alter_column('password',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=256),
               existing_nullable=False)


def downgrade():
    with op.batch_alter_table('Users', schema=None) as batch_op:
        batch_op.alter_column('password',
               existing_type=sa.String(length=256),
               type_=sa.VARCHAR(length=50),
               existing_nullable=False)
