from sqlalchemy import Column, MetaData, String, Table, create_engine

from constants.common import DATABASE_URL

metadata = MetaData()
users_table = Table(
    "users",
    metadata,
    Column("id",    String, primary_key=True),
    Column("email", String, unique=True, index=True),
    Column("pwd",   String),                  # plain password – demo only!
)
database_engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
