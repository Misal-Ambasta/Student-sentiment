#!/usr/bin/env python3
"""
Analyze response format line by line
"""

import requests
import json

def analyze_response_format():
    """Analyze the response format line by line"""
    try:
        response = requests.post('http://localhost:8000/api/chat/query', json={
            'query': 'Analyze student fsd25_08010',
            'response_format': 'individual_analysis',
            'auto_classify': 'false',
            'student_id': 'fsd25_08010'
        })
        
        if response.status_code == 200:
            data = response.json()
            content = data['response']['content']
            lines = content.split('\n')
            
            print("=== LINE BY LINE ANALYSIS ===")
            for i, line in enumerate(lines[:15]):
                print(f"Line {i}: {repr(line)}")
                
            print("\n=== STUDENT PROFILE SECTION ANALYSIS ===")
            # Find the STUDENT PROFILE section
            profile_start = -1
            for i, line in enumerate(lines):
                if 'STUDENT PROFILE' in line:
                    profile_start = i
                    break
                    
            if profile_start >= 0:
                print(f"STUDENT PROFILE found at line {profile_start}")
                # Show the next 5 lines after STUDENT PROFILE
                for i in range(profile_start, min(profile_start + 6, len(lines))):
                    print(f"  Line {i}: {repr(lines[i])}")
                    
                # Check if there's a line with demographic data
                demographic_line = None
                for i in range(profile_start + 1, min(profile_start + 4, len(lines))):
                    if 'Demographic:' in lines[i] or '|' in lines[i]:
                        demographic_line = lines[i]
                        print(f"\nFound demographic line at {i}: {repr(demographic_line)}")
                        break
                        
                if not demographic_line:
                    print("\n⚠️ No demographic line found after STUDENT PROFILE")
                    print("This explains why frontend shows 'Unknown' values!")
            else:
                print("STUDENT PROFILE section not found")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_response_format()