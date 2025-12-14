"""Add model field to Message table

Revision ID: a38d8070ec45
Revises: fac199d8e12a
Create Date: 2024-12-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a38d8070ec45'
down_revision = 'fac199d8e12a'
branch_labels = None
depends_on = None


def upgrade():
    # 步骤1：添加字段（允许为空）
    op.add_column('messages', sa.Column('model', sa.String(length=50), nullable=True))
    
    # 步骤2：更新所有现有消息的 model 字段
    op.execute("UPDATE messages SET model = 'deepseek-chat' WHERE model IS NULL")
    
    # 步骤3：将字段设置为必填
    op.alter_column('messages', 'model', nullable=False)


def downgrade():
    # 删除 model 字段
    op.drop_column('messages', 'model')
