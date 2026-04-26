"""
Database connection and ORM base classes

Provides:
- Base declarative class for all models
- Common database connection utilities
- Async session factory configuration
"""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# Configure naming convention for constraints
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Base metadata with naming convention
metadata = MetaData(naming_convention=naming_convention)

# Base class for all models
class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy models"""

    metadata = metadata

    # Common fields can be added here if needed
    # id = Column(Integer, primary_key=True)
    # created_at = Column(DateTime, default=datetime.utcnow)
    # updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)