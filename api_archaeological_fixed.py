"""
API Routes for Archaeological Data - Fixed with Correct Tables
Handles MEKAN entities with correct table names
"""

from flask import Blueprint, jsonify, request, current_app, send_file
from flask_login import login_required
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import io
from datetime import datetime

api_arch_fixed = Blueprint('api_arch_fixed', __name__, url_prefix='/api/v3')

def get_db():
    """Get database connection to Supabase"""
    return psycopg2.connect(
        host=current_app.config.get('host', 'aws-0-eu-central-1.pooler.supabase.com'),
        port=current_app.config.get('port', 5432),
        database=current_app.config.get('database', 'postgres'),
        user=current_app.config.get('user', 'postgres.ctlqtgwyuknxpkssidcd'),
        password=current_app.config.get('password', '6pRZELCQUoGFIcf')
    )

# ============= MEKAN (Strat Units) =============
@api_arch_fixed.route('/mekan', methods=['GET'])
@login_required
def get_mekan_units():
    """Get MEKAN units from strat_unit table"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT 
                su_uuid,
                mekan_no,
                mekan_year,
                mekan_alan,
                mekan_acma,
                mekan_type,
                mekan_plankare,
                mekan_tabaka,
                description,
                description_tr,
                mekan_koordinat_x as koordinat_x,
                mekan_koordinat_y as koordinat_y,
                mekan_koordinat_z as koordinat_z,
                created_at,
                ST_AsGeoJSON(geom) as geometry
            FROM strat_unit
            WHERE 1=1
        """
        params = []
        
        if search:
            # Try exact match first for numeric searches
            try:
                search_int = int(search)
                query += " AND (mekan_no = %s OR description ILIKE %s OR mekan_alan ILIKE %s)"
                params.extend([search_int, f'%{search}%', f'%{search}%'])
            except ValueError:
                # Not a number, use ILIKE for all fields
                query += " AND (mekan_no::text ILIKE %s OR description ILIKE %s OR mekan_alan ILIKE %s)"
                params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
            
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query}) as t"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination and order
        query += " ORDER BY mekan_year DESC NULLS LAST, mekan_no NULLS LAST LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        units = cursor.fetchall()
        
        # Log for debugging
        print(f"MEKAN Query executed: {query}")
        print(f"Params: {params}")
        print(f"Found {len(units)} MEKAN units")
        
        # Convert geometry and check for media
        for unit in units:
            if unit.get('geometry'):
                unit['geometry'] = json.loads(unit['geometry'])
            
            # Check if has media
            cursor.execute("""
                SELECT COUNT(*) as count FROM media 
                WHERE su_uuid = %s
            """, (unit['su_uuid'],))
            unit['has_media'] = cursor.fetchone()['count'] > 0
        
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

# ============= BIRIM =============
@api_arch_fixed.route('/birim', methods=['GET'])
@login_required
def get_birim_units():
    """Get Birim units from mekan_birin table"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT 
                b.birin_uuid,
                b.birin_no,
                b.birin_type,
                b.description,
                b.description_tr,
                b.koordinat_x,
                b.koordinat_y,
                b.koordinat_z,
                b.dimensions,
                b.preservation_state,
                b.created_at,
                s.mekan_no,
                s.mekan_year,
                s.mekan_alan,
                ST_AsGeoJSON(b.geom) as geometry
            FROM mekan_birin b
            LEFT JOIN strat_unit s ON b.su_uuid = s.su_uuid
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (b.birin_no::text ILIKE %s OR b.description ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
            
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query}) as t"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += " ORDER BY b.created_at DESC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        units = cursor.fetchall()
        
        # Convert geometry and check media
        for unit in units:
            if unit.get('geometry'):
                unit['geometry'] = json.loads(unit['geometry'])
            
            # Check for media
            cursor.execute("""
                SELECT COUNT(*) as count FROM media 
                WHERE birin_uuid = %s
            """, (unit['birin_uuid'],))
            unit['has_media'] = cursor.fetchone()['count'] > 0
        
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

# ============= WALLS =============
@api_arch_fixed.route('/walls', methods=['GET'])
@login_required
def get_walls():
    """Get Wall data from mekan_wall table"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT 
                w.*,
                ST_AsGeoJSON(w.geom) as geometry
            FROM mekan_wall w
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (w.wall_no ILIKE %s OR w.description ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
            
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query}) as t"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += " ORDER BY w.wall_year DESC NULLS LAST, w.wall_no LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        walls = cursor.fetchall()
        
        # Process each wall
        for wall in walls:
            if wall.get('geometry'):
                wall['geometry'] = json.loads(wall['geometry'])
            
            # Get parent MEKAN
            if wall.get('wall_year') and wall.get('wall_alan'):
                cursor.execute("""
                    SELECT mekan_no FROM strat_unit 
                    WHERE mekan_year = %s AND mekan_alan = %s
                    LIMIT 1
                """, (wall['wall_year'], wall['wall_alan']))
                result = cursor.fetchone()
                if result:
                    wall['mekan_no'] = result['mekan_no']
            
            # Check for media
            cursor.execute("""
                SELECT COUNT(*) as count FROM media 
                WHERE wall_uuid = %s
            """, (wall['wall_uuid'],))
            wall['has_media'] = cursor.fetchone()['count'] > 0
        
        return jsonify({
            'data': walls,
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

# ============= GRAVES =============
@api_arch_fixed.route('/graves', methods=['GET'])
@login_required
def get_graves():
    """Get Grave data from mekan_grave table"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT 
                g.*,
                s.mekan_no,
                ST_AsGeoJSON(g.geom) as geometry
            FROM mekan_grave g
            LEFT JOIN strat_unit s ON g.su_uuid = s.su_uuid
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (g.grave_no::text ILIKE %s OR g.description ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
            
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query}) as t"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += " ORDER BY g.grave_year DESC NULLS LAST, g.grave_no DESC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        graves = cursor.fetchall()
        
        # Process each grave
        for grave in graves:
            if grave.get('geometry'):
                grave['geometry'] = json.loads(grave['geometry'])
            
            # Check for media
            cursor.execute("""
                SELECT COUNT(*) as count FROM media 
                WHERE grave_uuid = %s
            """, (grave.get('grave_uuid'),))
            grave['has_media'] = cursor.fetchone()['count'] > 0
        
        return jsonify({
            'data': graves,
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

# ============= FINDS (BULUNTU) =============
@api_arch_fixed.route('/finds', methods=['GET'])
@login_required
def get_finds():
    """Get Finds data from mekan_buluntu table"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # First check if mekan_buluntu exists, otherwise use finds
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'mekan_buluntu'
            )
        """)
        use_buluntu = cursor.fetchone()['exists']
        
        if use_buluntu:
            query = """
                SELECT 
                    b.*,
                    s.mekan_no,
                    s.mekan_year,
                    s.mekan_alan,
                    ST_AsGeoJSON(b.geom) as geometry
                FROM mekan_buluntu b
                LEFT JOIN strat_unit s ON b.su_uuid = s.su_uuid
                WHERE 1=1
            """
            id_field = 'bul_no'
        else:
            query = """
                SELECT 
                    f.*,
                    s.mekan_no,
                    s.mekan_year,
                    s.mekan_alan,
                    ST_AsGeoJSON(f.geometry) as geometry
                FROM finds f
                LEFT JOIN strat_unit s ON f.su_uuid = s.su_uuid
                WHERE 1=1
            """
            id_field = 'find_number'
        
        params = []
        
        if search:
            if use_buluntu:
                query += f" AND (b.aciklama ILIKE %s OR b.malzemesi ILIKE %s)"
            else:
                query += f" AND (f.description ILIKE %s OR f.material_type ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
            
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query}) as t"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        finds = cursor.fetchall()
        
        # Process each find
        for find in finds:
            if find.get('geometry'):
                find['geometry'] = json.loads(find['geometry'])
            
            # Check for media
            if use_buluntu:
                cursor.execute("""
                    SELECT COUNT(*) as count FROM media 
                    WHERE su_uuid = %s OR birin_uuid = %s
                """, (find.get('su_uuid'), find.get('birin_uuid')))
            else:
                cursor.execute("""
                    SELECT COUNT(*) as count FROM media 
                    WHERE find_id = %s
                """, (find.get('find_id'),))
            find['has_media'] = cursor.fetchone()['count'] > 0
        
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

# ============= RELATIONSHIPS =============
@api_arch_fixed.route('/relationships/<mekan_no>', methods=['GET'])
@login_required
def get_relationships(mekan_no):
    """Get accurate relationship counts for a MEKAN"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get MEKAN details
        cursor.execute("""
            SELECT mekan_year, mekan_alan, su_uuid 
            FROM strat_unit 
            WHERE mekan_no = %s
            LIMIT 1
        """, (mekan_no,))
        mekan = cursor.fetchone()
        
        counts = {
            'birim': 0,
            'walls': 0,
            'graves': 0,
            'finds': 0
        }
        
        if mekan:
            # Count Birim
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM mekan_birin b
                JOIN strat_unit s ON b.su_uuid = s.su_uuid
                WHERE s.mekan_no = %s
            """, (mekan_no,))
            counts['birim'] = cursor.fetchone()['count']
            
            # Count Walls
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM mekan_wall
                WHERE wall_year = %s AND wall_alan = %s
            """, (mekan['mekan_year'], mekan['mekan_alan']))
            counts['walls'] = cursor.fetchone()['count']
            
            # Count Graves
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM mekan_grave
                WHERE grave_year = %s AND grave_alan = %s
            """, (mekan['mekan_year'], mekan['mekan_alan']))
            counts['graves'] = cursor.fetchone()['count']
            
            # Count Finds (check both tables)
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'mekan_buluntu'
                )
            """)
            if cursor.fetchone()['exists']:
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM mekan_buluntu b
                    JOIN strat_unit s ON b.su_uuid = s.su_uuid
                    WHERE s.mekan_no = %s
                """, (mekan_no,))
            else:
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM finds f
                    JOIN strat_unit s ON f.su_uuid = s.su_uuid
                    WHERE s.mekan_no = %s
                """, (mekan_no,))
            counts['finds'] = cursor.fetchone()['count']
        
        return jsonify(counts)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============= MEDIA =============
@api_arch_fixed.route('/media/<entity_type>/<entity_id>', methods=['GET'])
@login_required
def get_entity_media(entity_type, entity_id):
    """Get media files for an entity"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Build query based on entity type
        if entity_type == 'mekan':
            # Get UUID for the mekan (mekan_no can be integer or string)
            try:
                cursor.execute("SELECT su_uuid FROM strat_unit WHERE mekan_no::text = %s", (str(entity_id),))
            except:
                cursor.execute("SELECT su_uuid FROM strat_unit WHERE mekan_no = %s", (entity_id,))
            result = cursor.fetchone()
            if result:
                query = """
                    SELECT id, filename, original_filename, file_url, description, 
                           media_type, created_at, photographer, date_taken
                    FROM media 
                    WHERE su_uuid = %s
                    ORDER BY created_at DESC
                """
                params = (result['su_uuid'],)
            else:
                return jsonify({'entity_type': entity_type, 'entity_id': entity_id, 'media': [], 'total': 0})
                
        elif entity_type == 'birim':
            # Get UUID for the birim
            cursor.execute("SELECT birin_uuid FROM mekan_birin WHERE birin_no::text = %s", (entity_id,))
            result = cursor.fetchone()
            if result:
                query = """
                    SELECT id, filename, original_filename, file_url, description,
                           media_type, created_at, photographer, date_taken
                    FROM media 
                    WHERE birin_uuid = %s
                    ORDER BY created_at DESC
                """
                params = (result['birin_uuid'],)
            else:
                return jsonify({'entity_type': entity_type, 'entity_id': entity_id, 'media': [], 'total': 0})
                
        elif entity_type == 'wall':
            # Get UUID for the wall
            cursor.execute("SELECT wall_uuid FROM mekan_wall WHERE wall_no = %s", (entity_id,))
            result = cursor.fetchone()
            if result:
                query = """
                    SELECT id, filename, original_filename, file_url, description,
                           media_type, created_at, photographer, date_taken
                    FROM media 
                    WHERE wall_uuid = %s
                    ORDER BY created_at DESC
                """
                params = (result['wall_uuid'],)
            else:
                return jsonify({'entity_type': entity_type, 'entity_id': entity_id, 'media': [], 'total': 0})
                
        elif entity_type == 'grave':
            # Get UUID for the grave
            cursor.execute("SELECT grave_uuid FROM mekan_grave WHERE grave_no::text = %s", (entity_id,))
            result = cursor.fetchone()
            if result:
                query = """
                    SELECT id, filename, original_filename, file_url, description,
                           media_type, created_at, photographer, date_taken
                    FROM media 
                    WHERE grave_uuid = %s
                    ORDER BY created_at DESC
                """
                params = (result['grave_uuid'],)
            else:
                return jsonify({'entity_type': entity_type, 'entity_id': entity_id, 'media': [], 'total': 0})
                
        elif entity_type == 'find':
            # Check if using mekan_buluntu or finds table
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'mekan_buluntu'
                )
            """)
            if cursor.fetchone()['exists']:
                # Get UUID for the buluntu
                cursor.execute("SELECT su_uuid, birin_uuid FROM mekan_buluntu WHERE bul_no::text = %s", (entity_id,))
                result = cursor.fetchone()
                if result:
                    query = """
                        SELECT id, filename, original_filename, file_url, description,
                               media_type, created_at, photographer, date_taken
                        FROM media 
                        WHERE su_uuid = %s OR birin_uuid = %s
                        ORDER BY created_at DESC
                    """
                    params = (result['su_uuid'], result['birin_uuid'])
                else:
                    return jsonify({'entity_type': entity_type, 'entity_id': entity_id, 'media': [], 'total': 0})
            else:
                # Use finds table
                cursor.execute("SELECT find_id FROM finds WHERE find_number::text = %s", (entity_id,))
                result = cursor.fetchone()
                if result:
                    query = """
                        SELECT id, filename, original_filename, file_url, description,
                               media_type, created_at, photographer, date_taken
                        FROM media 
                        WHERE find_id = %s
                        ORDER BY created_at DESC
                    """
                    params = (result['find_id'],)
                else:
                    return jsonify({'entity_type': entity_type, 'entity_id': entity_id, 'media': [], 'total': 0})
        else:
            return jsonify({'error': 'Invalid entity type'}), 400
            
        cursor.execute(query, params)
        media_files = cursor.fetchall()
        
        # Construct URLs for each media file
        for media in media_files:
            # Use the file_url from database if available (it has the complete path)
            if media.get('file_url'):
                media['public_url'] = media['file_url']
            elif media.get('filename'):
                # Fallback: construct URL from filename
                # The files are stored in the mekan-media bucket on Supabase
                # Try to guess the path structure based on entity type
                if entity_type == 'mekan':
                    # Format: mekan/YYYY/filename
                    media['public_url'] = f"https://ctlqtgwyuknxpkssidcd.supabase.co/storage/v1/object/public/mekan-media/mekan/2025/{media['filename']}"
                elif entity_type == 'grave':
                    media['public_url'] = f"https://ctlqtgwyuknxpkssidcd.supabase.co/storage/v1/object/public/mekan-media/grave/2025/{media['filename']}"
                else:
                    # Generic path
                    media['public_url'] = f"https://ctlqtgwyuknxpkssidcd.supabase.co/storage/v1/object/public/mekan-media/{media['filename']}"
            else:
                media['public_url'] = None
            
            # Add display name
            media['display_name'] = media.get('original_filename') or media.get('filename') or 'Unnamed file'
        
        return jsonify({
            'entity_type': entity_type,
            'entity_id': entity_id,  
            'media': media_files,
            'total': len(media_files)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============= EXPORT TO EXCEL =============
@api_arch_fixed.route('/export/<entity_type>/excel', methods=['GET'])
@login_required
def export_to_excel(entity_type):
    """Export entity data to Excel"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get data based on entity type
        if entity_type == 'mekan':
            query = "SELECT * FROM strat_unit ORDER BY mekan_year DESC, mekan_no"
        elif entity_type == 'birim':
            query = """
                SELECT b.*, s.mekan_no, s.mekan_year, s.mekan_alan
                FROM mekan_birin b
                LEFT JOIN strat_unit s ON b.su_uuid = s.su_uuid
                ORDER BY b.created_at DESC
            """
        elif entity_type == 'walls':
            query = "SELECT * FROM mekan_wall ORDER BY wall_year DESC, wall_no"
        elif entity_type == 'graves':
            query = """
                SELECT g.*, s.mekan_no
                FROM mekan_grave g
                LEFT JOIN strat_unit s ON g.su_uuid = s.su_uuid
                ORDER BY g.grave_year DESC, g.grave_no
            """
        elif entity_type == 'finds':
            # Check which table to use
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'mekan_buluntu'
                )
            """)
            if cursor.fetchone()['exists']:
                query = """
                    SELECT b.*, s.mekan_no, s.mekan_year
                    FROM mekan_buluntu b
                    LEFT JOIN strat_unit s ON b.su_uuid = s.su_uuid
                    ORDER BY b.created_at DESC
                """
            else:
                query = """
                    SELECT f.*, s.mekan_no, s.mekan_year
                    FROM finds f
                    LEFT JOIN strat_unit s ON f.su_uuid = s.su_uuid
                    ORDER BY f.created_at DESC
                """
        else:
            return jsonify({'error': 'Invalid entity type'}), 400
        
        # Create DataFrame
        df = pd.read_sql_query(query, conn)
        
        # Remove geometry columns for Excel export
        geometry_cols = [col for col in df.columns if 'geom' in col.lower()]
        df = df.drop(columns=geometry_cols, errors='ignore')
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name=entity_type.capitalize(), index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets[entity_type.capitalize()]
            for i, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, min(max_len, 50))
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{entity_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============= EXPORT TO PDF =============
@api_arch_fixed.route('/export/<entity_type>/<entity_id>/pdf', methods=['GET'])
@login_required
def export_to_pdf(entity_type, entity_id):
    """Export single entity record to PDF"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get entity data
        if entity_type == 'mekan':
            cursor.execute("SELECT * FROM strat_unit WHERE mekan_no = %s", (entity_id,))
        elif entity_type == 'birim':
            cursor.execute("""
                SELECT b.*, s.mekan_no, s.mekan_year
                FROM mekan_birin b
                LEFT JOIN strat_unit s ON b.su_uuid = s.su_uuid
                WHERE b.birin_no::text = %s
            """, (entity_id,))
        elif entity_type == 'wall':
            cursor.execute("SELECT * FROM mekan_wall WHERE wall_no = %s", (entity_id,))
        elif entity_type == 'grave':
            cursor.execute("""
                SELECT g.*, s.mekan_no
                FROM mekan_grave g
                LEFT JOIN strat_unit s ON g.su_uuid = s.su_uuid
                WHERE g.grave_no::text = %s
            """, (entity_id,))
        elif entity_type == 'find':
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'mekan_buluntu'
                )
            """)
            if cursor.fetchone()['exists']:
                cursor.execute("""
                    SELECT b.*, s.mekan_no
                    FROM mekan_buluntu b
                    LEFT JOIN strat_unit s ON b.su_uuid = s.su_uuid
                    WHERE b.buluntu_no::text = %s
                """, (entity_id,))
            else:
                cursor.execute("""
                    SELECT f.*, s.mekan_no
                    FROM finds f
                    LEFT JOIN strat_unit s ON f.su_uuid = s.su_uuid
                    WHERE f.find_number::text = %s
                """, (entity_id,))
        else:
            return jsonify({'error': 'Invalid entity type'}), 400
        
        record = cursor.fetchone()
        if not record:
            return jsonify({'error': 'Record not found'}), 404
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(f"{entity_type.upper()} - {entity_id}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 0.2*inch))
        
        # Create data table
        data = []
        for key, value in record.items():
            if key not in ['geometry', 'geom'] and value is not None:
                # Format field names
                field_name = key.replace('_', ' ').title()
                data.append([field_name, str(value)])
        
        if data:
            table = Table(data, colWidths=[2.5*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(table)
        
        # Add timestamp
        story.append(Spacer(1, 0.5*inch))
        timestamp = Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
            styles['Normal']
        )
        story.append(timestamp)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{entity_type}_{entity_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============= TEST ENDPOINT =============
@api_arch_fixed.route('/test', methods=['GET'])
@login_required
def test_data():
    """Test endpoint to verify data access"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        test_results = {}
        
        # Test MEKAN query
        cursor.execute("SELECT COUNT(*) as count FROM strat_unit")
        test_results['mekan_count'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT mekan_no, mekan_year, mekan_alan FROM strat_unit LIMIT 5")
        test_results['mekan_sample'] = cursor.fetchall()
        
        # Test Walls query
        cursor.execute("SELECT COUNT(*) as count FROM mekan_wall")
        test_results['wall_count'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT wall_no, wall_year, wall_alan FROM mekan_wall LIMIT 5")
        test_results['wall_sample'] = cursor.fetchall()
        
        # Test Graves query
        cursor.execute("SELECT COUNT(*) as count FROM mekan_grave")
        test_results['grave_count'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT grave_no, grave_year, grave_alan FROM mekan_grave LIMIT 5")
        test_results['grave_sample'] = cursor.fetchall()
        
        return jsonify(test_results)
        
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': str(e.__traceback__)}), 500
    finally:
        cursor.close()
        conn.close()

# ============= STATISTICS =============
@api_arch_fixed.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """Get accurate statistics"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        stats = {}
        
        # Count MEKAN units
        cursor.execute("SELECT COUNT(*) as count FROM strat_unit")
        stats['total_mekan'] = cursor.fetchone()['count']
        
        # Count Birim
        cursor.execute("SELECT COUNT(*) as count FROM mekan_birin")
        stats['total_birim'] = cursor.fetchone()['count']
        
        # Count Walls
        cursor.execute("SELECT COUNT(*) as count FROM mekan_wall")
        stats['total_walls'] = cursor.fetchone()['count']
        
        # Count Graves
        cursor.execute("SELECT COUNT(*) as count FROM mekan_grave")
        stats['total_graves'] = cursor.fetchone()['count']
        
        # Count Finds
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'mekan_buluntu'
            )
        """)
        if cursor.fetchone()['exists']:
            cursor.execute("SELECT COUNT(*) as count FROM mekan_buluntu")
        else:
            cursor.execute("SELECT COUNT(*) as count FROM finds")
        stats['total_finds'] = cursor.fetchone()['count']
        
        # Media count
        cursor.execute("SELECT COUNT(*) as count FROM media")
        stats['total_media'] = cursor.fetchone()['count']
        
        # Years
        cursor.execute("""
            SELECT DISTINCT mekan_year as year
            FROM strat_unit
            WHERE mekan_year IS NOT NULL
            ORDER BY mekan_year DESC
        """)
        stats['excavation_years'] = [row['year'] for row in cursor.fetchall()]
        
        # Birim by type
        cursor.execute("""
            SELECT birin_type, COUNT(*) as count
            FROM mekan_birin
            WHERE birin_type IS NOT NULL
            GROUP BY birin_type
            ORDER BY count DESC
        """)
        stats['birim_by_type'] = cursor.fetchall()
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()