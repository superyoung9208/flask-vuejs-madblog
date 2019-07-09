"""more notifications

Revision ID: 64ed92f0be60
Revises: 3734630b522c
Create Date: 2019-07-09 10:26:44.470791

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '64ed92f0be60'
down_revision = '3734630b522c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_followeds_posts_read_time', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('last_follows_read_time', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('last_likes_read_time', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('last_likes_read_time')
        batch_op.drop_column('last_follows_read_time')
        batch_op.drop_column('last_followeds_posts_read_time')

    # ### end Alembic commands ###