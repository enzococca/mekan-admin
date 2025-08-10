#!/usr/bin/env python3
"""Test detail API endpoints"""

from app import app
import json

with app.test_client() as client:
    # Login
    login_resp = client.post('/login', data={'username': 'admin', 'password': 'admin123'})
    print('Login status:', login_resp.status_code)
    
    # Get a sample MEKAN first
    response = client.get('/api/v3/mekan?page=1&per_page=1')
    print('\nGet MEKAN list:', response.status_code)
    
    if response.status_code == 200:
        data = response.get_json()
        if data['data'] and len(data['data']) > 0:
            mekan = data['data'][0]
            mekan_no = mekan['mekan_no']
            print(f'Found MEKAN: {mekan_no}')
            
            # Now test searching for this specific MEKAN
            search_resp = client.get(f'/api/v3/mekan?search={mekan_no}')
            print(f'\nSearch for MEKAN {mekan_no}:', search_resp.status_code)
            if search_resp.status_code != 200:
                print('Error:', search_resp.data.decode())
            else:
                search_data = search_resp.get_json()
                print(f'Search returned {search_data["total"]} results')
                
            # Test media endpoint
            media_resp = client.get(f'/api/v3/media/mekan/{mekan_no}')
            print(f'\nMedia for MEKAN {mekan_no}:', media_resp.status_code)
            if media_resp.status_code != 200:
                print('Error:', media_resp.data.decode())
                
            # Test relationships
            rel_resp = client.get(f'/api/v3/relationships/{mekan_no}')
            print(f'\nRelationships for MEKAN {mekan_no}:', rel_resp.status_code)
            if rel_resp.status_code != 200:
                print('Error:', rel_resp.data.decode())
    else:
        print('Error getting MEKAN list:', response.data.decode())
        
    # Test Birim
    print('\n--- Testing Birim ---')
    birim_resp = client.get('/api/v3/birim?page=1&per_page=1')
    print('Get Birim list:', birim_resp.status_code)
    if birim_resp.status_code == 200:
        data = birim_resp.get_json()
        if data['data'] and len(data['data']) > 0:
            birim = data['data'][0]
            birim_no = birim['birin_no']
            print(f'Found Birim: {birim_no}')
            
            # Search for this Birim
            search_resp = client.get(f'/api/v3/birim?search={birim_no}')
            print(f'Search for Birim {birim_no}:', search_resp.status_code)
            if search_resp.status_code != 200:
                print('Error:', search_resp.data.decode())