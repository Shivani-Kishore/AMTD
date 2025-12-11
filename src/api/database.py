"""
Database Connection Module
Handles PostgreSQL database connections
"""

import os
import logging
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class Database:
    """PostgreSQL database connection manager"""

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database connection

        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string or os.getenv(
            'DATABASE_URL',
            'postgresql://amtd:amtd@localhost:5432/amtd'
        )
        self._connection = None

    @contextmanager
    def get_connection(self):
        """
        Get database connection context manager

        Yields:
            Database connection
        """
        conn = psycopg2.connect(self.connection_string)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    @contextmanager
    def get_cursor(self, cursor_factory=None):
        """
        Get database cursor context manager

        Args:
            cursor_factory: Cursor factory (default: RealDictCursor)

        Yields:
            Database cursor
        """
        if cursor_factory is None:
            cursor_factory = psycopg2.extras.RealDictCursor

        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()

    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch: bool = True
    ) -> Optional[List[Dict]]:
        """
        Execute a SQL query

        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results

        Returns:
            Query results or None
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params or ())

                if fetch:
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                return None

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def execute_one(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> Optional[Dict]:
        """
        Execute query and return single result

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Single result dictionary or None
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params or ())
                result = cursor.fetchone()
                return dict(result) if result else None

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def insert(
        self,
        table: str,
        data: Dict[str, Any],
        returning: str = '*'
    ) -> Optional[Dict]:
        """
        Insert data into table

        Args:
            table: Table name
            data: Data dictionary
            returning: Columns to return

        Returns:
            Inserted row data
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"""
            INSERT INTO {table} ({columns})
            VALUES ({placeholders})
            RETURNING {returning}
        """

        return self.execute_one(query, tuple(data.values()))

    def update(
        self,
        table: str,
        data: Dict[str, Any],
        where: str,
        where_params: tuple,
        returning: str = '*'
    ) -> Optional[Dict]:
        """
        Update table data

        Args:
            table: Table name
            data: Data dictionary
            where: WHERE clause
            where_params: WHERE clause parameters
            returning: Columns to return

        Returns:
            Updated row data
        """
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        query = f"""
            UPDATE {table}
            SET {set_clause}
            WHERE {where}
            RETURNING {returning}
        """

        params = tuple(data.values()) + where_params
        return self.execute_one(query, params)

    def delete(
        self,
        table: str,
        where: str,
        where_params: tuple
    ) -> int:
        """
        Delete from table

        Args:
            table: Table name
            where: WHERE clause
            where_params: WHERE clause parameters

        Returns:
            Number of deleted rows
        """
        query = f"DELETE FROM {table} WHERE {where}"

        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, where_params)
                return cursor.rowcount

        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise

    def test_connection(self) -> bool:
        """
        Test database connection

        Returns:
            True if connection successful
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None

        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Global database instance
db = Database()


if __name__ == '__main__':
    # Test database connection
    logging.basicConfig(level=logging.INFO)

    if db.test_connection():
        print("Database connection successful")

        # Test query
        applications = db.execute_query(
            "SELECT * FROM applications LIMIT 5"
        )
        print(f"Found {len(applications) if applications else 0} applications")
    else:
        print("Database connection failed")
