from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Student, Schedule,StudentFile
from datetime import time
from typing import Optional


async def orm_add_student(session: AsyncSession, data: dict):
    student = Student(
        name=data["name"],
        umk=data["umk"],
        lesson_link=data["lesson_link"],
        cost=data["cost"],
        tg_id=data["tg_id"],
        file_umk=data.get("files", [{}])[0].get("file_name") if data.get("files") else None,
        balance=0
    )
    # Добавляем файлы, если они были загружены
    for file_data in data.get("files", []):
        student_file = StudentFile(
            file_name=file_data["file_name"],
            file_path=file_data["file_path"]
        )
        student.files.append(student_file)
    
    session.add(student)
    await session.commit()


async def get_files(student_id, session:AsyncSession):
    query = select(StudentFile.file_path).where(StudentFile.student_id == student_id)
    result = await session.execute(query)
    files_list = result.scalars().all()
    return files_list
    
    
async def get_students(session: AsyncSession):
    query = select(Student).order_by(Student.name)
    result  = await session.execute(query)
    return result.scalars().all()


async def get_student_link(session: AsyncSession, student_id):
    query = select(Student.lesson_link).where(Student.id == student_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_delete_student(session: AsyncSession, student_id: int):
    """Безопасное удаление ученика и связанных записей"""
    try:
        async with session.begin():
            # 1. Удаляем связанные уроки в расписании
            await session.execute(
                delete(Schedule).where(Schedule.student_id == student_id)
            )
            # 2. Удаляем самого ученика
            result = await session.execute(
                delete(Student).where(Student.id == student_id)
            )
            # 3. Проверяем что ученик существовал
            if result.rowcount == 0:
                raise ValueError("Ученик не найден")
            
        return True
    except Exception as e:
        await session.rollback()
        logger.error(f"Ошибка удаления ученика {student_id}: {e}")
        raise
    
    
async def orm_update_student(session:AsyncSession, student_name:str, field:str, value:str):
    result = await session.execute(
        update(Student).where(Student.name==student_name).values(**{field: value})
    )
    await session.commit()
    return result
    

async def orm_get_balance(session: AsyncSession, student_name: str) -> int:
    result = await session.execute(
        select(Student.balance).where(Student.name == student_name)
    )
    return result.scalar_one()

async def orm_plus_lesson(session: AsyncSession, student_name: str, operation: str):
    student = await session.execute(
        select(Student).where(Student.name == student_name)
    )
    student = student.scalar_one()
    
    if operation == "+":
        student.balance += 1
    elif operation == "-":
        student.balance -= 1
        
    await session.commit()


async def create_lesson(
    session: AsyncSession,
    day_of_week: int,
    start_time: time,
    student_id: int,
    duration: int
) -> Schedule:
    new_lesson = Schedule(
        day_of_week=day_of_week,
        start_time=start_time,
        student_id=student_id,
        duration=duration
    )
    
    existing = await session.execute(
    select(Schedule).where(
        Schedule.day_of_week == day_of_week,
        Schedule.start_time == start_time,
        Schedule.student_id == student_id
    )
)
    if existing.scalar():
        raise ValueError("Урок уже существует")
    
    
    session.add(new_lesson)
    await session.commit()
    return new_lesson
    
    
async def get_lessons(session:AsyncSession):
    query = select(Schedule, Student.name).join(Student, Schedule.student_id == Student.id).order_by(Schedule.day_of_week, Schedule.start_time)
    
    result = await session.execute(query)
    await session.commit()
    return result.all()
    
async def delete_lesson(session: AsyncSession, lesson_id: int) -> bool:
    result = await session.execute(
        delete(Schedule).where(Schedule.id == lesson_id)
    )
    await session.commit()
    return result.rowcount > 0
    
# Исправленная функция get_student_by_id
async def get_student_by_id(session: AsyncSession, student_id: int) -> Optional[Student]:
    """Возвращает ученика по ID или None, если не найден."""
    try:
        result = await session.execute(select(Student).where(Student.id == student_id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Ошибка при получении ученика {student_id}: {e}")
        return None
        
        
async def orm_update_balance(session: AsyncSession, student_id: int, operation: str) -> bool:
    try:
        student = await get_student_by_id(session, student_id)
        if not student:
            return False
            
        if operation == "+":
            student.balance += 1
        elif operation == "-":
            if student.balance > 0:
                student.balance -= 1
        await session.commit()
        return True
    except Exception as e:
        logger.error(f"Balance update error: {e}")
        await session.rollback()
        return False
        
        
