"""Dagster resources for the case study project.

Resources are external dependencies that assets need to interact with.
Examples: database connections, API clients, file systems, etc.
"""

import dagster as dg
from pydantic import Field
import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from case_study.tefas_parser import TefasCrawler


class PostgresResource(dg.ConfigurableResource):
    """PostgreSQL database resource.
    
    This resource provides a SQLAlchemy engine for connecting to PostgreSQL.
    Assets can use this to read/write data to the database.
    """
    
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="fintela")
    user: str = Field(default="postgres")
    password: str = Field(default="postgres")
    
    def get_engine(self) -> Engine:
        """Create and return a SQLAlchemy engine."""
        connection_string = (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )
        return create_engine(connection_string)


class TefasCrawlerResource(dg.ConfigurableResource):
    """TEFAS crawler resource.
    
    This resource provides a TefasCrawler instance for fetching data
    from the TEFAS website. Assets can use this to fetch fund data.
    """
    
    def get_crawler(self) -> TefasCrawler:
        """Create and return a TefasCrawler instance."""
        return TefasCrawler()

