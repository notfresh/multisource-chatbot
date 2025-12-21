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

    # 使用 SQL 直接检查表是否存在
def table_exists(table_name):
    """检查表是否存在"""
    result = conn.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=:name"
    ), {"name": table_name})
    return result.fetchone() is not None
def upgrade():
    # 检查表是否存在，如果不存在则创建表
    from sqlalchemy import text
    conn = op.get_bind()
    
    # 如果 conversations 表不存在，创建它
    if not table_exists('conversations'):
        op.create_table('conversations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=True, server_default='新对话'),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    
    # 如果 messages 表不存在，创建它（包含 model 字段）
    if not table_exists('messages'):
        op.create_table('messages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('conversation_id', sa.Integer(), nullable=False),
            sa.Column('role', sa.String(length=20), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('order_index', sa.Integer(), nullable=True),
            sa.Column('model', sa.String(length=50), nullable=False, server_default='deepseek-chat'),
            sa.Column('generation_time', sa.Float(), nullable=True),
            sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade():
    # 删除表
    if table_exists('conversations'):
        op.drop_table('conversations')
    if table_exists('messages'):
        op.drop_table('messages')
    
