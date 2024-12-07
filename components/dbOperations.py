from supabase import create_client
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from settings import SUPABASE_URL, SUPABASE_KEY

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Courses Series Operations
def create_course_series(unique_id: str, title: str, description: str = None, pic: str = None, source: str = None, owner: str = None, face:str =None) -> Dict:
    """Create a new course series"""
    data = {
        'unique_id': unique_id,
        'title': title,
        'description': description,
        'pic': pic,
        'source': source,
        'owner': owner,
        'face': face
    }
    return supabase.table('courses_series').insert(data).execute().data[0]

def get_course_series(series_id: str = None, unique_id: str = None) -> List[Dict]:
    """Get course series by id or unique_id"""
    query = supabase.table('courses_series').select()
    if series_id:
        query = query.eq('series_id', series_id)
    if unique_id:
        query = query.eq('unique_id', unique_id)
    return query.execute().data

def update_course_series(series_id: str, data: Dict) -> Dict:
    """Update course series"""
    data['updated_at'] = datetime.now().isoformat()
    return supabase.table('courses_series').update(data).eq('series_id', series_id).execute().data[0]

def delete_course_series(series_id: str) -> Dict:
    """Delete course series"""
    return supabase.table('courses_series').delete().eq('series_id', series_id).execute().data[0]

# Course Parts Operations
def create_course_part(series_id: str, title: str, page: str = None, subtitle: str = None,
                      default_note: str = None, status: int = 0) -> Dict:
    """Create a new course part"""
    data = {
        'series_id': series_id,
        'title': title,
        'page': page,
        'subtitle': subtitle,
        'default_note': default_note,
        'status': status
    }
    return supabase.table('course_parts').insert(data).execute().data[0]

def get_course_parts(part_id: str = None, series_id: str = None) -> List[Dict]:
    """Get course parts by id or series_id"""
    query = supabase.table('course_parts').select()
    if part_id:
        query = query.eq('part_id', part_id)
    if series_id:
        query = query.eq('series_id', series_id)
    return query.execute().data

def update_course_part(part_id: str, data: Dict) -> Dict:
    """Update course part"""
    data['updated_at'] = datetime.now().isoformat()
    return supabase.table('course_parts').update(data).eq('part_id', part_id).execute().data[0]

def delete_course_part(part_id: str) -> Dict:
    """Delete course part"""
    return supabase.table('course_parts').delete().eq('part_id', part_id).execute().data[0]

# Notes Operations
def create_note(user_id: str, part_id: str, content: str) -> Dict:
    """Create a new note"""
    data = {
        'user_id': user_id,
        'part_id': part_id,
        'content': content
    }
    return supabase.table('notes').insert(data).execute().data[0]

def get_notes(note_id: int = None, user_id: str = None, part_id: str = None) -> List[Dict]:
    """Get notes by various parameters"""
    query = supabase.table('notes').select()
    if note_id:
        query = query.eq('note_id', note_id)
    if user_id:
        query = query.eq('user_id', user_id)
    if part_id:
        query = query.eq('part_id', part_id)
    return query.execute().data

def update_note(note_id: int, content: str) -> Dict:
    """Update note content"""
    data = {
        'content': content,
        'updated_at': datetime.now().isoformat()
    }
    return supabase.table('notes').update(data).eq('note_id', note_id).execute().data[0]

def delete_note(note_id: int) -> Dict:
    """Delete note"""
    return supabase.table('notes').delete().eq('note_id', note_id).execute().data[0]

# Quiz Operations
def create_quiz(part_id: str, question_text: str, answer_options: str, 
                correct_answer: str) -> Dict:
    """Create a new quiz"""
    data = {
        'part_id': part_id,
        'question_text': question_text,
        'answer_options': answer_options,
        'correct_answer': correct_answer
    }
    return supabase.table('quiz').insert(data).execute().data[0]

def get_quizzes(quiz_id: int = None, part_id: str = None) -> List[Dict]:
    """Get quizzes by various parameters"""
    query = supabase.table('quiz').select()
    if quiz_id:
        query = query.eq('quiz_id', quiz_id)
    if part_id:
        query = query.eq('part_id', part_id)
    return query.execute().data

def update_quiz(quiz_id: int, data: Dict) -> Dict:
    """Update quiz"""
    data['updated_at'] = datetime.now().isoformat()
    return supabase.table('quiz').update(data).eq('quiz_id', quiz_id).execute().data[0]

def delete_quiz(quiz_id: int) -> Dict:
    """Delete quiz"""
    return supabase.table('quiz').delete().eq('quiz_id', quiz_id).execute().data[0]

# User Watching History Operations
def create_watching_history(user_id: str, part_id: str, progress: float) -> Dict:
    """Create or update watching history"""
    data = {
        'user_id': user_id,
        'part_id': part_id,
        'progress': progress,
        'watched_at': datetime.now().isoformat()
    }
    # First try to update existing record
    existing = get_watching_history(user_id=user_id, part_id=part_id)
    if existing:
        return update_watching_history(existing[0]['history_id'], data)
    # If no existing record, create new one
    return supabase.table('user_watching_history').insert(data).execute().data[0]

def get_watching_history(history_id: int = None, user_id: str = None, 
                        part_id: str = None) -> List[Dict]:
    """Get watching history by various parameters"""
    query = supabase.table('user_watching_history').select()
    if history_id:
        query = query.eq('history_id', history_id)
    if user_id:
        query = query.eq('user_id', user_id)
    if part_id:
        query = query.eq('part_id', part_id)
    return query.execute().data

def update_watching_history(history_id: int, data: Dict) -> Dict:
    """Update watching history"""
    data['updated_at'] = datetime.now().isoformat()
    return supabase.table('user_watching_history').update(data).eq('history_id', history_id).execute().data[0]

def delete_watching_history(history_id: int) -> Dict:
    """Delete watching history"""
    return supabase.table('user_watching_history').delete().eq('history_id', history_id).execute().data[0]

# User Favorites Operations
def create_favorite(user_id: str, series_id: str) -> Dict:
    """Create a new favorite"""
    data = {
        'user_id': user_id,
        'series_id': series_id,
        'favorited_at': datetime.now().isoformat()
    }
    return supabase.table('user_favorites').insert(data).execute().data[0]

def get_favorites(favorite_id: int = None, user_id: str = None, 
                 series_id: str = None) -> List[Dict]:
    """Get favorites by various parameters"""
    query = supabase.table('user_favorites').select()
    if favorite_id:
        query = query.eq('favorite_id', favorite_id)
    if user_id:
        query = query.eq('user_id', user_id)
    if series_id:
        query = query.eq('series_id', series_id)
    return query.execute().data

def delete_favorite(favorite_id: int) -> Dict:
    """Delete favorite"""
    return supabase.table('user_favorites').delete().eq('favorite_id', favorite_id).execute().data[0] 