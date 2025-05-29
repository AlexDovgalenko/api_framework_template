from sqlalchemy import MetaData, Table, Column, String, create_engine

from utils.constants import DATABASE_URL

metadata = MetaData()
users_table = Table(
    "users",
    metadata,
    Column("id",    String, primary_key=True),
    Column("email", String, unique=True, index=True),
    Column("pwd",   String),                  # plain password – demo only!
)
database_engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
