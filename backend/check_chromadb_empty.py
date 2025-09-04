import asyncio
from vector_store import get_chroma_manager

async def check_collections():
    manager = get_chroma_manager()
    
    # Check survey data collection
    try:
        survey_count = len(await manager.search_survey_data('test'))
        print(f'Survey documents: {survey_count}')
    except Exception as e:
        print(f'Error checking survey collection: {e}')
    
    # Check student data collection
    try:
        student_count = len(await manager.search_student_data('test'))
        print(f'Student documents: {student_count}')
    except Exception as e:
        print(f'Error checking student collection: {e}')
    
    # Check chat history collection
    try:
        chat_count = len(await manager.search_chat_history('test'))
        print(f'Chat history documents: {chat_count}')
    except Exception as e:
        print(f'Error checking chat history collection: {e}')

if __name__ == '__main__':
    asyncio.run(check_collections())