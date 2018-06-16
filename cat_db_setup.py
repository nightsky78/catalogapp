#!/usr/bin/env python3
"""Initialize the database tables via sqlalchemy."""

# CONFIGURATION
# Do all imports required for sqlalchemy
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime

from sqlalchemy.ext.declarative import declarative_base

# seems to have something to do with the relationships in the table
from sqlalchemy.orm import relationship

from sqlalchemy import create_engine
import datetime
# Let SQLalchemy know that below classes are special  classes
# corresponding with tables in our database
Base = declarative_base()


# Define one class for each table
# Category is the first table
class User(Base):
    """
    The class User defines the User table t_user.

    Args: Base

    Returns: no returns

    Raises: no exceptions.

    Functions: no functions.

    """

    __tablename__ = 't_user'

    name = Column(String(200), nullable=False)
    email = Column(String(100), nullable=False)
    picture = Column(String(200), nullable=False)
    id = Column(Integer, primary_key=True)


class Category(Base):
    """
    The class Category defines the User table t_category.

    Args: Base

    Returns: no returns

    Raises: no exceptions.

    Functions: serialize() returns the serialized data objects.

    """

    # define the table name with the special variable __table name
    __tablename__ = 't_category'

    #  MAPPER
    # define two columns in the table, where
    # 1. the type is string(1000) and can not be null
    # 2. the type is an integer and is a primary key
    cat_name = Column(String(200), nullable=False)
    cat_id = Column(Integer, primary_key=True)

    @property
    def serialize1(self):
        """Serialize function used for JSON endpoint."""
        # Returns object data in easily serializable format
        return {
            'cat_name': self.cat_name,
            'cat_id': self.cat_id
            }


# Define Item as the second table
class Item(Base):
    """
    The class Item defines the User table t_item.

    Args: Base

    Returns: no returns

    Raises: no exceptions.

    Functions: serialize() returns the serialized data objects.

    """

    # again as before set table name for this table.
    __tablename__ = 't_item'

    # MAPPER
    item_name = Column(String(200), nullable=False)
    item_id = Column(Integer, primary_key=True)
    item_desc = Column(String(2500))
    create_date = Column(DateTime, default=datetime.datetime.utcnow)
    # looks like it make a join
    fk_cat_id = Column(Integer, ForeignKey('t_category.cat_id'))
    # relationship with class Category
    t_category = relationship(Category)

    # adding serialisation for enabling JSON interface
    @property
    def serialize(self):
        """Serialize function used for JSON endpoint."""
        # Returns object data in easily serializable format
        return {
            'name': self.item_name,
            'description': self.item_desc,
            'create_date:': self.create_date,
            'id': self.item_id,
            }


# Create instance of the create_engine class and point it to the
# connection to our database.
# The database needs to exist already
engine = create_engine(
    'postgresql+psycopg2://vagrant:vagrant@192.168.56.3:5432/catalog')

Base.metadata.create_all(engine)
