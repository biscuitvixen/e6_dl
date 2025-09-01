"""Database module for tracking downloaded pools and posts."""

import sqlite3
import os
from pathlib import Path
from backend.logger_config import logger
from contextlib import contextmanager

class DownloadDatabase:
    def __init__(self, db_path="e6dl_downloads.db", base_download_dir="."):
        """Initialize the database connection."""
        self.db_path = db_path
        self.base_download_dir = Path(base_download_dir)
        self._init_database()
    
    def _init_database(self):
        """Create the database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table for pools
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pools (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    artist TEXT,
                    folder_path TEXT NOT NULL,
                    post_count INTEGER,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table for downloaded posts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS downloaded_posts (
                    post_id INTEGER,
                    pool_id INTEGER,
                    file_path TEXT NOT NULL,
                    position INTEGER,
                    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (post_id, pool_id),
                    FOREIGN KEY (pool_id) REFERENCES pools (id)
                )
            ''')
            
            conn.commit()
            logger.debug("Database initialized")
    
    def _to_relative_path(self, absolute_path):
        """Convert absolute path to relative path from base download directory."""
        try:
            abs_path = Path(absolute_path).resolve()
            base_path = self.base_download_dir.resolve()
            
            # If the path is under our base directory, make it relative
            if str(abs_path).startswith(str(base_path)):
                return str(abs_path.relative_to(base_path))
            else:
                # If it's outside our base directory, store as absolute for safety
                return str(abs_path)
        except (ValueError, OSError):
            # Fallback to storing as-is if there are any path issues
            return str(absolute_path)
    
    def _to_absolute_path(self, stored_path):
        """Convert stored path to absolute path."""
        path = Path(stored_path)
        
        # If it's already absolute, return as-is
        if path.is_absolute():
            return str(path)
        
        # Otherwise, resolve relative to base download directory
        return str((self.base_download_dir / path).resolve())
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def get_pool_info(self, pool_id):
        """Get existing pool information from database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pools WHERE id = ?', (pool_id,))
            row = cursor.fetchone()
            
            if row:
                # Convert stored path back to absolute path
                row_dict = dict(row)
                row_dict['folder_path'] = self._to_absolute_path(row_dict['folder_path'])
                return row_dict
            
            return None
    
    def save_pool(self, pool_id, name, artist, folder_path, post_count):
        """Save or update pool information."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Store path as relative
            relative_path = self._to_relative_path(folder_path)
            cursor.execute('''
                INSERT OR REPLACE INTO pools 
                (id, name, artist, folder_path, post_count, last_updated) 
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (pool_id, name, artist, relative_path, post_count))
            conn.commit()
            logger.debug(f"Pool {pool_id} saved to database with relative path: {relative_path}")
    
    def get_downloaded_posts(self, pool_id):
        """Get list of downloaded post IDs for a pool."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT post_id FROM downloaded_posts WHERE pool_id = ?', (pool_id,))
            return [row[0] for row in cursor.fetchall()]
    
    def mark_post_downloaded(self, post_id, pool_id, file_path, position):
        """Mark a post as downloaded."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Store path as relative
            relative_path = self._to_relative_path(file_path)
            cursor.execute('''
                INSERT OR REPLACE INTO downloaded_posts 
                (post_id, pool_id, file_path, position, downloaded_at) 
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (post_id, pool_id, relative_path, position))
            conn.commit()
            logger.debug(f"Post {post_id} marked as downloaded at relative path: {relative_path}")
    
    def get_missing_posts(self, pool_id, all_post_ids):
        """Get list of post IDs that haven't been downloaded yet."""
        downloaded = set(self.get_downloaded_posts(pool_id))
        all_posts = set(all_post_ids)
        return list(all_posts - downloaded)
    
    def verify_downloaded_files(self, pool_id):
        """Verify that downloaded files still exist and remove missing ones from DB.
        Also detect orphaned files that exist but aren't tracked in the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT post_id, file_path, position FROM downloaded_posts WHERE pool_id = ?', (pool_id,))
            records = cursor.fetchall()
            
            # Get pool info to know where files should be
            pool_info = self.get_pool_info(pool_id)
            if not pool_info:
                logger.warning(f"Pool {pool_id} not found in database, cannot verify files")
                return []
            
            folder_path = Path(pool_info['folder_path'])
            logger.info(f"Checking {len(records)} database records against filesystem in: {folder_path}")
            
            # Track which positions are accounted for in the database
            db_positions = {}  # position -> post_id mapping
            db_file_paths = set()  # Track all database file paths
            
            missing_files = []
            for post_id, stored_path, position in records:
                # Convert to absolute path for existence check
                absolute_path = self._to_absolute_path(stored_path)
                db_file_paths.add(absolute_path.lower())  # Store lowercase for comparison
                db_positions[position] = post_id
                
                if not os.path.exists(absolute_path):
                    missing_files.append(post_id)
                    cursor.execute('DELETE FROM downloaded_posts WHERE post_id = ? AND pool_id = ?', (post_id, pool_id))
                    logger.info(f"Removed missing file record: post {post_id} (expected at {absolute_path})")
            
            # Check for orphaned files (files that exist but aren't in database)
            orphaned_files = 0
            if folder_path.exists():
                for file_path in folder_path.iterdir():
                    if file_path.is_file() and not file_path.name.endswith('.url'):  # Skip .url shortcuts
                        abs_file_path = str(file_path.resolve())
                        
                        # Check if this file is tracked in database (case-insensitive)
                        if abs_file_path.lower() not in db_file_paths:
                            orphaned_files += 1
                            logger.info(f"Found orphaned file (exists but not in database): {file_path.name}")
            
            # Commit any missing file deletions
            if missing_files:
                conn.commit()
                logger.info(f"Database cleanup complete: removed {len(missing_files)} missing file records for pool {pool_id}")
            else:
                logger.info(f"All {len(records)} database records have corresponding files")
                
            if orphaned_files > 0:
                logger.info(f"Found {orphaned_files} orphaned files that exist but aren't tracked in database")
                logger.info("These files will be considered as needing re-download to ensure database consistency")
            
            return missing_files
    
    def get_all_downloaded_pools(self):
        """Get all pools that have been downloaded."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, artist, folder_path, post_count FROM pools ORDER BY last_updated DESC')
            pools = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                row_dict['folder_path'] = self._to_absolute_path(row_dict['folder_path'])
                pools.append(row_dict)
            return pools
    
    def get_pool_current_post_count(self, pool_id):
        """Get the current post count for a pool from the database."""
        pool_info = self.get_pool_info(pool_id)
        return pool_info['post_count'] if pool_info else 0
    
    def update_pool_post_count(self, pool_id, new_post_count):
        """Update the post count for a pool."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE pools 
                SET post_count = ?, last_updated = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (new_post_count, pool_id))
            conn.commit()
            logger.debug(f"Updated pool {pool_id} post count to {new_post_count}")
