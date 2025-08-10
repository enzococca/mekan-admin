"""
API Routes for Archaeological Data - Correct Structure
Handles MEKAN entities: Birin, Wall, Grave, Finds with media
"""

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required
import psycopg2
from psycopg2.extras import RealDictCursor
import json

api_arch = Blueprint('api_arch', __name__, url_prefix='/api/v2')

def get_db():
    """Get database connection to Supabase"""
    return psycopg2.connect(
        host=current_app.config.get('host', 'aws-0-eu-central-1.pooler.supabase.com'),
        port=current_app.config.get('port', 5432),
        database=current_app.config.get('database', 'postgres'),
        user=current_app.config.get('user', 'postgres.ctlqtgwyuknxpkssidcd'),
        password=current_app.config.get('password', '6pRZELCQUoGFIcf')
    )

# ============= MEKAN BIRIN (Stratigraphic Units) =============
@api_arch.route('/birin', methods=['GET'])
@login_required
def get_birin_units():
    """Get MEKAN Birin units (stratigraphic units)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    year = request.args.get('year')
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT 
                b.birin_uuid,
                b.su_uuid,
                b.birin_no,
                b.birin_type,
                b.description,
                b.description_tr,
                b.koordinat_x,
                b.koordinat_y,
                b.koordinat_z,
                b.dimensions,
                b.preservation_state,
                b.excavation_date,
                b.excavated_by,
                b.created_at,
                ST_AsGeoJSON(b.geom) as geometry,
                s.mekan_year,
                s.mekan_alan,
                s.mekan_acma,
                s.mekan_no
            FROM mekan_birin b
            LEFT JOIN strat_unit s ON b.su_uuid = s.su_uuid
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (b.birin_no::text ILIKE %s OR b.description ILIKE %s OR b.birin_type ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if year:
            query += " AND s.mekan_year = %s"
            params.append(year)
            
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query}) as t"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += " ORDER BY b.created_at DESC LIMIT %s OFFSET %s"
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

# ============= MEKAN WALL =============
@api_arch.route('/walls', methods=['GET'])
@login_required
def get_walls():
    """Get MEKAN Wall data"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    year = request.args.get('year')
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT 
                w.wall_uuid,
                w.wall_no,
                w.wall_year,
                w.wall_alan,
                w.wall_acma,
                w.description,
                w.description_tr,
                w.wall_type,
                w.wall_thickness_cm,
                w.wall_height_cm,
                w.wall_length_m,
                w.construction_technique,
                w.material,
                w.preservation_state,
                w.created_at,
                ST_AsGeoJSON(w.geometry) as geometry
            FROM mekan_wall w
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (w.wall_no ILIKE %s OR w.description ILIKE %s OR w.wall_type ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if year:
            query += " AND w.wall_year = %s"
            params.append(year)
            
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query}) as t"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += " ORDER BY w.wall_year DESC NULLS LAST, w.wall_no LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        walls = cursor.fetchall()
        
        # Add MEKAN relationship for each wall
        for wall in walls:
            if wall.get('wall_year') and wall.get('wall_alan'):
                cursor.execute("""
                    SELECT mekan_no FROM strat_unit 
                    WHERE mekan_year = %s AND mekan_alan = %s
                    LIMIT 1
                """, (wall['wall_year'], wall['wall_alan']))
                result = cursor.fetchone()
                if result:
                    wall['mekan_no'] = result['mekan_no']
        
        # Convert geometry
        for wall in walls:
            if wall.get('geometry'):
                wall['geometry'] = json.loads(wall['geometry'])
        
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

# ============= MEKAN GRAVE =============
@api_arch.route('/graves', methods=['GET'])
@login_required
def get_graves():
    """Get MEKAN Grave data"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    year = request.args.get('year')
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT 
                g.grave_uuid,
                g.grave_no,
                g.grave_year,
                g.grave_alan,
                g.grave_acma,
                g.grave_type,
                g.grave_subtype,
                g.description,
                g.description_tr,
                g.individual_count,
                g.burial_type,
                g.orientation,
                g.preservation_state,
                g.grave_goods,
                g.created_at,
                ST_AsGeoJSON(g.geometry) as geometry,
                s.mekan_no
            FROM mekan_grave g
            LEFT JOIN strat_unit s ON g.su_uuid = s.su_uuid
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (g.grave_no::text ILIKE %s OR g.description ILIKE %s OR g.grave_type ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if year:
            query += " AND g.grave_year = %s"
            params.append(year)
            
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query}) as t"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += " ORDER BY g.grave_year DESC, g.grave_no DESC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        graves = cursor.fetchall()
        
        # Convert geometry
        for grave in graves:
            if grave.get('geometry'):
                grave['geometry'] = json.loads(grave['geometry'])
        
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

# ============= FINDS (Correct Structure) =============
@api_arch.route('/finds', methods=['GET'])
@login_required
def get_finds():
    """Get Finds with correct structure"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    material = request.args.get('material')
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT 
                f.id,
                f.su_uuid,
                f.find_number,
                f.material_type,
                f.material_type_tr,
                f.description,
                f.description_tr,
                f.quantity,
                f.weight_g,
                f.dimensions,
                f.preservation_state,
                f.discovery_date,
                f.registered_by,
                f.created_at,
                ST_AsGeoJSON(f.geometry) as geometry,
                s.mekan_no,
                s.mekan_year,
                s.mekan_alan
            FROM finds f
            LEFT JOIN strat_unit s ON f.su_uuid = s.su_uuid
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (f.find_number::text ILIKE %s OR f.description ILIKE %s OR f.material_type ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if material:
            query += " AND f.material_type = %s"
            params.append(material)
            
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query}) as t"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += " ORDER BY f.created_at DESC LIMIT %s OFFSET %s"
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

# ============= MEDIA/PHOTOS =============
@api_arch.route('/media/<entity_type>/<entity_id>', methods=['GET'])
@login_required
def get_entity_media(entity_type, entity_id):
    """Get media files for an entity"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Query media table for entity
        query = """
            SELECT 
                id,
                entity_type,
                entity_id,
                file_name,
                file_path,
                file_url,
                file_type,
                file_size,
                description,
                uploaded_by,
                created_at
            FROM media
            WHERE entity_type = %s AND entity_id = %s
            ORDER BY created_at DESC
        """
        
        cursor.execute(query, (entity_type, entity_id))
        media_files = cursor.fetchall()
        
        # Get Supabase storage URLs if available
        for media in media_files:
            if media.get('file_path'):
                # Construct Supabase storage URL
                media['public_url'] = f"https://sbtpbadebhycqugsgglv.supabase.co/storage/v1/object/public/{media['file_path']}"
        
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

# ============= SPATIAL DATA =============
@api_arch.route('/spatial/all', methods=['GET'])
@login_required
def get_all_spatial():
    """Get all spatial features for map visualization"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        features = []
        
        # Get Birin units with geometry
        cursor.execute("""
            SELECT 
                'birin' as layer,
                birin_uuid as id,
                birin_no as label,
                birin_type,
                description,
                ST_AsGeoJSON(ST_Transform(geom, 4326)) as geometry
            FROM mekan_birin
            WHERE geom IS NOT NULL
        """)
        for row in cursor.fetchall():
            if row['geometry']:
                features.append({
                    'type': 'Feature',
                    'properties': {
                        'layer': row['layer'],
                        'id': str(row['id']),
                        'label': f"Birin {row['label']}",
                        'type': row['birin_type'],
                        'description': row['description']
                    },
                    'geometry': json.loads(row['geometry'])
                })
        
        # Get Walls with geometry
        cursor.execute("""
            SELECT 
                'wall' as layer,
                wall_uuid as id,
                wall_no as label,
                wall_type,
                description,
                ST_AsGeoJSON(ST_Transform(geometry, 4326)) as geometry
            FROM mekan_wall
            WHERE geometry IS NOT NULL
        """)
        for row in cursor.fetchall():
            if row['geometry']:
                features.append({
                    'type': 'Feature',
                    'properties': {
                        'layer': row['layer'],
                        'id': str(row['id']),
                        'label': f"Wall {row['label']}",
                        'type': row['wall_type'],
                        'description': row['description']
                    },
                    'geometry': json.loads(row['geometry'])
                })
        
        # Get Graves with geometry
        cursor.execute("""
            SELECT 
                'grave' as layer,
                grave_uuid as id,
                grave_no as label,
                grave_type,
                description,
                ST_AsGeoJSON(ST_Transform(geometry, 4326)) as geometry
            FROM mekan_grave
            WHERE geometry IS NOT NULL
        """)
        for row in cursor.fetchall():
            if row['geometry']:
                features.append({
                    'type': 'Feature',
                    'properties': {
                        'layer': row['layer'],
                        'id': str(row['id']),
                        'label': f"Grave {row['label']}",
                        'type': row['grave_type'],
                        'description': row['description']
                    },
                    'geometry': json.loads(row['geometry'])
                })
        
        # Get Finds with geometry
        cursor.execute("""
            SELECT 
                'find' as layer,
                id,
                find_number as label,
                material_type,
                description,
                ST_AsGeoJSON(ST_Transform(geometry, 4326)) as geometry
            FROM finds
            WHERE geometry IS NOT NULL
            LIMIT 500
        """)
        for row in cursor.fetchall():
            if row['geometry']:
                features.append({
                    'type': 'Feature',
                    'properties': {
                        'layer': row['layer'],
                        'id': str(row['id']),
                        'label': f"Find {row['label']}",
                        'material': row['material_type'],
                        'description': row['description']
                    },
                    'geometry': json.loads(row['geometry'])
                })
        
        return jsonify({
            'type': 'FeatureCollection',
            'features': features,
            'total': len(features)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============= RELATIONSHIP COUNTS =============
@api_arch.route('/relationships/<mekan_no>', methods=['GET'])
@login_required
def get_relationships(mekan_no):
    """Get accurate relationship counts for a MEKAN"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get MEKAN year and area for matching
        cursor.execute("""
            SELECT mekan_year, mekan_alan 
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
            # Count Birim units
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
            
            # Count Finds
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

# ============= STATISTICS =============
@api_arch.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """Get comprehensive statistics"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        stats = {}
        
        # Total counts
        cursor.execute("SELECT COUNT(*) as count FROM mekan_birin")
        stats['total_birin'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM mekan_wall")
        stats['total_walls'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM mekan_grave")
        stats['total_graves'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM finds")
        stats['total_finds'] = cursor.fetchone()['count']
        
        # Birin by type
        cursor.execute("""
            SELECT birin_type, COUNT(*) as count
            FROM mekan_birin
            WHERE birin_type IS NOT NULL
            GROUP BY birin_type
            ORDER BY count DESC
        """)
        stats['birin_by_type'] = cursor.fetchall()
        
        # Finds by material
        cursor.execute("""
            SELECT material_type, COUNT(*) as count
            FROM finds
            WHERE material_type IS NOT NULL
            GROUP BY material_type
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['finds_by_material'] = cursor.fetchall()
        
        # Excavation years
        cursor.execute("""
            SELECT DISTINCT mekan_year as year
            FROM strat_unit
            WHERE mekan_year IS NOT NULL
            ORDER BY mekan_year DESC
        """)
        stats['excavation_years'] = [row['year'] for row in cursor.fetchall()]
        
        # Media count
        cursor.execute("SELECT COUNT(*) as count FROM media")
        stats['total_media'] = cursor.fetchone()['count']
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()