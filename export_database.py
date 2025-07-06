#!/usr/bin/env python3
"""
Database Export Script
Exports current database data to SQL files for backup or migration
"""

import asyncio
import asyncpg
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def export_database():
    """Export all database data to SQL files"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to database")
        
        # Get timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export each table
        tables = [
            'protected_roles',
            'role_assignments', 
            'command_usage',
            'bot_statistics',
            'error_logs',
            'guild_settings'
        ]
        
        for table in tables:
            try:
                # Get table data
                rows = await conn.fetch(f'SELECT * FROM {table}')
                
                if rows:
                    # Create SQL export file
                    filename = f"{table}_export_{timestamp}.sql"
                    with open(filename, 'w') as f:
                        f.write(f"-- Export of {table} table\n")
                        f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        
                        # Get column names
                        columns = list(rows[0].keys())
                        columns_str = ', '.join(columns)
                        
                        f.write(f"-- Clear existing data (uncomment if needed)\n")
                        f.write(f"-- DELETE FROM {table};\n\n")
                        
                        # Write INSERT statements
                        f.write(f"INSERT INTO {table} ({columns_str}) VALUES\n")
                        
                        for i, row in enumerate(rows):
                            values = []
                            for col in columns:
                                value = row[col]
                                if value is None:
                                    values.append('NULL')
                                elif isinstance(value, str):
                                    # Escape single quotes
                                    escaped = value.replace("'", "''")
                                    values.append(f"'{escaped}'")
                                elif isinstance(value, bool):
                                    values.append('TRUE' if value else 'FALSE')
                                elif isinstance(value, datetime):
                                    values.append(f"'{value.isoformat()}'")
                                else:
                                    values.append(str(value))
                            
                            values_str = ', '.join(values)
                            comma = ',' if i < len(rows) - 1 else ';'
                            f.write(f"({values_str}){comma}\n")
                        
                        f.write(f"\n-- {len(rows)} rows exported\n")
                    
                    print(f"✅ Exported {len(rows)} rows from {table} to {filename}")
                else:
                    print(f"ℹ️  Table {table} is empty")
                    
            except Exception as e:
                print(f"❌ Error exporting {table}: {e}")
        
        # Create a combined export file
        combined_filename = f"full_database_export_{timestamp}.sql"
        with open(combined_filename, 'w') as f:
            f.write(f"-- Full Database Export\n")
            f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Include schema
            f.write("-- Database Schema\n")
            with open('database_schema.sql', 'r') as schema_file:
                f.write(schema_file.read())
            f.write("\n\n")
            
            # Include all table exports
            for table in tables:
                export_file = f"{table}_export_{timestamp}.sql"
                if os.path.exists(export_file):
                    f.write(f"-- Data for {table}\n")
                    with open(export_file, 'r') as table_file:
                        content = table_file.read()
                        # Skip the header comments
                        lines = content.split('\n')
                        data_lines = []
                        skip_header = True
                        for line in lines:
                            if skip_header and (line.startswith('INSERT') or line.startswith('-- Clear')):
                                skip_header = False
                            if not skip_header:
                                data_lines.append(line)
                        f.write('\n'.join(data_lines))
                    f.write("\n\n")
        
        print(f"✅ Created combined export: {combined_filename}")
        
        # Database statistics
        print("\n📊 Database Statistics:")
        for table in tables:
            try:
                count = await conn.fetchval(f'SELECT COUNT(*) FROM {table}')
                print(f"  {table}: {count} rows")
            except Exception as e:
                print(f"  {table}: Error getting count - {e}")
        
        await conn.close()
        print("✅ Database export completed successfully")
        
    except Exception as e:
        print(f"❌ Database export failed: {e}")

if __name__ == "__main__":
    asyncio.run(export_database())