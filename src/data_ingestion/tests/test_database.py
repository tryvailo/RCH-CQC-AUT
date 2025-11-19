"""Tests for database module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import psycopg2
from data_ingestion.database import get_db_connection, init_database
from data_ingestion.exceptions import DatabaseError


class TestDatabase:
    """Test database functions."""
    
    def test_get_db_connection_success(self):
        """Test successful database connection."""
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            
            with get_db_connection() as conn:
                assert conn == mock_conn
            
            assert mock_conn.commit.called
            assert mock_conn.close.called
    
    def test_get_db_connection_error(self):
        """Test database connection with error."""
        with patch('psycopg2.connect') as mock_connect:
            mock_connect.side_effect = psycopg2.Error("Connection failed")
            
            with pytest.raises(DatabaseError):
                with get_db_connection():
                    pass
    
    def test_get_db_connection_rollback_on_error(self):
        """Test rollback on database error."""
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_conn.commit.side_effect = psycopg2.Error("Commit failed")
            mock_connect.return_value = mock_conn
            
            with pytest.raises(DatabaseError):
                with get_db_connection():
                    pass
            
            assert mock_conn.rollback.called
    
    def test_init_database(self):
        """Test database initialization."""
        with patch('data_ingestion.database.get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value.__enter__.return_value = mock_conn
            
            init_database()
            
            # Should create tables and indexes
            assert mock_cursor.execute.call_count >= 6  # At least 6 CREATE statements

