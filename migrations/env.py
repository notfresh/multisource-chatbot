from __future__ import with_statement

import logging
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from flask import current_app

# 导入原生 SQLAlchemy 模型（app/core/db.py）
# 这些模型使用独立的 Base，需要合并到 Flask-SQLAlchemy 的 metadata 中
try:
    from app.core.db import Base as CoreBase, ConversationDBModel, MessageDBModel
    # 合并原生 SQLAlchemy 的 metadata 到 Flask-SQLAlchemy 的 metadata
    # 这样 Flask-Migrate 就能检测到这些模型了
    from sqlalchemy import MetaData
    flask_metadata = current_app.extensions['migrate'].db.metadata
    core_metadata = CoreBase.metadata
    
    # 将 core 模型的表添加到 Flask metadata 中
    for table_name, table in core_metadata.tables.items():
        if table_name not in flask_metadata.tables:
            table.tometadata(flask_metadata)
    
    target_metadata = flask_metadata
except ImportError:
    # 如果导入失败，只使用 Flask-SQLAlchemy 的 metadata
    target_metadata = current_app.extensions['migrate'].db.metadata

# 直接从 Flask 配置获取数据库 URI，避免访问 engine.url（SQLAlchemy 1.4.x 兼容性问题）
# 对于 SQLite，确保使用绝对路径
db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
if db_uri and db_uri.startswith('sqlite:///'):
    # SQLite 路径处理：如果是相对路径，转换为绝对路径
    import os
    db_path = db_uri.replace('sqlite:///', '')
    if not os.path.isabs(db_path):
        # 相对路径，转换为绝对路径
        db_path = os.path.join(current_app.root_path, '..', db_path)
        db_path = os.path.abspath(db_path)
        db_uri = f'sqlite:///{db_path}'
else:
    # 非 SQLite 数据库，直接使用配置的 URI
    pass

config.set_main_option(
    'sqlalchemy.url',
    db_uri.replace('%', '%%') if db_uri else 'sqlite:///app.sqlite')

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    # 检测是否为 SQLite，如果是则启用 batch mode
    is_sqlite = url and url.startswith('sqlite')
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True,
        render_as_batch=is_sqlite
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # 检测是否为 SQLite，如果是则启用 batch mode
        is_sqlite = connection.dialect.name == 'sqlite'
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
            render_as_batch=is_sqlite,
            **current_app.extensions['migrate'].configure_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
