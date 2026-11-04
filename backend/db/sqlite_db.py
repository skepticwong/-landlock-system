import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'landlock.db')

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
    except sqlite3.DatabaseError as e:
        if "database disk image is malformed" in str(e):
            # Try to recover using SQLite's recovery mode
            conn = sqlite3.connect(DB_PATH, isolation_level=None)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
        else:
            raise
    conn.row_factory = sqlite3.Row
    return conn

def init_db(retry_count=0):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create Users Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            phone TEXT UNIQUE,
            password_hash TEXT,
            hashed_password TEXT,
            full_name TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_superuser BOOLEAN DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
        ''')

        cursor.execute("PRAGMA table_info(users)")
        user_columns = [column[1] for column in cursor.fetchall()]
        if 'password_attempts' not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN password_attempts INTEGER DEFAULT 0")
        if 'must_change_password' not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT 0")
        
        # Create Plots Table
        # For JSON arrays like points, we can store as TEXT and serialize/deserialize
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plot_name TEXT,
            points TEXT,
            status TEXT DEFAULT 'pending',
            approved_by INTEGER,
            approved_at TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (approved_by) REFERENCES users(id)
        )
        ''')

        # Add new columns to existing plots table if they don't exist (migration)
        cursor.execute("PRAGMA table_info(plots)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'status' not in columns:
            cursor.execute("ALTER TABLE plots ADD COLUMN status TEXT DEFAULT 'pending'")
        if 'approved_by' not in columns:
            cursor.execute("ALTER TABLE plots ADD COLUMN approved_by INTEGER")
        if 'approved_at' not in columns:
            cursor.execute("ALTER TABLE plots ADD COLUMN approved_at TEXT")
        if 'district' not in columns:
            cursor.execute("ALTER TABLE plots ADD COLUMN district TEXT")
        if 'traditional_authority' not in columns:
            cursor.execute("ALTER TABLE plots ADD COLUMN traditional_authority TEXT")
        if 'village' not in columns:
            cursor.execute("ALTER TABLE plots ADD COLUMN village TEXT")
        if 'landmark_description' not in columns:
            cursor.execute("ALTER TABLE plots ADD COLUMN landmark_description TEXT")
        if 'witnesses' not in columns:
            cursor.execute("ALTER TABLE plots ADD COLUMN witnesses TEXT")
        if 'land_use' not in columns:
            cursor.execute("ALTER TABLE plots ADD COLUMN land_use TEXT")
        if 'acquisition_method' not in columns:
            cursor.execute("ALTER TABLE plots ADD COLUMN acquisition_method TEXT")
        if 'estimated_size' not in columns:
            cursor.execute("ALTER TABLE plots ADD COLUMN estimated_size TEXT")
        if 'has_map_boundary' not in columns:
            cursor.execute("ALTER TABLE plots ADD COLUMN has_map_boundary BOOLEAN DEFAULT 0")
        if 'size_unit' not in columns:
            cursor.execute("ALTER TABLE plots ADD COLUMN size_unit TEXT DEFAULT 'meters'")

        # Create Transactions Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plot_id INTEGER,
            transaction_type TEXT,
            counterparty TEXT,
            status TEXT DEFAULT 'pending',
            amount REAL,
            notes TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (plot_id) REFERENCES plots(id)
        )
        ''')

        # Create Land Listings Table (for citizens selling/leasing their land)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS land_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plot_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            asking_price REAL,
            location TEXT,
            size_description TEXT,
            listing_type TEXT DEFAULT 'sale',
            status TEXT DEFAULT 'active',
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (plot_id) REFERENCES plots(id)
        )
        ''')

        # Create Listing Images Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS listing_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            image_path TEXT NOT NULL,
            image_filename TEXT,
            created_at TEXT,
            FOREIGN KEY (listing_id) REFERENCES land_listings(id)
        )
        ''')

        # Create Plot History Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plot_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plot_id INTEGER,
            user_id INTEGER,
            change_type TEXT,
            previous_status TEXT,
            new_status TEXT,
            changes TEXT,
            created_at TEXT,
            FOREIGN KEY (plot_id) REFERENCES plots(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plot_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plot_id INTEGER NOT NULL,
            media_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            created_at TEXT,
            FOREIGN KEY (plot_id) REFERENCES plots(id)
        )
        ''')

        # Add updated_at column to plots if it doesn't exist
        cursor.execute("PRAGMA table_info(plots)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'updated_at' not in columns:
            cursor.execute("ALTER TABLE plots ADD COLUMN updated_at TEXT")

        # Add role column to users if it doesn't exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'role' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'citizen'")

        # Add multi-party approval columns to transactions
        cursor.execute("PRAGMA table_info(transactions)")
        tx_columns = [column[1] for column in cursor.fetchall()]
        if 'seller_id' not in tx_columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN seller_id INTEGER REFERENCES users(id)")
        if 'buyer_id' not in tx_columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN buyer_id INTEGER REFERENCES users(id)")
        if 'witness_id' not in tx_columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN witness_id INTEGER REFERENCES users(id)")
        if 'chief_id' not in tx_columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN chief_id INTEGER REFERENCES users(id)")
        if 'witness_approval_code' not in tx_columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN witness_approval_code TEXT")
        if 'witness_approval_status' not in tx_columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN witness_approval_status TEXT DEFAULT 'pending'")
        if 'witness_approved_at' not in tx_columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN witness_approved_at TEXT")
        if 'chief_approval_code' not in tx_columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN chief_approval_code TEXT")
        if 'chief_approval_status' not in tx_columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN chief_approval_status TEXT DEFAULT 'pending'")
        if 'chief_approved_at' not in tx_columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN chief_approved_at TEXT")
        if 'buyer_approval_status' not in tx_columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN buyer_approval_status TEXT DEFAULT 'pending'")
        if 'buyer_approved_at' not in tx_columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN buyer_approved_at TEXT")
        if 'updated_at' not in tx_columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN updated_at TEXT")

        # Create Chief Areas Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chief_areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chief_id INTEGER,
            area_type TEXT,
            area_id TEXT,
            area_name TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (chief_id) REFERENCES users(id)
        )
        ''')

        # Create Buyer Interests Table (for marketplace interest requests)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS buyer_interests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            buyer_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            message TEXT,
            status TEXT DEFAULT 'pending_consent',
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (listing_id) REFERENCES land_listings(id),
            FOREIGN KEY (buyer_id) REFERENCES users(id),
            FOREIGN KEY (seller_id) REFERENCES users(id)
        )
        ''')

        # Create Messages Table (for buyer-seller chat)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interest_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            message_type TEXT DEFAULT 'text',
            is_read BOOLEAN DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY (interest_id) REFERENCES buyer_interests(id),
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
        ''')

        # Create Transaction Events Table (immutable audit trail)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaction_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            actor_id INTEGER,
            actor_role TEXT,
            metadata TEXT,
            previous_event_hash TEXT,
            event_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(id),
            FOREIGN KEY (actor_id) REFERENCES users(id)
        )
        ''')

        # Create Notifications Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            link TEXT,
            is_read BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')

        conn.commit()
        conn.close()
    except sqlite3.DatabaseError as e:
        if "database disk image is malformed" in str(e) and retry_count < 1:
            print(f"Database corrupted: {e}")
            print("Attempting to recover by recreating database...")
            # Backup the corrupted file
            backup_path = DB_PATH + '.corrupted'
            try:
                import shutil
                shutil.move(DB_PATH, backup_path)
                print(f"Corrupted database backed up to: {backup_path}")
            except Exception as backup_error:
                print(f"Could not backup corrupted database: {backup_error}")
                # If backup fails, try deleting directly
                try:
                    os.remove(DB_PATH)
                    print(f"Deleted corrupted database: {DB_PATH}")
                except Exception as delete_error:
                    print(f"Could not delete corrupted database: {delete_error}")
                    raise
            # Retry initialization once
            init_db(retry_count + 1)
        else:
            raise

class SQLiteClient:
    def __init__(self):
        # Ensure DB is initialized
        init_db()
        
    def _dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def select(self, table, columns="*", eq=None, order=None):
        conn = get_db_connection()
        conn.row_factory = self._dict_factory
        cursor = conn.cursor()
        
        query = f"SELECT {columns} FROM {table}"
        params = []
        
        if eq:
            conditions = []
            for key, value in eq.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)
            
        if order:
            query += f" ORDER BY {order}"
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def insert(self, table, data):
        conn = get_db_connection()
        conn.row_factory = self._dict_factory
        cursor = conn.cursor()
        
        is_list = isinstance(data, list)
        items = data if is_list else [data]
        
        inserted_rows = []
        for item in items:
            # Handle JSON serialization for 'points' in plots
            if 'points' in item and isinstance(item['points'], list):
                item['points'] = json.dumps(item['points'])
                
            columns = ', '.join(item.keys())
            placeholders = ', '.join(['?'] * len(item))
            values = tuple(item.values())
            
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            cursor.execute(query, values)
            
            # Fetch the inserted row (sqlite3 lastrowid)
            cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (cursor.lastrowid,))
            inserted_rows.append(cursor.fetchone())
            
        conn.commit()
        conn.close()
        
        return inserted_rows if is_list else (inserted_rows[0] if inserted_rows else None)

    def update(self, table, data, eq=None):
        conn = get_db_connection()
        conn.row_factory = self._dict_factory
        cursor = conn.cursor()
        
        if 'points' in data and isinstance(data['points'], list):
            data['points'] = json.dumps(data['points'])
            
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        values = list(data.values())
        
        query = f"UPDATE {table} SET {set_clause}"
        
        if eq:
            conditions = []
            for key, value in eq.items():
                conditions.append(f"{key} = ?")
                values.append(value)
            query += " WHERE " + " AND ".join(conditions)
            
        cursor.execute(query, tuple(values))
        conn.commit()
        
        # We try to return updated rows if eq was provided and simple
        updated_rows = []
        if eq and len(eq) == 1 and 'id' in eq:
            cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (eq['id'],))
            updated_rows = cursor.fetchall()
            
        conn.close()
        return updated_rows

    def delete(self, table, eq):
        conn = get_db_connection()
        conn.row_factory = self._dict_factory
        cursor = conn.cursor()
        
        query = f"DELETE FROM {table}"
        params = []
        
        if eq:
            conditions = []
            for key, value in eq.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)
            
        cursor.execute(query, tuple(params))
        conn.commit()
        conn.close()
        return True

db = SQLiteClient()
