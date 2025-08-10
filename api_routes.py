"""
API Routes for Archaeological Data Management
Provides RESTful endpoints for querying and managing archaeological data
"""

from flask import Blueprint, jsonify, request, send_file, current_app
from flask_login import login_required, current_user
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import pandas as pd
import json
from datetime import datetime
import io
import xlsxwriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

api_bp = Blueprint('api', __name__, url_prefix='/api')

def get_db():
    """Get database connection"""
    return psycopg2.connect(
        host=current_app.config.get('DB_HOST', 'localhost'),
        port=current_app.config.get('DB_PORT', 5433),
        database=current_app.config.get('DB_NAME', 'hybrid_strat'),
        user=current_app.config.get('DB_USER', 'postgres'),
        password=current_app.config.get('DB_PASSWORD', 'postgres')
    )

@api_bp.route('/stratigraphic_units', methods=['GET'])
@login_required
def get_stratigraphic_units():
    """Get all stratigraphic units with filters"""
    # Get query parameters
    site = request.args.get('site')
    area = request.args.get('area')
    year = request.args.get('year')
    unit_type = request.args.get('type')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Build query - using strat_unit table
        query = """
            SELECT 
                id,
                site,
                area,
                us as us_number,
                year,
                definition,
                interpretation,
                period,
                phase,
                dating,
                initial_dating,
                final_dating,
                activity,
                criteria,
                reliability,
                ST_AsGeoJSON(geometry) as geometry,
                created_at,
                updated_at
            FROM strat_unit
            WHERE 1=1
        """
        params = []
        
        if site:
            query += " AND site = %s"
            params.append(site)
        if area:
            query += " AND area = %s"
            params.append(area)
        if year:
            query += " AND year = %s"
            params.append(year)
        if unit_type:
            query += " AND definition = %s"
            params.append(unit_type)
        if search:
            query += " AND (us::text LIKE %s OR interpretation ILIKE %s OR definition ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
            
        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) as t"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += " ORDER BY year DESC, us DESC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        units = cursor.fetchall()
        
        # Convert geometry from string to dict
        for unit in units:
            if unit['geometry']:
                unit['geometry'] = json.loads(unit['geometry'])
        
        return jsonify({
            'data': units,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    finally:
        cursor.close()
        conn.close()

@api_bp.route('/mekan_units', methods=['GET'])
@login_required
def get_mekan_units():
    """Get MEKAN/CAN units"""
    site = request.args.get('site')
    area = request.args.get('area')
    year = request.args.get('year')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT 
                id,
                site,
                area,
                mekan_no,
                can_no,
                year,
                definition,
                description,
                period,
                phase,
                ST_AsGeoJSON(geom) as geometry,
                created_at,
                updated_at
            FROM mekan_birin
            WHERE 1=1
        """
        params = []
        
        if site:
            query += " AND site = %s"
            params.append(site)
        if area:
            query += " AND area = %s"
            params.append(area)
        if year:
            query += " AND year = %s"
            params.append(year)
        if search:
            query += " AND (mekan_no::text LIKE %s OR can_no::text LIKE %s OR description ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
            
        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) as t"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += " ORDER BY year DESC, mekan_no DESC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        units = cursor.fetchall()
        
        # Convert geometry
        for unit in units:
            if unit['geometry']:
                unit['geometry'] = json.loads(unit['geometry'])
        
        return jsonify({
            'data': units,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    finally:
        cursor.close()
        conn.close()

@api_bp.route('/finds', methods=['GET'])
@login_required
def get_finds():
    """Get finds catalog"""
    site = request.args.get('site')
    area = request.args.get('area')
    year = request.args.get('year')
    category = request.args.get('category')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT 
                find_id,
                site,
                area,
                us_number,
                mekan_no,
                find_number,
                year,
                category,
                material,
                description,
                quantity,
                weight,
                dimensions,
                conservation_state,
                dating,
                photo_references,
                notes,
                ST_AsGeoJSON(geom) as geometry,
                created_at,
                updated_at
            FROM finds
            WHERE 1=1
        """
        params = []
        
        if site:
            query += " AND site = %s"
            params.append(site)
        if area:
            query += " AND area = %s"
            params.append(area)
        if year:
            query += " AND year = %s"
            params.append(year)
        if category:
            query += " AND category = %s"
            params.append(category)
        if search:
            query += " AND (find_number::text LIKE %s OR description ILIKE %s OR material ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
            
        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) as t"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += " ORDER BY year DESC, find_number DESC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        finds = cursor.fetchall()
        
        # Convert geometry
        for find in finds:
            if find['geometry']:
                find['geometry'] = json.loads(find['geometry'])
        
        return jsonify({
            'data': finds,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    finally:
        cursor.close()
        conn.close()

@api_bp.route('/relationships', methods=['GET'])
@login_required
def get_relationships():
    """Get stratigraphic relationships"""
    site = request.args.get('site')
    area = request.args.get('area')
    year = request.args.get('year')
    us_number = request.args.get('us_number')
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT 
                r.id,
                r.site,
                r.area,
                r.us_number_1,
                r.us_number_2,
                r.relationship_type,
                r.year,
                r.notes,
                u1.interpretation as us1_interpretation,
                u2.interpretation as us2_interpretation
            FROM stratigraphic_relationships r
            LEFT JOIN stratigraphic_units u1 
                ON r.site = u1.site AND r.area = u1.area 
                AND r.us_number_1 = u1.us_number AND r.year = u1.year
            LEFT JOIN stratigraphic_units u2 
                ON r.site = u2.site AND r.area = u2.area 
                AND r.us_number_2 = u2.us_number AND r.year = u2.year
            WHERE 1=1
        """
        params = []
        
        if site:
            query += " AND r.site = %s"
            params.append(site)
        if area:
            query += " AND r.area = %s"
            params.append(area)
        if year:
            query += " AND r.year = %s"
            params.append(year)
        if us_number:
            query += " AND (r.us_number_1 = %s OR r.us_number_2 = %s)"
            params.extend([us_number, us_number])
            
        query += " ORDER BY r.us_number_1, r.us_number_2"
        
        cursor.execute(query, params)
        relationships = cursor.fetchall()
        
        return jsonify(relationships)
        
    finally:
        cursor.close()
        conn.close()

@api_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """Get archaeological data statistics"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        stats = {}
        
        # US counts by year
        cursor.execute("""
            SELECT year, COUNT(*) as count
            FROM strat_unit
            GROUP BY year
            ORDER BY year DESC
        """)
        stats['us_by_year'] = cursor.fetchall()
        
        # MEKAN counts by year
        cursor.execute("""
            SELECT year, COUNT(*) as count
            FROM mekan_birin
            GROUP BY year
            ORDER BY year DESC
        """)
        stats['mekan_by_year'] = cursor.fetchall()
        
        # Finds by category
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM finds
            GROUP BY category
            ORDER BY count DESC
        """)
        stats['finds_by_category'] = cursor.fetchall()
        
        # US by period
        cursor.execute("""
            SELECT period, COUNT(*) as count
            FROM strat_unit
            WHERE period IS NOT NULL
            GROUP BY period
            ORDER BY count DESC
        """)
        stats['us_by_period'] = cursor.fetchall()
        
        # Total counts
        cursor.execute("SELECT COUNT(*) as count FROM stratigraphic_units")
        stats['total_us'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM mekan_data")
        stats['total_mekan'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM finds_catalog")
        stats['total_finds'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(DISTINCT year) as count FROM stratigraphic_units")
        stats['total_years'] = cursor.fetchone()['count']
        
        return jsonify(stats)
        
    finally:
        cursor.close()
        conn.close()

@api_bp.route('/export/excel', methods=['POST'])
@login_required
def export_excel():
    """Export data to Excel"""
    if not current_user.permissions.get('can_export'):
        return jsonify({'error': 'Permission denied'}), 403
        
    data_type = request.json.get('type', 'us')
    filters = request.json.get('filters', {})
    
    conn = get_db()
    
    try:
        # Get data based on type
        if data_type == 'us':
            query = """
                SELECT * FROM stratigraphic_units
                WHERE 1=1
            """
            params = []
            if filters.get('site'):
                query += " AND site = %s"
                params.append(filters['site'])
            if filters.get('year'):
                query += " AND year = %s"
                params.append(filters['year'])
            if filters.get('area'):
                query += " AND area = %s"
                params.append(filters['area'])
                
            df = pd.read_sql_query(query, conn, params=params)
            
        elif data_type == 'mekan':
            query = """
                SELECT * FROM mekan_data
                WHERE 1=1
            """
            params = []
            if filters.get('site'):
                query += " AND site = %s"
                params.append(filters['site'])
            if filters.get('year'):
                query += " AND year = %s"
                params.append(filters['year'])
                
            df = pd.read_sql_query(query, conn, params=params)
            
        elif data_type == 'finds':
            query = """
                SELECT * FROM finds_catalog
                WHERE 1=1
            """
            params = []
            if filters.get('site'):
                query += " AND site = %s"
                params.append(filters['site'])
            if filters.get('year'):
                query += " AND year = %s"
                params.append(filters['year'])
            if filters.get('category'):
                query += " AND category = %s"
                params.append(filters['category'])
                
            df = pd.read_sql_query(query, conn, params=params)
        else:
            return jsonify({'error': 'Invalid data type'}), 400
            
        # Remove geometry column if present
        if 'geom' in df.columns:
            df = df.drop('geom', axis=1)
            
        # Create Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Data']
            
            # Add formatting
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#366092',
                'font_color': 'white',
                'border': 1
            })
            
            # Write headers with formatting
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
            # Adjust column widths
            for i, col in enumerate(df.columns):
                column_len = df[col].astype(str).map(len).max()
                column_len = max(column_len, len(col))
                worksheet.set_column(i, i, min(column_len + 2, 50))
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{data_type}_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        
    finally:
        conn.close()

@api_bp.route('/export/pdf', methods=['POST'])
@login_required
def export_pdf():
    """Export data to PDF"""
    if not current_user.permissions.get('can_export'):
        return jsonify({'error': 'Permission denied'}), 403
        
    data_type = request.json.get('type', 'us')
    record_id = request.json.get('id')
    
    if not record_id:
        return jsonify({'error': 'Record ID required'}), 400
        
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get data based on type
        if data_type == 'us':
            cursor.execute("""
                SELECT * FROM stratigraphic_units
                WHERE id = %s
            """, (record_id,))
            data = cursor.fetchone()
            title = f"Stratigraphic Unit - US {data['us']}"
            
        elif data_type == 'mekan':
            cursor.execute("""
                SELECT * FROM mekan_data
                WHERE id = %s
            """, (record_id,))
            data = cursor.fetchone()
            title = f"MEKAN Unit - {data['mekan_no']}"
            
        elif data_type == 'find':
            cursor.execute("""
                SELECT * FROM finds_catalog
                WHERE find_id = %s
            """, (record_id,))
            data = cursor.fetchone()
            title = f"Find - {data['find_number']}"
        else:
            return jsonify({'error': 'Invalid data type'}), 400
            
        if not data:
            return jsonify({'error': 'Record not found'}), 404
            
        # Create PDF
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#366092'),
            spaceAfter=30
        )
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Create table data
        table_data = []
        for key, value in data.items():
            if key not in ['geom', 'id', 'id_us', 'find_id']:
                if value is not None:
                    key_formatted = key.replace('_', ' ').title()
                    table_data.append([key_formatted, str(value)])
        
        # Create table
        table = Table(table_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E6E6E6')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(table)
        
        # Build PDF
        doc.build(story)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{data_type}_{record_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
        
    finally:
        cursor.close()
        conn.close()

@api_bp.route('/spatial/features', methods=['GET'])
@login_required
def get_spatial_features():
    """Get spatial features for map visualization"""
    data_type = request.args.get('type', 'all')
    bounds = request.args.get('bounds')
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        features = []
        
        # Parse bounds if provided
        where_clause = ""
        params = []
        if bounds:
            try:
                b = json.loads(bounds)
                where_clause = """
                    AND ST_Intersects(
                        geom,
                        ST_MakeEnvelope(%s, %s, %s, %s, 3997)
                    )
                """
                params = [b['west'], b['south'], b['east'], b['north']]
            except:
                pass
        
        # Get US features
        if data_type in ['all', 'us']:
            query = f"""
                SELECT 
                    'us' as layer,
                    id,
                    us as label,
                    site,
                    area,
                    year,
                    interpretation,
                    period,
                    ST_AsGeoJSON(ST_Transform(geom, 4326)) as geometry
                FROM strat_unit
                WHERE geom IS NOT NULL {where_clause}
            """
            cursor.execute(query, params)
            for row in cursor.fetchall():
                features.append({
                    'type': 'Feature',
                    'properties': {
                        'layer': row['layer'],
                        'id': row['id'],
                        'label': f"US {row['label']}",
                        'site': row['site'],
                        'area': row['area'],
                        'year': row['year'],
                        'interpretation': row['interpretation'],
                        'period': row['period']
                    },
                    'geometry': json.loads(row['geometry']) if row['geometry'] else None
                })
        
        # Get MEKAN features
        if data_type in ['all', 'mekan']:
            query = f"""
                SELECT 
                    'mekan' as layer,
                    id,
                    mekan_no,
                    can_no,
                    site,
                    area,
                    year,
                    description,
                    period,
                    ST_AsGeoJSON(ST_Transform(geom, 4326)) as geometry
                FROM mekan_birin
                WHERE geom IS NOT NULL {where_clause}
            """
            cursor.execute(query, params)
            for row in cursor.fetchall():
                label = f"MEKAN {row['mekan_no']}"
                if row['can_no']:
                    label += f" / CAN {row['can_no']}"
                features.append({
                    'type': 'Feature',
                    'properties': {
                        'layer': row['layer'],
                        'id': row['id'],
                        'label': label,
                        'site': row['site'],
                        'area': row['area'],
                        'year': row['year'],
                        'description': row['description'],
                        'period': row['period']
                    },
                    'geometry': json.loads(row['geometry']) if row['geometry'] else None
                })
        
        # Get finds features
        if data_type in ['all', 'finds']:
            query = f"""
                SELECT 
                    'find' as layer,
                    find_id as id,
                    find_number,
                    site,
                    area,
                    year,
                    category,
                    material,
                    description,
                    ST_AsGeoJSON(ST_Transform(geom, 4326)) as geometry
                FROM finds
                WHERE geom IS NOT NULL {where_clause}
            """
            cursor.execute(query, params)
            for row in cursor.fetchall():
                features.append({
                    'type': 'Feature',
                    'properties': {
                        'layer': row['layer'],
                        'id': row['id'],
                        'label': f"Find {row['find_number']}",
                        'site': row['site'],
                        'area': row['area'],
                        'year': row['year'],
                        'category': row['category'],
                        'material': row['material'],
                        'description': row['description']
                    },
                    'geometry': json.loads(row['geometry']) if row['geometry'] else None
                })
        
        return jsonify({
            'type': 'FeatureCollection',
            'features': features
        })
        
    finally:
        cursor.close()
        conn.close()

@api_bp.route('/search/global', methods=['GET'])
@login_required
def global_search():
    """Global search across all data types"""
    query = request.args.get('q', '')
    if len(query) < 3:
        return jsonify({'results': []})
        
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        results = []
        
        # Search US
        cursor.execute("""
            SELECT 
                'us' as type,
                id,
                CONCAT('US ', us, ' - ', interpretation) as title,
                CONCAT(site, ' / ', area, ' / Year: ', year) as subtitle
            FROM strat_unit
            WHERE 
                us::text ILIKE %s OR
                interpretation ILIKE %s OR
                definition ILIKE %s OR
                period ILIKE %s
            LIMIT 10
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        
        for row in cursor.fetchall():
            results.append(row)
        
        # Search MEKAN
        cursor.execute("""
            SELECT 
                'mekan' as type,
                id,
                CONCAT('MEKAN ', mekan_no, CASE WHEN can_no IS NOT NULL THEN CONCAT(' / CAN ', can_no) ELSE '' END) as title,
                CONCAT(site, ' / ', area, ' / Year: ', year) as subtitle
            FROM mekan_birin
            WHERE 
                mekan_no::text ILIKE %s OR
                can_no::text ILIKE %s OR
                description ILIKE %s OR
                definition ILIKE %s
            LIMIT 10
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        
        for row in cursor.fetchall():
            results.append(row)
        
        # Search finds
        cursor.execute("""
            SELECT 
                'find' as type,
                find_id as id,
                CONCAT('Find ', find_number, ' - ', category) as title,
                CONCAT(material, ' / ', site, ' / Year: ', year) as subtitle
            FROM finds
            WHERE 
                find_number::text ILIKE %s OR
                category ILIKE %s OR
                material ILIKE %s OR
                description ILIKE %s
            LIMIT 10
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        
        for row in cursor.fetchall():
            results.append(row)
        
        return jsonify({'results': results})
        
    finally:
        cursor.close()
        conn.close()