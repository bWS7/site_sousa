"""Adicionando a coluna first_viewed_at

Revision ID: 7424b12d8d4c
Revises: 
Create Date: 2025-01-29 15:10:41.568014

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7424b12d8d4c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pdf_file', schema=None) as batch_op:
        batch_op.add_column(sa.Column('first_viewed_at', sa.DateTime(), nullable=True))
        batch_op.alter_column('filename',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=100),
               nullable=True)
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pdf_file', schema=None) as batch_op:
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('filename',
               existing_type=sa.String(length=100),
               type_=sa.VARCHAR(length=200),
               nullable=False)
        batch_op.drop_column('first_viewed_at')

    # ### end Alembic commands ###
