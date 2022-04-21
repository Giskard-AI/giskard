"""rename user to giskard_users

Revision ID: a2bf1692954b
Revises: 81808bd4049a
Create Date: 2022-04-21 16:29:51.687324

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2bf1692954b'
down_revision = '81808bd4049a'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("user", "giskard_users")


def downgrade():
    op.rename_table("giskard_users", "user")
