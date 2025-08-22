#!/usr/bin/env python3

import sys
sys.path.append('.')
sys.path.append('./backend')

from celery_tasks.data_processing import get_sync_db
from sqlalchemy import text

def check_aspect_scores():
    try:
        db = get_sync_db()
        result = db.execute(text('SELECT student_id, aspect_1_score, aspect_2_score, aspect_3_score, course_id FROM surveys LIMIT 10'))
        
        print('Current aspect scores in database:')
        print('=' * 50)
        for row in result:
            print(f'Student: {row[0]}, Course: {row[4]}, Aspect1: {row[1]}, Aspect2: {row[2]}, Aspect3: {row[3]}')
            
        # Also check for any patterns in the data
        result2 = db.execute(text('SELECT COUNT(*) as count, aspect_1_score, aspect_2_score, aspect_3_score FROM surveys GROUP BY aspect_1_score, aspect_2_score, aspect_3_score ORDER BY count DESC LIMIT 5'))
        print('\nMost common aspect score combinations:')
        print('=' * 50)
        for row in result2:
            print(f'Count: {row[0]}, Aspect1: {row[1]}, Aspect2: {row[2]}, Aspect3: {row[3]}')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    check_aspect_scores()