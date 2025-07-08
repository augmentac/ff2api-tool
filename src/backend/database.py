import sqlite3
import json
import os
import shutil
import zipfile
import hashlib
from datetime import datetime
from cryptography.fernet import Fernet
import logging
from typing import Optional

class DatabaseManager:
    def __init__(self, db_path="data/freight_loader.db"):
        self.db_path = db_path
        self.backup_dir = "data/backups"
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with enhanced brokerage-centric schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced brokerage configurations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS brokerage_configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brokerage_name TEXT NOT NULL,
                configuration_name TEXT NOT NULL,
                field_mappings TEXT NOT NULL,
                api_credentials TEXT NOT NULL,
                file_headers TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP,
                version INTEGER DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                description TEXT,
                UNIQUE(brokerage_name, configuration_name)
            )
        ''')
        
        # Enhanced upload history table with better error tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS upload_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brokerage_name TEXT NOT NULL,
                configuration_name TEXT,
                filename TEXT NOT NULL,
                total_records INTEGER,
                successful_records INTEGER,
                failed_records INTEGER,
                error_log TEXT,
                processing_time_seconds REAL,
                file_headers TEXT,
                upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT
            )
        ''')
        
        # Processing errors table for detailed troubleshooting
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_history_id INTEGER,
                row_number INTEGER,
                field_name TEXT,
                error_type TEXT,
                error_message TEXT,
                suggested_fix TEXT,
                original_value TEXT,
                expected_format TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (upload_history_id) REFERENCES upload_history (id)
            )
        ''')
        
        # Configuration change log for versioning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuration_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                configuration_id INTEGER,
                change_type TEXT NOT NULL, -- 'created', 'updated', 'field_added', 'field_removed', 'field_modified'
                change_description TEXT,
                old_value TEXT,
                new_value TEXT,
                changed_by TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (configuration_id) REFERENCES brokerage_configurations (id)
            )
        ''')
        
        # Legacy table migration - keep old table for backward compatibility
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT UNIQUE NOT NULL,
                field_mappings TEXT NOT NULL,
                api_credentials TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Backup history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_name TEXT NOT NULL,
                backup_path TEXT NOT NULL,
                backup_size INTEGER,
                backup_type TEXT NOT NULL,
                checksum TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        ''')
        
        conn.commit()
        
        # Migrate existing databases to new schema
        self._migrate_database_schema(conn, cursor)
        
        conn.commit()
        conn.close()
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, backup_name=None, description=""):
        """Create a complete database backup"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create backup directory
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.db")
        
        try:
            # Create database backup
            shutil.copy2(self.db_path, backup_path)
            
            # Calculate checksum for integrity verification
            checksum = self._calculate_file_checksum(backup_path)
            
            # Get backup size
            backup_size = os.path.getsize(backup_path)
            
            # Record backup in history
            self._save_backup_history(backup_name, backup_path, backup_size, "database", checksum, description)
            
            return {
                'success': True,
                'backup_name': backup_name,
                'backup_path': backup_path,
                'size': backup_size,
                'checksum': checksum
            }
            
        except Exception as e:
            logging.error(f"Error creating backup: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def create_data_export(self, customer_name=None, export_format="json", backup_name=None):
        """Export data in various formats (JSON, CSV)"""
        if not backup_name:
            backup_name = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            export_data = {
                'export_info': {
                    'created_at': datetime.now().isoformat(),
                    'export_format': export_format,
                    'customer_name': customer_name
                },
                'customer_mappings': [],
                'upload_history': []
            }
            
            # Export customer mappings
            if customer_name:
                mapping = self.get_customer_mapping(customer_name)
                if mapping:
                    export_data['customer_mappings'].append({
                        'customer_name': customer_name,
                        'field_mappings': mapping['field_mappings'],
                        # Don't export API credentials for security
                        'api_credentials': {'base_url': mapping['api_credentials'].get('base_url', '')},
                        'created_at': datetime.now().isoformat()
                    })
            else:
                # Export all mappings
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT customer_name, field_mappings, created_at, updated_at FROM customer_mappings')
                mappings = cursor.fetchall()
                
                for mapping in mappings:
                    export_data['customer_mappings'].append({
                        'customer_name': mapping[0],
                        'field_mappings': json.loads(mapping[1]),
                        'created_at': mapping[2],
                        'updated_at': mapping[3]
                    })
                conn.close()
            
            # Export upload history
            history = self.get_upload_history(customer_name, limit=None)
            for record in history:
                export_data['upload_history'].append({
                    'brokerage_name': record[1],  # Updated to use brokerage_name
                    'filename': record[3],        # Adjusted index for new schema
                    'total_records': record[4],
                    'successful_records': record[5],
                    'failed_records': record[6],
                    'error_log': json.loads(record[7]) if record[7] else None,
                    'upload_timestamp': record[10]  # Adjusted index for new schema
                })
            
            # Save export file
            export_path = os.path.join(self.backup_dir, f"{backup_name}.json")
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            # Create ZIP archive
            zip_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(export_path, f"{backup_name}.json")
            
            # Clean up JSON file
            os.remove(export_path)
            
            # Calculate checksum
            checksum = self._calculate_file_checksum(zip_path)
            backup_size = os.path.getsize(zip_path)
            
            # Record export in history
            self._save_backup_history(backup_name, zip_path, backup_size, "export", checksum, f"Data export for {customer_name or 'all customers'}")
            
            return {
                'success': True,
                'export_name': backup_name,
                'export_path': zip_path,
                'size': backup_size,
                'checksum': checksum
            }
            
        except Exception as e:
            logging.error(f"Error creating data export: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def restore_from_backup(self, backup_name):
        """Restore database from backup"""
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.db")
        
        if not os.path.exists(backup_path):
            return {
                'success': False,
                'error': 'Backup file not found'
            }
        
        try:
            # Verify backup integrity
            backup_info = self.get_backup_info(backup_name)
            if backup_info:
                current_checksum = self._calculate_file_checksum(backup_path)
                if current_checksum != backup_info['checksum']:
                    return {
                        'success': False,
                        'error': 'Backup file integrity check failed'
                    }
            
            # Create current database backup before restore
            current_backup = self.create_backup(f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}", "Backup before restore operation")
            
            # Restore database
            shutil.copy2(backup_path, self.db_path)
            
            return {
                'success': True,
                'restored_from': backup_name,
                'pre_restore_backup': current_backup
            }
            
        except Exception as e:
            logging.error(f"Error restoring from backup: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def import_data(self, import_file_path):
        """Import data from export file"""
        try:
            # Extract and read import file
            with zipfile.ZipFile(import_file_path, 'r') as zipf:
                # Get the JSON file from the zip
                json_files = [f for f in zipf.namelist() if f.endswith('.json')]
                if not json_files:
                    return {'success': False, 'error': 'No JSON data file found in archive'}
                
                json_content = zipf.read(json_files[0])
                import_data = json.loads(json_content)
            
            # Validate import data structure
            if not all(key in import_data for key in ['export_info', 'customer_mappings', 'upload_history']):
                return {'success': False, 'error': 'Invalid import data structure'}
            
            # Import customer mappings
            imported_mappings = 0
            imported_history = 0
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # Import customer mappings (skip API credentials for security)
                for mapping in import_data['customer_mappings']:
                    cursor.execute('''
                        INSERT OR IGNORE INTO customer_mappings 
                        (customer_name, field_mappings, api_credentials, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        mapping['customer_name'],
                        json.dumps(mapping['field_mappings']),
                        json.dumps({'base_url': '', 'api_key': ''}),  # Empty credentials
                        mapping.get('created_at', datetime.now().isoformat()),
                        mapping.get('updated_at', datetime.now().isoformat())
                    ))
                    imported_mappings += 1
                
                # Import upload history
                for record in import_data['upload_history']:
                    cursor.execute('''
                        INSERT INTO upload_history 
                        (brokerage_name, filename, total_records, successful_records, failed_records, error_log, upload_timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        record.get('brokerage_name', record.get('customer_name', 'Unknown')),  # Handle both old and new formats
                        record['filename'],
                        record['total_records'],
                        record['successful_records'],
                        record['failed_records'],
                        json.dumps(record['error_log']) if record['error_log'] else None,
                        record['upload_timestamp']
                    ))
                    imported_history += 1
                
                conn.commit()
                
                return {
                    'success': True,
                    'imported_mappings': imported_mappings,
                    'imported_history': imported_history
                }
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
                
        except Exception as e:
            logging.error(f"Error importing data: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_backup_list(self):
        """Get list of available backups"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT backup_name, backup_path, backup_size, backup_type, created_at, description
            FROM backup_history
            ORDER BY created_at DESC
        ''')
        
        backups = cursor.fetchall()
        conn.close()
        
        # Verify backup files still exist
        verified_backups = []
        for backup in backups:
            if os.path.exists(backup[1]):
                verified_backups.append({
                    'name': backup[0],
                    'path': backup[1],
                    'size': backup[2],
                    'type': backup[3],
                    'created_at': backup[4],
                    'description': backup[5]
                })
        
        return verified_backups

    def get_backup_info(self, backup_name):
        """Get detailed information about a specific backup"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT backup_name, backup_path, backup_size, backup_type, checksum, created_at, description
            FROM backup_history
            WHERE backup_name = ?
        ''', (backup_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'name': result[0],
                'path': result[1],
                'size': result[2],
                'type': result[3],
                'checksum': result[4],
                'created_at': result[5],
                'description': result[6]
            }
        return None

    def delete_backup(self, backup_name):
        """Delete a backup file and its record"""
        backup_info = self.get_backup_info(backup_name)
        if not backup_info:
            return {'success': False, 'error': 'Backup not found'}
        
        try:
            # Delete backup file
            if os.path.exists(backup_info['path']):
                os.remove(backup_info['path'])
            
            # Remove from backup history
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM backup_history WHERE backup_name = ?', (backup_name,))
            conn.commit()
            conn.close()
            
            return {'success': True}
            
        except Exception as e:
            logging.error(f"Error deleting backup: {e}")
            return {'success': False, 'error': str(e)}

    def verify_backup_integrity(self, backup_name):
        """Verify the integrity of a backup file"""
        backup_info = self.get_backup_info(backup_name)
        if not backup_info:
            return {'success': False, 'error': 'Backup not found'}
        
        if not os.path.exists(backup_info['path']):
            return {'success': False, 'error': 'Backup file not found'}
        
        try:
            current_checksum = self._calculate_file_checksum(backup_info['path'])
            integrity_ok = current_checksum == backup_info['checksum']
            
            return {
                'success': True,
                'integrity_ok': integrity_ok,
                'original_checksum': backup_info['checksum'],
                'current_checksum': current_checksum
            }
            
        except Exception as e:
            logging.error(f"Error verifying backup integrity: {e}")
            return {'success': False, 'error': str(e)}

    def _save_backup_history(self, backup_name, backup_path, backup_size, backup_type, checksum, description):
        """Save backup record to history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO backup_history 
            (backup_name, backup_path, backup_size, backup_type, checksum, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (backup_name, backup_path, backup_size, backup_type, checksum, description))
        
        conn.commit()
        conn.close()

    def _calculate_file_checksum(self, file_path):
        """Calculate SHA256 checksum of a file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def get_database_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get table counts
        cursor.execute('SELECT COUNT(*) FROM customer_mappings')
        mapping_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM upload_history')
        history_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM backup_history')
        backup_count = cursor.fetchone()[0]
        
        # Get database size
        db_size = os.path.getsize(self.db_path)
        
        conn.close()
        
        return {
            'customer_mappings': mapping_count,
            'upload_history': history_count,
            'backup_history': backup_count,
            'database_size': db_size
        }
    
    def save_customer_mapping(self, customer_name, field_mappings, api_credentials):
        """Save or update customer mapping configuration"""
        # Input validation
        if not customer_name or not isinstance(customer_name, str):
            raise ValueError("Invalid customer name")
        if len(customer_name) > 100:
            raise ValueError("Customer name too long")
        if not field_mappings or not isinstance(field_mappings, dict):
            raise ValueError("Invalid field mappings")
        if not api_credentials or not isinstance(api_credentials, dict):
            raise ValueError("Invalid API credentials")
        
        # Sanitize customer name
        import re
        safe_customer_name = re.sub(r'[^\w\s-]', '', customer_name.strip())[:100]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Encrypt API credentials
            key = self._get_encryption_key()
            f = Fernet(key)
            
            # Validate API credentials structure before encrypting
            required_cred_fields = ['base_url', 'api_key']
            if not all(field in api_credentials for field in required_cred_fields):
                raise ValueError("Missing required API credential fields")
            
            encrypted_credentials = f.encrypt(json.dumps(api_credentials).encode())
            
            cursor.execute('''
                INSERT OR REPLACE INTO customer_mappings 
                (customer_name, field_mappings, api_credentials, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (safe_customer_name, json.dumps(field_mappings), encrypted_credentials, datetime.now()))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Error saving customer mapping: {e}")
            raise
        finally:
            conn.close()
    
    def get_customer_mapping(self, customer_name):
        """Retrieve customer mapping configuration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT field_mappings, api_credentials FROM customer_mappings 
            WHERE customer_name = ?
        ''', (customer_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Decrypt API credentials
            key = self._get_encryption_key()
            f = Fernet(key)
            decrypted_credentials = json.loads(f.decrypt(result[1]).decode())
            
            return {
                'field_mappings': json.loads(result[0]),
                'api_credentials': decrypted_credentials
            }
        return None
    
    def delete_customer_mapping(self, customer_name):
        """Delete customer mapping configuration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM customer_mappings WHERE customer_name = ?
        ''', (customer_name,))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    def get_customer_mapping_details(self, customer_name):
        """Get customer mapping metadata (creation/update times, field count, etc.)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT created_at, updated_at, field_mappings FROM customer_mappings 
            WHERE customer_name = ?
        ''', (customer_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            field_mappings = json.loads(result[2])
            return {
                'created_at': result[0],
                'updated_at': result[1],
                'field_count': len(field_mappings),
                'fields': list(field_mappings.keys())
            }
        return None
    
    def save_upload_history(self, brokerage_name, filename, total_records, successful_records, failed_records, error_log):
        """Save upload history record - legacy method updated to use brokerage_name"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO upload_history 
            (brokerage_name, filename, total_records, successful_records, failed_records, error_log)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (brokerage_name, filename, total_records, successful_records, failed_records, error_log))
        
        conn.commit()
        conn.close()
    
    def get_upload_history(self, brokerage_name=None, limit: Optional[int] = 50):
        """Retrieve upload history - legacy method updated to use brokerage_name"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if brokerage_name:
            if limit is None:
                cursor.execute('''
                    SELECT * FROM upload_history 
                    WHERE brokerage_name = ?
                    ORDER BY upload_timestamp DESC
                ''', (brokerage_name,))
            else:
                cursor.execute('''
                    SELECT * FROM upload_history 
                    WHERE brokerage_name = ?
                    ORDER BY upload_timestamp DESC
                    LIMIT ?
                ''', (brokerage_name, limit))
        else:
            if limit is None:
                cursor.execute('''
                    SELECT * FROM upload_history 
                    ORDER BY upload_timestamp DESC
                ''')
            else:
                cursor.execute('''
                    SELECT * FROM upload_history 
                    ORDER BY upload_timestamp DESC
                    LIMIT ?
                ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def _get_encryption_key(self):
        """Get or create encryption key for API credentials"""
        # Try to get key from Streamlit secrets first (for cloud deployment)
        try:
            import streamlit as st
            if 'database' in st.secrets and 'ENCRYPTION_KEY' in st.secrets.database:
                key = st.secrets.database.ENCRYPTION_KEY.encode()
                # Validate the key is the correct format
                if len(key) == 44:  # Fernet key length
                    return key
                else:
                    logging.warning("Invalid encryption key format in secrets")
        except Exception:
            # Streamlit secrets not available or not configured
            pass
        
        # Fall back to local file for development
        key_file = "config/encryption.key"
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    key = f.read()
                # Validate the key is the correct format
                if len(key) == 44:  # Fernet key length
                    return key
                else:
                    logging.warning("Invalid encryption key format, generating new key")
            except Exception as e:
                logging.error(f"Error reading encryption key: {e}")
        
        # Generate new key
        key = Fernet.generate_key()
        os.makedirs("config", exist_ok=True)
        try:
            # Write with restricted permissions
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set file permissions to owner-only (Unix-like systems)
            try:
                import stat
                os.chmod(key_file, stat.S_IRUSR | stat.S_IWUSR)
            except:
                pass  # Windows or permission error
        except Exception as e:
            logging.error(f"Error writing encryption key: {e}")
            raise
        return key 

    def save_brokerage_configuration(self, brokerage_name, configuration_name, field_mappings, api_credentials, file_headers=None, description=None):
        """Save or update brokerage configuration with versioning"""
        # Input validation
        if not brokerage_name or not isinstance(brokerage_name, str):
            raise ValueError("Invalid brokerage name")
        if not configuration_name or not isinstance(configuration_name, str):
            raise ValueError("Invalid configuration name")
        if len(brokerage_name) > 100:
            raise ValueError("Brokerage name too long")
        if field_mappings is None or not isinstance(field_mappings, dict):
            raise ValueError("Invalid field mappings")
        if not api_credentials or not isinstance(api_credentials, dict):
            raise ValueError("Invalid API credentials")
        
        # Sanitize names
        import re
        safe_brokerage_name = re.sub(r'[^\w\s-]', '', brokerage_name.strip())[:100]
        safe_configuration_name = re.sub(r'[^\w\s-]', '', configuration_name.strip())[:100]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Encrypt API credentials
            key = self._get_encryption_key()
            f = Fernet(key)
            
            # Validate API credentials structure before encrypting
            required_cred_fields = ['base_url', 'api_key']
            if not all(field in api_credentials for field in required_cred_fields):
                raise ValueError("Missing required API credential fields")
            
            encrypted_credentials = f.encrypt(json.dumps(api_credentials).encode())
            
            # Check if configuration exists
            cursor.execute('''
                SELECT id, field_mappings, version FROM brokerage_configurations 
                WHERE brokerage_name = ? AND configuration_name = ?
            ''', (safe_brokerage_name, safe_configuration_name))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing configuration (no version increment - update in place)
                config_id, old_mappings, current_version = existing
                
                cursor.execute('''
                    UPDATE brokerage_configurations 
                    SET field_mappings = ?, api_credentials = ?, file_headers = ?, 
                        updated_at = ?, last_used_at = ?, description = ?
                    WHERE id = ?
                ''', (
                    json.dumps(field_mappings), encrypted_credentials, 
                    json.dumps(file_headers) if file_headers else None,
                    datetime.now(), datetime.now(), description, config_id
                ))
                
                # Log configuration change
                self._log_configuration_change(
                    cursor, config_id, 'updated', 
                    f"Configuration updated with new field mappings",
                    old_mappings, json.dumps(field_mappings)
                )
                
            else:
                # Create new configuration
                cursor.execute('''
                    INSERT INTO brokerage_configurations 
                    (brokerage_name, configuration_name, field_mappings, api_credentials, 
                     file_headers, last_used_at, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    safe_brokerage_name, safe_configuration_name, 
                    json.dumps(field_mappings), encrypted_credentials,
                    json.dumps(file_headers) if file_headers else None,
                    datetime.now(), description
                ))
                
                config_id = cursor.lastrowid
                
                # Log configuration creation
                self._log_configuration_change(
                    cursor, config_id, 'created',
                    "New configuration created",
                    None, json.dumps(field_mappings)
                )
            
            conn.commit()
            return config_id
            
        except Exception as e:
            conn.rollback()
            logging.error(f"Error saving brokerage configuration: {e}")
            raise
        finally:
            conn.close()

    def get_brokerage_configurations(self, brokerage_name):
        """Get all configurations for a brokerage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, configuration_name, created_at, updated_at, last_used_at, 
                   version, description, field_mappings, api_credentials
            FROM brokerage_configurations 
            WHERE brokerage_name = ? AND is_active = 1
            ORDER BY last_used_at DESC, updated_at DESC
        ''', (brokerage_name,))
        
        results = cursor.fetchall()
        conn.close()
        
        configurations = []
        for row in results:
            config_id, config_name, created_at, updated_at, last_used_at, version, desc, mappings, creds = row
            
            # Decrypt API credentials
            key = self._get_encryption_key()
            f = Fernet(key)
            decrypted_credentials = json.loads(f.decrypt(creds).decode())
            
            configurations.append({
                'id': config_id,
                'name': config_name,
                'created_at': created_at,
                'updated_at': updated_at,
                'last_used_at': last_used_at,
                'version': version,
                'description': desc,
                'field_mappings': json.loads(mappings),
                'api_credentials': decrypted_credentials,
                'field_count': len(json.loads(mappings))
            })
        
        return configurations

    def get_brokerage_configuration(self, brokerage_name, configuration_name):
        """Get specific brokerage configuration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT field_mappings, api_credentials, file_headers, version, description
            FROM brokerage_configurations 
            WHERE brokerage_name = ? AND configuration_name = ? AND is_active = 1
        ''', (brokerage_name, configuration_name))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            mappings, creds, headers, version, desc = result
            
            # Decrypt API credentials
            key = self._get_encryption_key()
            f = Fernet(key)
            decrypted_credentials = json.loads(f.decrypt(creds).decode())
            
            return {
                'field_mappings': json.loads(mappings),
                'api_credentials': decrypted_credentials,
                'file_headers': json.loads(headers) if headers else None,
                'version': version,
                'description': desc
            }
        return None

    def update_configuration_last_used(self, brokerage_name, configuration_name):
        """Update the last used timestamp for a configuration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE brokerage_configurations 
            SET last_used_at = ?
            WHERE brokerage_name = ? AND configuration_name = ?
        ''', (datetime.now(), brokerage_name, configuration_name))
        
        conn.commit()
        conn.close()

    def get_all_brokerages(self):
        """Get list of all brokerages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT brokerage_name, COUNT(*) as config_count,
                   MAX(last_used_at) as last_used
            FROM brokerage_configurations 
            WHERE is_active = 1
            GROUP BY brokerage_name
            ORDER BY last_used DESC, brokerage_name
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [{'name': row[0], 'config_count': row[1], 'last_used': row[2]} for row in results]

    def save_upload_history_enhanced(self, brokerage_name, configuration_name, filename, 
                                   total_records, successful_records, failed_records, 
                                   error_log, processing_time, file_headers, session_id):
        """Save enhanced upload history with detailed error tracking"""
        
        # Data validation and type conversion to prevent SQLite parameter binding errors
        def safe_convert_to_str(value, default=""):
            """Safely convert value to string"""
            if value is None:
                return default
            if isinstance(value, (str, int, float)):
                return str(value)
            return default
        
        def safe_convert_to_int(value, default=0):
            """Safely convert value to integer"""
            if value is None:
                return default
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                try:
                    return int(float(value))
                except (ValueError, TypeError):
                    return default
            if isinstance(value, dict):
                # Handle case where value is accidentally a dict - extract meaningful value if possible
                if 'value' in value:
                    return safe_convert_to_int(value['value'], default)
                return default
            return default
        
        def safe_convert_to_float(value, default=0.0):
            """Safely convert value to float"""
            if value is None:
                return default
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default
            return default
        
        # Validate and convert all parameters
        brokerage_name = safe_convert_to_str(brokerage_name, "Unknown")
        configuration_name = safe_convert_to_str(configuration_name, "Unknown")
        filename = safe_convert_to_str(filename, "unknown_file.csv")
        total_records = safe_convert_to_int(total_records, 0)
        successful_records = safe_convert_to_int(successful_records, 0)
        failed_records = safe_convert_to_int(failed_records, 0)
        processing_time = safe_convert_to_float(processing_time, 0.0)
        session_id = safe_convert_to_str(session_id, f"session_{datetime.now().isoformat()}")
        
        # Validate integer constraints
        if total_records < 0:
            total_records = 0
        if successful_records < 0:
            successful_records = 0
        if failed_records < 0:
            failed_records = 0
        if processing_time < 0:
            processing_time = 0.0
        
        # Ensure successful + failed doesn't exceed total (logical consistency)
        if successful_records + failed_records > total_records:
            total_records = successful_records + failed_records
        
        # Handle error_log - ensure it's a string (JSON) or None
        if error_log is not None and not isinstance(error_log, str):
            try:
                error_log = json.dumps(error_log)
            except:
                error_log = None
        
        # Handle file_headers - ensure it's properly JSON serialized
        if file_headers is not None:
            try:
                if isinstance(file_headers, str):
                    # Already a string, validate it's valid JSON
                    json.loads(file_headers)
                else:
                    # Convert to JSON string
                    file_headers = json.dumps(file_headers)
            except:
                file_headers = None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO upload_history 
            (brokerage_name, configuration_name, filename, total_records, 
             successful_records, failed_records, error_log, processing_time_seconds,
             file_headers, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            brokerage_name, configuration_name, filename, total_records,
            successful_records, failed_records, error_log, processing_time,
            file_headers, session_id
        ))
        
        upload_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return upload_id

    def save_processing_errors(self, upload_history_id, errors_list):
        """Save detailed processing errors for troubleshooting"""
        
        # Validate upload_history_id
        if not isinstance(upload_history_id, int) or upload_history_id <= 0:
            logging.error(f"Invalid upload_history_id: {upload_history_id}")
            return
        
        # Validate errors_list
        if not errors_list or not isinstance(errors_list, list):
            logging.warning("No errors provided or invalid errors_list format")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        def safe_convert_to_str(value, default=""):
            """Safely convert value to string"""
            if value is None:
                return default
            if isinstance(value, (str, int, float)):
                return str(value)
            if isinstance(value, dict):
                return str(value)
            return default
        
        def safe_convert_to_int(value, default=None):
            """Safely convert value to integer"""
            if value is None:
                return default
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                try:
                    return int(float(value))
                except (ValueError, TypeError):
                    return default
            return default
        
        for error in errors_list:
            # Validate that error is a dictionary
            if not isinstance(error, dict):
                logging.warning(f"Skipping invalid error record: {error}")
                continue
            
            # Extract and validate error fields
            row_number = safe_convert_to_int(error.get('row_number'))
            field_name = safe_convert_to_str(error.get('field_name'))
            error_type = safe_convert_to_str(error.get('error_type'))
            error_message = safe_convert_to_str(error.get('error_message'))
            suggested_fix = safe_convert_to_str(error.get('suggested_fix'))
            original_value = safe_convert_to_str(error.get('original_value'))
            expected_format = safe_convert_to_str(error.get('expected_format'))
            
            # Skip if essential fields are missing
            if not error_type or not error_message:
                logging.warning(f"Skipping error record with missing essential fields: {error}")
                continue
            
            cursor.execute('''
                INSERT INTO processing_errors 
                (upload_history_id, row_number, field_name, error_type, 
                 error_message, suggested_fix, original_value, expected_format)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                upload_history_id,
                row_number,
                field_name,
                error_type,
                error_message,
                suggested_fix,
                original_value,
                expected_format
            ))
        
        conn.commit()
        conn.close()

    def get_brokerage_upload_history(self, brokerage_name, limit=50):
        """Get upload history for a specific brokerage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT h.*, COUNT(e.id) as error_count
            FROM upload_history h
            LEFT JOIN processing_errors e ON h.id = e.upload_history_id
            WHERE h.brokerage_name = ?
            GROUP BY h.id
            ORDER BY h.upload_timestamp DESC
            LIMIT ?
        ''', (brokerage_name, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return results

    def _log_configuration_change(self, cursor, config_id, change_type, description, old_value, new_value):
        """Log configuration changes for version tracking"""
        cursor.execute('''
            INSERT INTO configuration_changes 
            (configuration_id, change_type, change_description, old_value, new_value)
            VALUES (?, ?, ?, ?, ?)
        ''', (config_id, change_type, description, old_value, new_value))

    def compare_file_headers(self, saved_headers, current_headers):
        """Compare saved configuration headers with current file headers"""
        if not saved_headers:
            return {'status': 'new_config', 'changes': [], 'missing': [], 'added': current_headers}
        
        saved_set = set(saved_headers)
        current_set = set(current_headers)
        
        missing = list(saved_set - current_set)  # In saved but not in current
        added = list(current_set - saved_set)    # In current but not in saved
        common = list(saved_set & current_set)   # In both
        
        status = 'identical' if not missing and not added else 'changed'
        
        return {
            'status': status,
            'missing': missing,
            'added': added,
            'common': common,
            'changes': missing + added
        } 

    def _migrate_database_schema(self, conn, cursor):
        """Migrate database schema from old format to new format"""
        try:
            # Check if upload_history table has old schema (customer_name instead of brokerage_name)
            cursor.execute("PRAGMA table_info(upload_history)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'customer_name' in column_names and 'brokerage_name' not in column_names:
                logging.info("Migrating upload_history table from customer_name to brokerage_name schema...")
                
                # Create new table with correct schema
                cursor.execute('''
                    CREATE TABLE upload_history_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        brokerage_name TEXT NOT NULL,
                        configuration_name TEXT,
                        filename TEXT NOT NULL,
                        total_records INTEGER,
                        successful_records INTEGER,
                        failed_records INTEGER,
                        error_log TEXT,
                        processing_time_seconds REAL,
                        file_headers TEXT,
                        upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        session_id TEXT
                    )
                ''')
                
                # Copy data from old table to new table (customer_name -> brokerage_name)
                cursor.execute('''
                    INSERT INTO upload_history_new 
                    (id, brokerage_name, filename, total_records, successful_records, 
                     failed_records, error_log, upload_timestamp)
                    SELECT id, customer_name, filename, total_records, successful_records,
                           failed_records, error_log, upload_timestamp
                    FROM upload_history
                ''')
                
                # Drop old table and rename new table
                cursor.execute('DROP TABLE upload_history')
                cursor.execute('ALTER TABLE upload_history_new RENAME TO upload_history')
                
                logging.info("Successfully migrated upload_history table schema")
                
        except Exception as e:
            logging.error(f"Error during database migration: {e}")
            # Don't raise error - let the app continue with what it has 