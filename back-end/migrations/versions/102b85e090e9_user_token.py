"""user token

Revision ID: 102b85e090e9
Revises: 2dd5401451a5
Create Date: 2019-06-29 20:45:58.030985

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '102b85e090e9'
down_revision = '2dd5401451a5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('token_expiration')
        batch_op.drop_column('token')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('token', sa.VARCHAR(length=32), nullable=True))
        batch_op.add_column(sa.Column('token_expiration', sa.DATETIME(), nullable=True))

    # ### end Alembic commands ###
