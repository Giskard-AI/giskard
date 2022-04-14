"""change superuser to admin

Revision ID: 7b1b02c08fb2
Revises: 1f2deebfe933
Create Date: 2021-02-06 08:42:20.239732

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '7b1b02c08fb2'
down_revision = '1f2deebfe933'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE role SET name='Admin' WHERE id=1")


def downgrade():
    op.execute("UPDATE role SET name='Superuser' WHERE id=1")
