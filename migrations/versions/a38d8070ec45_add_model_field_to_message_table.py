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
    # 检查表是否存在，如果不存在则先创建表
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # 如果 conversations 表不存在，先创建它
    if 'conversations' not in existing_tables:
        op.create_table('conversations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=True, server_default='新对话'),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        print("✓ 创建了 conversations 表")
    
    # 如果 messages 表不存在，先创建它（包含 model 字段）
    if 'messages' not in existing_tables:
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
        print("✓ 创建了 messages 表（包含 model 字段）")
    else:
        # 表已存在，检查是否有 model 字段
        columns = [col['name'] for col in inspector.get_columns('messages')]
        if 'model' not in columns:
            # 步骤1：添加字段（允许为空）
            op.add_column('messages', sa.Column('model', sa.String(length=50), nullable=True))
            
            # 步骤2：更新所有现有消息的 model 字段
            op.execute("UPDATE messages SET model = 'deepseek-chat' WHERE model IS NULL")
            
            # 步骤3：将字段设置为必填（SQLite 需要使用 batch mode）
            with op.batch_alter_table('messages', schema=None) as batch_op:
                batch_op.alter_column('model', nullable=False)
            print("✓ 添加了 model 字段到 messages 表")
        else:
            print("✓ messages 表已有 model 字段，跳过")


def downgrade():
    # 删除 model 字段
    op.drop_column('messages', 'model')
