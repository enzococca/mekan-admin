#!/usr/bin/env python3
"""Test API v3 endpoints locally"""

from app import app
from flask_login import login_user
import psycopg2
from psycopg2.extras import RealDictCursor

# Test database connection first
def test_db_connection():
    try:
        conn = psycopg2.connect(
            host='aws-0-eu-central-1.pooler.supabase.com',
            port=5432,
            database='postgres',
            user='postgres.ctlqtgwyuknxpkssidcd',
            password='6pRZELCQUoGFIcf'
        )
        cursor = conn.cursor()
        
        # Test basic queries
        print("Testing database queries:")
        
        # Test strat_unit table
        cursor.execute("SELECT COUNT(*) FROM strat_unit")
        count = cursor.fetchone()[0]
        print(f"  strat_unit count: {count}")
        
        # Test mekan_birin table  
        cursor.execute("SELECT COUNT(*) FROM mekan_birin")
        count = cursor.fetchone()[0]
        print(f"  mekan_birin count: {count}")
        
        # Test mekan_wall table
        cursor.execute("SELECT COUNT(*) FROM mekan_wall")
        count = cursor.fetchone()[0]
        print(f"  mekan_wall count: {count}")
        
        # Test mekan_grave table
        cursor.execute("SELECT COUNT(*) FROM mekan_grave")
        count = cursor.fetchone()[0]
        print(f"  mekan_grave count: {count}")
        
        # Check if mekan_buluntu exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'mekan_buluntu'
            )
        """)
        has_buluntu = cursor.fetchone()[0]
        
        if has_buluntu:
            cursor.execute("SELECT COUNT(*) FROM mekan_buluntu")
            count = cursor.fetchone()[0]
            print(f"  mekan_buluntu count: {count}")
        else:
            cursor.execute("SELECT COUNT(*) FROM finds")
            count = cursor.fetchone()[0]
            print(f"  finds count: {count} (mekan_buluntu not found)")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Database error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("Testing MEKAN Admin API v3")
    print("=" * 50)
    
    # Test database first
    if test_db_connection():
        print("\nDatabase connection OK\n")
        
        # Test API endpoints
        with app.test_client() as client:
            # Login first
            login_response = client.post('/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=True)
            
            print("Testing API v3 endpoints:")
            
            # Test each endpoint
            endpoints = [
                '/api/v3/test',
                '/api/v3/statistics', 
                '/api/v3/mekan?page=1&per_page=5',
                '/api/v3/birim?page=1&per_page=5',
                '/api/v3/walls?page=1&per_page=5',
                '/api/v3/graves?page=1&per_page=5',
                '/api/v3/finds?page=1&per_page=5'
            ]
            
            for endpoint in endpoints:
                response = client.get(endpoint)
                print(f"\n{endpoint}")
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.get_json()
                        if 'total' in data:
                            print(f"  Total records: {data['total']}")
                        elif 'total_mekan' in data:
                            # Statistics endpoint
                            print(f"  MEKAN: {data.get('total_mekan', 0)}")
                            print(f"  Birim: {data.get('total_birim', 0)}")
                            print(f"  Walls: {data.get('total_walls', 0)}")
                            print(f"  Graves: {data.get('total_graves', 0)}")
                            print(f"  Finds: {data.get('total_finds', 0)}")
                    except:
                        print(f"  Response: {response.data[:200]}")
                else:
                    print(f"  Error: {response.data.decode()[:200]}")
    else:
        print("\nDatabase connection failed!")