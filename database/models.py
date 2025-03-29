from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column,relationship
from sqlalchemy import DateTime, Float, String, Text, func, DECIMAL,Integer,ForeignKey, Column,Text
from datetime import date, time


class Base(DeclarativeBase):
    __abstract__ = True  # Делаем базовый класс абстрактным
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())


class Student(Base): 
    __tablename__ = "students"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    umk: Mapped[str]
    lesson_link: Mapped[str]= mapped_column(Text,nullable=True)
    cost: Mapped[int] = mapped_column(nullable=True)
    tg_id: Mapped[str] = mapped_column(nullable=True)
    file_umk: Mapped[str] = mapped_column(Text,nullable=True)
    balance: Mapped[int]
    
    files: Mapped[list["StudentFile"]] = relationship(
        back_populates="student", 
        cascade="all, delete-orphan"
    )
    
    
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="student")

class Schedule(Base):
    __tablename__ = "schedule"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    day_of_week: Mapped[int]  # 0-6 
    start_time: Mapped[time]
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    # Опционально
    duration: Mapped[int] = mapped_column(default=60)  # в минутах
    
    student: Mapped["Student"] = relationship(back_populates="schedules")
    

class StudentFile(Base):  # Исправлено название (ед. число)
    __tablename__ = "student_files"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(nullable=False)
    file_path: Mapped[str] = mapped_column(nullable=False)  # Путь к файлу
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    
    student: Mapped["Student"] = relationship(back_populates="files")
    