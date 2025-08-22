import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database import get_db
from sqlalchemy import text

async def check_data():
    async for db in get_db():
        try:
            # Check available course_ids
            result = await db.execute(text('SELECT DISTINCT course_id FROM surveys LIMIT 10'))
            courses = result.fetchall()
            print('Available course_ids:', [row[0] for row in courses])
            
            # Check records for fsd25
            result2 = await db.execute(text("SELECT COUNT(*) FROM surveys WHERE course_id = 'fsd25'"))
            count = result2.scalar()
            print(f'Records for fsd25: {count}')
            
            # Check total records
            result3 = await db.execute(text('SELECT COUNT(*) FROM surveys'))
            total = result3.scalar()
            print(f'Total survey records: {total}')
            
            # Check sample data
            result4 = await db.execute(text('SELECT student_id, course_id, nps_score FROM surveys LIMIT 5'))
            samples = result4.fetchall()
            print('Sample records:')
            for sample in samples:
                print(f'  Student: {sample[0]}, Course: {sample[1]}, NPS: {sample[2]}')
                
        finally:
            await db.close()
        break

if __name__ == "__main__":
    asyncio.run(check_data())