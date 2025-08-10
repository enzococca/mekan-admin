"""
Simplified API Routes for Archaeological Data
Works with actual Supabase table structure
"""

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
import psycopg2
from psycopg2.extras import RealDictCursor
import json

api_bp = Blueprint('api', __name__, url_prefix='/api')

def get_db():
    """Get database connection"""
    return psycopg2.connect(
        host=current_app.config.get('host', 'aws-0-eu-central-1.pooler.supabase.com'),
        port=current_app.config.get('port', 5432),
        database=current_app.config.get('database', 'postgres'),
        user=current_app.config.get('user', 'postgres.ctlqtgwyuknxpkssidcd'),
        password=current_app.config.get('password', '6pRZELCQUoGFIcf')
    )

@api_bp.route('/test_connection', methods=['GET'])
@login_required
def test_connection():
    """Test database connection"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return jsonify({'status': 'Connected successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/strat_units', methods=['GET'])
@login_required
def get_strat_units():
    """Get stratigraphic units"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Simple query for strat_unit table
        query = """
            SELECT 
                su_uuid,
                proj_id,
                site_id,
                code,
                std_code,
                description,
                description_tr,
                elevation_m,
                date_from,
                date_to,
                created_at,
                mekan_year,
                mekan_alan,
                mekan_acma,
                mekan_no,
                mekan_type
            FROM strat_unit
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (code ILIKE %s OR description ILIKE %s OR std_code ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
            
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query}) as t"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        units = cursor.fetchall()
        
        return jsonify({
            'data': units,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@api_bp.route('/mekan_units', methods=['GET'])
@login_required
def get_mekan_units():
    """Get MEKAN units"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Query for mekan_birin table
        query = """
            SELECT 
                birin_uuid,
                su_uuid,
                birin_no,
                birin_type,
                description,
                description_tr,
                koordinat_x,
                koordinat_y,
                koordinat_z,
                dimensions,
                preservation_state,
                excavation_date,
                excavated_by,
                created_at,
                ST_AsGeoJSON(geom) as geometry
            FROM mekan_birin
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (birin_no::text ILIKE %s OR description ILIKE %s OR birin_type ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
            
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query}) as t"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        units = cursor.fetchall()
        
        # Convert geometry
        for unit in units:
            if unit.get('geometry'):
                unit['geometry'] = json.loads(unit['geometry'])
        
        return jsonify({
            'data': units,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@api_bp.route('/finds', methods=['GET'])
@login_required
def get_finds():
    """Get finds"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Query for finds table
        query = """
            SELECT 
                find_uuid,
                find_id,
                proj_id,
                site_id,
                catalog_sys,
                catalog_year,
                catalog_number,
                std_code,
                macro_class,
                material,
                description,
                description_tr,
                quantity,
                weight_g,
                dimensions,
                date_from,
                date_to,
                collected_by,
                collected_date,
                created_at,
                ST_AsGeoJSON(geometry) as geometry
            FROM finds
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (find_id ILIKE %s OR description ILIKE %s OR material ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
            
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query}) as t"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        finds = cursor.fetchall()
        
        # Convert geometry
        for find in finds:
            if find.get('geometry'):
                find['geometry'] = json.loads(find['geometry'])
        
        return jsonify({
            'data': finds,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@api_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """Get database statistics"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        stats = {}
        
        # Count strat units
        cursor.execute("SELECT COUNT(*) as count FROM strat_unit")
        stats['total_strat_units'] = cursor.fetchone()['count']
        
        # Count mekan units
        cursor.execute("SELECT COUNT(*) as count FROM mekan_birin")
        stats['total_mekan'] = cursor.fetchone()['count']
        
        # Count finds
        cursor.execute("SELECT COUNT(*) as count FROM finds")
        stats['total_finds'] = cursor.fetchone()['count']
        
        # Count by year for strat_unit
        cursor.execute("""
            SELECT mekan_year as year, COUNT(*) as count
            FROM strat_unit
            WHERE mekan_year IS NOT NULL
            GROUP BY mekan_year
            ORDER BY mekan_year DESC
            LIMIT 10
        """)
        stats['units_by_year'] = cursor.fetchall()
        
        # Count by material for finds
        cursor.execute("""
            SELECT material, COUNT(*) as count
            FROM finds
            WHERE material IS NOT NULL
            GROUP BY material
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['finds_by_material'] = cursor.fetchall()
        
        # Count by type for mekan
        cursor.execute("""
            SELECT birin_type, COUNT(*) as count
            FROM mekan_birin
            WHERE birin_type IS NOT NULL
            GROUP BY birin_type
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['mekan_by_type'] = cursor.fetchall()
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@api_bp.route('/tables', methods=['GET'])
@login_required
def get_tables():
    """List all archaeological tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
            AND (
                table_name LIKE '%mekan%' OR 
                table_name LIKE '%strat%' OR 
                table_name LIKE '%find%' OR
                table_name LIKE '%us_%' OR
                table_name LIKE '%can_%'
            )
            ORDER BY table_name
        """)
        
        tables = []
        for row in cursor.fetchall():
            tables.append({
                'name': row[0],
                'columns': row[1]
            })
        
        return jsonify({'tables': tables})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()