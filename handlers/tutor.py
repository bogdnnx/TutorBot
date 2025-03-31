from aiogram import F, Router,types
from aiogram.types import Message, CallbackQuery,FSInputFile
from aiogram.filters import Command,StateFilter,or_f
from aiogram.fsm.state import StatesGroup,State
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import os
from urllib.parse import quote
from sqlalchemy import select, case
from datetime import time
from aiogram.types import ReplyKeyboardRemove
import re
import logging
from typing import Optional



from filters.chat_types import ChatTypeFilter, IsTutor
from keyboard.reply import get_keyboard
from keyboard.inline import get_callback_btns
from database.orm_query import orm_update_balance, get_student_by_id,orm_delete_student, get_student_link, get_students,orm_update_student, orm_plus_lesson,orm_get_balance, orm_add_student, create_lesson, delete_lesson,get_files, get_lessons
from database.models import Student, Schedule, StudentFile

tutor_router = Router()
tutor_router.message.filter(ChatTypeFilter(["private"]), IsTutor())
logger = logging.getLogger(__name__)

UPLOADS_DIR = "uploads"

INFO = """\n➖Краткий экскурс в функционал бота\n\n➖Здесь ты можешь вести отчетность по занятиям,получать материалы,ссылки на конференции,ссылки на материалы для ученика, расписание занятий и тд\n
🆖🆖🆖Вот основные моменты которые нужно понимать:\n◾️Если ты не хочешь что-либо вводить ты чаще всего можешь поставить -\n◾️Если ты запуталась или не понимаешь чего-то то  нужно ввести команду отмены(об этом ниже)\n
◾️Если возникает какая-либо проблема: бот не работает, бот выдал какую-то ошибку - напиши разработчику(@bogdnnx)\n◾️Если есть какие-либо пожелания или что-то выглядит неудобно - тоже пиши разработчику
\n🆖Вот список доступных на данный момент команд:\n
/tutor - Открытие панели репетитора для дальнейших действий\n
/cancel - Отмена заполнения данных\n
/back - Возврат на предыдущий шаг(если ты что-то добавляешь для ученика)\n
/status - Узнать что ты сейчас вводишь


*** Если возникают любые проблемы/вопросы или пожелания нужно обратиться 💬 к разработчику***\n
"""
TUTOR_KB = get_keyboard(
    "💵Добавить ученика",
    "👥Посмотреть учеников",
    "📅 Расписание",
    placeholder="Выберите действие",
    sizes=(2,1),
)

sheduele_buttons = get_keyboard(
    "📖 Показать расписание",
    "➕ Добавить урок",
    "❌ Удалить урок",
    "В главное меню"
    
)


@tutor_router.message(F.text == "В главное меню")
async def get_main_menu(message, state:FSMContext):
    await message.answer("Вы вернулись в главное меню",reply_markup = TUTOR_KB)
    await state.clear()


class StudentActions(StatesGroup):
    name = State()
    umk = State()
    lesson_link = State()
    cost = State()
    tg_id = State()
    umk_file = State()
    

    state_descriptions = {
        "StudentActions:name": "Ввод имени ученика",
        "StudentActions:umk": "Ввод названия умк",
        "StudentActions:lesson_link": "Ввод ссылки на конференцию",
        "StudentActions:cost": "Ввод стоимости занятия",
        "StudentActions:tg_id": "Ввод Telegram ID ученика",
        "StudentActions:umk_file": "Ввод файла"     
    }

class StudentSelection(StatesGroup):
    choosed_student = State()  # Состояние выбора ученика
    another_actions = State()  # Состояние дополнительных действий
    view_students = State()  # Новое состояние для просмотра списка учеников
    advanced_actions = State()
    
@tutor_router.message(Command("start"))
async def start(message:Message):
    await message.answer("✌️ Это бот репетитора по английскому\n"+INFO, reply_markup=TUTOR_KB)



@tutor_router.message(StateFilter("*"),Command("cancel"))
@tutor_router.message(StateFilter("*"),F.text.casefold() == "отмена")   
async def cancel(message:Message, state:FSMContext):
    await state.clear()
    await message.answer("Заполнение данных отменено",reply_markup=TUTOR_KB)
    
    
@tutor_router.message(Command("status"))
async def get_status(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    
    # Если нет активного состояния
    if not current_state:
        await message.answer("Ты сейчас не в процессе заполнения данных. Всё в порядке! 😊")
        return
    readable_state = StudentActions.state_descriptions.get(current_state, "Неизвестное состояние 🤔")

    await message.answer(f"🔍 Сейчас твой статус: {readable_state}")   
    return current_state
   
@tutor_router.message(StateFilter("*"),Command("back"))
@tutor_router.message(StateFilter("*"),F.text.casefold() == "назад")
async def back(message:Message, state:FSMContext):
    current_state = await state.get_state()
    
    if current_state == StudentActions.name:
        await message.answer("Это первый шаг, вернуться нельзя, можете отменить действия")
        return  
    prev = None
    
    for step in StudentActions.__all_states__:
        if step.state == current_state:
            await state.set_state(prev)
            await message.answer(f"Вы вернулись на предыдущий шаг {StudentActions.state_descriptions[prev.state]}\nКоманду можно отправить несколько раз и вернуться в нужное место")
            return
        prev = step
    
   
   
@tutor_router.message(or_f(Command("tutor"),F.text == "В главное меню"))
async def tutor_begin(message:Message):
    ''' начало работы репетитора с ботом'''
    await message.answer("👩‍🏫Приветсвую, учитель👩‍🏫",reply_markup = TUTOR_KB)
        

@tutor_router.message(F.text == "💵Добавить ученика")
async def set_name(message:Message, state:FSMContext):
    '''запрос фи и установка статуса "ввод имени" '''
    await message.answer("Введите фамилию и имя ученика", reply_markup=types.ReplyKeyboardRemove())   
    await state.set_state(StudentActions.name)   
   
   
@tutor_router.message(StateFilter(StudentActions.name),F.text)
async def set_umk(message:Message, state:FSMContext):
    ''' запрос умк и апдейт словаря именем'''
    await state.update_data(name = message.text)
    await message.answer("Введите Описание/Заметки про учениа\n\n❗️Здесь можно указать удобное для тебя тектовое значение\n\nЛибо можно поставить -")
    await state.set_state(StudentActions.umk)

  
@tutor_router.message(StateFilter(StudentActions.umk), F.text)
async def set_umk_link(message:Message,state: FSMContext):
    '''запрос ссылки на урок и апдейт словаря'''
    await state.update_data(umk = message.text)
    await message.answer("🌐Введите ссылку на конференцию🌐")
    await state.set_state(StudentActions.lesson_link)
    

@tutor_router.message(StateFilter(StudentActions.lesson_link), F.text)
async def set_cost(message:Message,state:FSMContext):
    '''запрос стоимость и апдейст словаря лмнком'''
    await state.update_data(lesson_link = message.text)
    await message.answer("Введите стоимость урока\n‼️Здесь нужно ввести просто целое число, пример: 1500")
    await state.set_state(StudentActions.cost)

@tutor_router.message(StateFilter(StudentActions.cost),F.text)
async def set_tg_id(message:Message,state:FSMContext):
    try:
        await state.update_data(cost = int(message.text))
    except:
        await message.answer("🆖Стоимость урока некорректна🆖\nВведи снова")
        return
    await message.answer("Введите телеграмм id ученика\n‼️Пример:8193157007")
    await state.set_state(StudentActions.tg_id)
    
    
@tutor_router.message(StateFilter(StudentActions.tg_id))
async def set_file(message, state:FSMContext, session: AsyncSession):
    try:
        await state.update_data(tg_id = message.text)
    except:
        await message.answer("🆖Телеграмм ID некорректен🆖\nВведи снова")
        return
    await message.answer("📍Загрузите файл📍\n\n📎Размер не должен превышать 20МБ\nТакже можно ввести -")
    await state.set_state(StudentActions.umk_file)



@tutor_router.message(StateFilter(StudentActions.umk_file), F.document)
async def handle_file(message: Message, state: FSMContext):
    data = await state.get_data()
    # Получаем список файлов, если его ещё нет – создаём
    files = data.get("files", [])
    
    document: Document = message.document  
    file_name = document.file_name
    file_path = os.path.join(UPLOADS_DIR, file_name)
    
    # Скачиваем файл
    await message.bot.download(file=document, destination=file_path)
    
    # Добавляем информацию о файле в список
    files.append({
        "file_name": file_name,
        "file_path": file_path
    })
    
    data["files"] = files
    await state.update_data(data)
    
    await message.answer(f"Файл добавлен. Отправьте ещё или введите '-' для завершения.")

@tutor_router.message(StateFilter(StudentActions.umk_file), F.text == "-")
async def finish_files(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    
    # Если список файлов пуст, можно записать, что файлов нет
    if not data.get("files"):
        data["files"] = []
        await message.answer("Файла у ученика пока нет")
    
    # Остальные данные остаются без изменений:
    student_info = (
        f"Имя: {data['name']}\n"
        f"УМК: {data['umk']}\n"
        f"Ссылка на урок: {data['lesson_link']}\n"
        f"Стоимость урока: {data['cost']}\n"
        f"Телеграм ID ученика: {data['tg_id']}\n"
        f"Файлы УМК: {', '.join(file['file_name'] for file in data.get('files', [])) or 'Нет файла'}"
    )
    
    await message.answer("Заполнение профиля ученика завершено", reply_markup=TUTOR_KB)
    await message.answer_sticker("CAACAgIAAx0Cd0LlaQACAUZn3wfdH3RWW1N8duMCtyzMnmBZMQAC7hQAAuNVUEk4S4qtAhNhvDYE")
    
    # Сохранение данных с учетом нескольких файлов
    await orm_add_student(session, data)
    await state.clear()






# Хэндлер для просмотра всех учеников
@tutor_router.message(F.text == "👥Посмотреть учеников")
async def view_students(message: types.Message, session: AsyncSession, state: FSMContext):
    """Отображает список всех учеников."""
    students = await get_students(session)
    
    if not students:
        await message.answer("В базе данных нет учеников.")
        return

    # Формируем список учеников для вывода
    students_list = "\n\n".join(
        f"{index}🧒. Имя: {student.name}\nОплачено занятий сейчас: {student.balance}" 
        for index, student in enumerate(students, start=1))
    
    # Сохраняем список учеников в состояние
    await state.update_data(students=students)
    await state.set_state(StudentSelection.view_students)  # Устанавливаем состояние просмотра списка
    
    await message.answer(students_list)
    await message.answer("Введите номер ученика, с которым хотите взаимодействовать.")


@tutor_router.message(StateFilter(StudentSelection.view_students), F.text.isdigit())
async def select_student(message: Message, state: FSMContext, session: AsyncSession):
    """Обрабатывает выбор ученика по номеру."""
    data = await state.get_data()
    students = data.get("students", [])
    
    try:
        student_index = int(message.text) - 1
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число.")
        return

    if 0 <= student_index < len(students):
        student = students[student_index]
        
        # Сохраняем ID выбранного ученика
        await state.update_data(
            selected_student_id=student.id,
            selected_student_name=student.name  # Сохраняем имя только для отображения
        )
        await state.set_state(StudentSelection.choosed_student)

        # Формируем сообщение с кнопками, используя ID
        await message.answer(
            f"👤 Имя: {student.name}\n"
            f"📚 Инфа: {student.umk}\n"
            f"💸 Оплачено занятий: {student.balance}",
            reply_markup=get_callback_btns(
                btns={
                    "💸 Баланс": f"checkBalance_{student.id}",
                    "🔗 Ссылка": f"lessonLink_{student.id}", 
                    "📚 Материалы": f"sendfile_{student.id}",
                    "✏️ Изменить": f"edit_{student.id}",
                    "⚙️ Дополнительно": f"additional_{student.id}",
                    "◀️ Назад": "back_to_list"
                },
                sizes=(2, 2, 1)
            )
        )
    else:
        await message.answer("❌ Некорректный номер. Попробуйте снова.")


@tutor_router.callback_query(F.data == "back_to_list")
async def back_to_students_list(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Возвращает к списку учеников с актуальными данными"""
    try:
        await callback.answer()  # Убираем индикатор загрузки на кнопке
        
        # Получаем актуальные данные из БД
        students = await get_students(session)
        if not students:
            await callback.message.edit_text("🎉 Список учеников пуст.")
            await state.clear()
            return

        # Обновляем данные в состоянии
        await state.update_data(students=students)
        await state.set_state(StudentSelection.view_students)

        # Формируем список с ID и именами
        students_list = "\n".join(
            f"{idx}. ID{student.id} | {student.name}"
            for idx, student in enumerate(students, start=1)
        )

        # Редактируем сообщение с новыми данными
        await callback.message.edit_text(
            "📋 Список учеников:\n\n" + students_list + 
            "\n\nВведите номер ученика из списка:",
            reply_markup=get_callback_btns(btns={"◀️ Назад в меню": "main_menu"})
        )

    except Exception as e:
        logger.error(f"Error in back_to_list: {e}")
        await callback.message.answer("❌ Ошибка при загрузке списка.")
        await state.clear()



@tutor_router.callback_query(F.data == "main_menu")
async def handle_main_menu(callback: CallbackQuery, state: FSMContext):
    """Обработчик возврата в главное меню"""
    try:
        await callback.answer()
        await state.clear()
        await callback.message.answer(
            "🏠 Вы вернулись в главное меню:",
            reply_markup=TUTOR_KB
        )
    except Exception as e:
        logger.error(f"Main menu error: {e}")
        await callback.message.answer("❌ Ошибка возврата в меню")


@tutor_router.callback_query(F.data == "back_inline_to_list")
async def back_to_students_list(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Возвращает к списку учеников с актуальными данными"""
    try:
        await callback.answer()
        students = await get_students(session)
        
        if not students:
            await callback.message.edit_text("🎉 Список учеников пуст.")
            await state.clear()
            return

        await state.update_data(students=students)
        await state.set_state(StudentSelection.view_students)

        students_list = "\n".join(
            f"{idx}. ID{student.id} | {student.name}"
            for idx, student in enumerate(students, start=1)
        )

        await callback.message.edit_text(
            "📋 Список учеников:\n\n" + students_list + 
            "\n\nВведите номер ученика из списка:",
            reply_markup=get_callback_btns(
                btns={
                    "◀️ Назад в меню": "main_menu",
                    "🔄 Обновить список": "refresh_list"
                }
            )
        )

    except Exception as e:
        logger.error(f"Error in back_to_list: {e}")
        await callback.message.answer("❌ Ошибка при загрузке списка.")
        await state.clear()

# Добавим также обработчик для кнопки обновления
@tutor_router.callback_query(F.data == "refresh_list")
async def refresh_students_list(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обновляет список учеников"""
    await back_to_students_list(callback, state, session)





@tutor_router.callback_query(F.data.startswith("lessonLink_"))
async def send_link(callback:CallbackQuery, session:AsyncSession):
    student_id = int(callback.data.split("_")[-1])
    link = await get_student_link(session, student_id)
    await callback.message.answer(link)
    await callback.answer()
    
    
    
# Хэндлер для отправки файла ученика
@tutor_router.callback_query(F.data.startswith("sendfile_"))
async def send_student_files(callback: CallbackQuery, session: AsyncSession):
    try:
        files_list = await get_files(int(callback.data.split("_")[-1]), session)
        if not files_list:
            await callback.message.answer("❌ Файлы ученика не найдены.")
            return
        
        # Отправляем файлы по одному, проверяя их наличие
        for file in files_list:
            # Проверка, что файл существует по указанному пути
            if not os.path.exists(file):
                await callback.message.answer(f"❌ Файл '{file}' не найден на сервере.")
                continue
            document = FSInputFile(file)
            await callback.message.answer_document(document)
            
    except Exception as e:
        # Логирование ошибки для отладки (можно использовать logging.exception)
        await callback.message.answer("❌ Произошла ошибка при отправке файлов.")
        print(f"Ошибка при отправке файлов: {e}")
    finally:
        await callback.answer()



@tutor_router.callback_query(F.data.startswith("additional_"))
async def additional_actions(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обрабатывает дополнительные действия для ученика по ID"""
    try:
        await callback.answer()
        
        # Получаем ID ученика из callback данных
        student_id = int(callback.data.split("_")[1])
        
        # Проверяем существование ученика в базе
        student = await session.get(Student, student_id)
        if not student:
            await callback.message.answer("❌ Ученик не найден в базе данных")
            return

        # Сохраняем ID и имя в состоянии
        await state.update_data(
            selected_student_id=student_id,
            selected_student_name=student.name
        )
        await state.set_state(StudentSelection.advanced_actions)

        # Формируем клавиатуру с ID
        await callback.message.edit_text(
            f"⚙️ Дополнительные действия для:\n{student.name}",
            reply_markup=get_callback_btns(
                btns={
                    "◀️ Назад к ученику": f"back_{student_id}",
                    "🗑️ Удалить ученика": f"delete_{student_id}"
                },
                sizes=(1, 1)
        )
        )
        
    except ValueError:
        await callback.message.answer("❌ Ошибка в формате данных")
    except Exception as e:
        logger.error(f"Error in additional_actions: {e}")
        await callback.message.answer("❌ Произошла ошибка")



@tutor_router.callback_query(F.data.startswith("back_"))
async def back_to_student_profile(callback: CallbackQuery, session: AsyncSession):
    """Возврат к профилю ученика"""
    try:
        await callback.answer()
        student_id = int(callback.data.split("_")[1])
        
        student = await session.get(Student, student_id)
        if not student:
            await callback.message.answer("❌ Ученик не найден")
            return

        await callback.message.edit_text(
            f"👤 Профиль ученика:\n\n"
            f"Имя: {student.name}\n"
            f"УМК: {student.umk}\n"
            f"Баланс: {student.balance} занятий",
            reply_markup=get_callback_btns(
                btns={
                    "💸 Баланс": f"checkBalance_{student.id}",
                    "🔗 Ссылка": f"lessonLink_{student.id}", 
                    "📚 Материалы": f"sendfile_{student.id}",
                    "✏️ Изменить": f"edit_{student.id}",
                    "⚙️ Дополнительно": f"additional_{student.id}",
                    "◀️ Назад": "back_to_list"
                },
                sizes=(2, 2, 1)
            )
        )
    except Exception as e:
        logger.error(f"Ошибка возврата к ученику: {e}")
        await callback.message.answer("❌ Ошибка загрузки профиля")

@tutor_router.callback_query(F.data.startswith("delete_"))
async def delete_student_handler(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Обработка удаления ученика"""
    try:
        await callback.answer()
        student_id = int(callback.data.split("_")[1])
        
        await callback.message.edit_text(
            "⚠️ Вы уверены, что хотите удалить ученика?",
            reply_markup=get_callback_btns(
                btns={
                    "✅ Да, удалить": f"confirm_delete_{student_id}",
                    "❌ Нет, отмена": "cancel_delete"
                },
                sizes=(2,)
            )
        )
    except Exception as e:
        logger.error(f"Ошибка инициализации удаления: {e}")
        await callback.message.answer("❌ Ошибка при удалении")

@tutor_router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_student(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Подтвержденное удаление ученика"""
    try:
        await callback.answer()
        student_id = int(callback.data.split("_")[2])
        
        # Используем новую функцию удаления
        success = await orm_delete_student(session, student_id)
        
        if success:
            await callback.message.edit_text("✅ Ученик и связанные уроки удалены")
            await state.clear()
            await callback.message.answer(
                "Выберите действие:",
                reply_markup=TUTOR_KB
        )
        else:
            await callback.message.edit_text("❌ Ученик не найден")
            
    except ValueError as e:
        await callback.message.answer(str(e))
    except Exception as e:
        logger.error(f"Ошибка удаления: {e}")
        await callback.message.answer("❌ Ошибка при удалении ученика")
        
        
@tutor_router.callback_query(F.data == "cancel_delete")
async def cancel_deletion(callback: CallbackQuery, state: FSMContext, session):
    """Обработка отмены удаления ученика"""
    try:
        # Завершаем callback и убираем индикатор загрузки
        await callback.answer("❌ Удаление отменено")
        
        # Получаем данные из состояния
        data = await state.get_data()
        student_id = data.get("selected_student_id")
        
        if student_id:
            # Возвращаемся к профилю ученика
            student = await session.get(Student, student_id)
            if student:
                await callback.message.edit_text(
                    f"👤 Профиль ученика:\n{student.name}",
                    reply_markup=get_callback_btns(
                        btns={
                    "💸 Баланс": f"checkBalance_{student.id}",
                    "🔗 Ссылка": f"lessonLink_{student.id}", 
                    "📚 Материалы": f"sendfile_{student.id}",
                    "✏️ Изменить": f"edit_{student.id}",
                    "⚙️ Дополнительно": f"additional_{student.id}",
                    "◀️ Назад": "back_to_list"
                }, sizes=(2,2,1)
                    )
                )
            else:
                await callback.message.edit_text("❌ Ученик не найден")
                await state.clear()
        else:
            # Если ID ученика не сохранен, возвращаем к списку
            await callback.message.edit_text("🚫 Действие отменено")
            await back_to_students_list(callback, state, session)
            
    except Exception as e:
        logger.error(f"Ошибка при отмене удаления: {e}")
        await callback.message.answer("❌ Произошла ошибка при отмене")
        await state.clear()





# 1. Обработчик кнопки "Баланс ученика"
@tutor_router.callback_query(F.data.startswith("checkBalance_"))
async def balance_actions(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Управление балансом ученика по ID"""
    try:
        await callback.answer()
        student_id = int(callback.data.split("_")[1])
        
        # Получаем ученика из базы
        student = await session.get(Student, student_id)
        if not student:
            await callback.message.answer("❌ Ученик не найден")
            return

        # Обновляем сообщение вместо создания нового
        await callback.message.edit_text(
            f"💸 Баланс ученика: {student.balance} занятий\n"
            "Используйте кнопки для изменения:",
            reply_markup=get_callback_btns(btns={
                "➖ Провели урок": f"minus_{student_id}",
                "➕ Пополнение": f"plus_{student_id}",
                "◀️ Назад": f"back_{student_id}"
            })
        )
        
        # Сохраняем ID ученика в состоянии
        await state.update_data(selected_student_id=student_id)

    except Exception as e:
        logger.error(f"Ошибка баланса: {e}")
        await callback.message.answer("❌ Ошибка загрузки баланса")

# 2. Обработчики кнопок +/- 
@tutor_router.callback_query(F.data.startswith("minus_"))
async def minus_lesson(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Уменьшение баланса"""
    try:
        await callback.answer()
        student_id = int(callback.data.split("_")[1])
        
        async with session.begin():
            student = await session.get(Student, student_id)
            if not student:
                await callback.answer("❌ Ученик не найден")
                return

            
            student.balance -= 1
            await session.commit()
            await callback.answer("✅ Занятие списано")
            await balance_actions(callback, session, state)  # Обновляем баланс
            

    except Exception as e:
        logger.error(f"Ошибка списания: {e}")
        await session.rollback()
        await callback.answer("❌ Ошибка списания")

@tutor_router.callback_query(F.data.startswith("plus_"))
async def plus_lesson(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Увеличение баланса"""
    try:
        await callback.answer()
        student_id = int(callback.data.split("_")[1])
        
        async with session.begin():
            student = await session.get(Student, student_id)
            if not student:
                await callback.answer("❌ Ученик не найден")
                return

            student.balance += 1
            await session.commit()
            await callback.answer("✅ Занятие добавлено")
            await balance_actions(callback, session, state)  # Обновляем баланс

    except Exception as e:
        logger.error(f"Ошибка пополнения: {e}")
        await session.rollback()
        await callback.answer("❌ Ошибка пополнения")




class ChangeProperties(StatesGroup):
    main_changing_properties = State()
    waiting_for_umk = State()
    waiting_for_schedule = State()
    waiting_for_lesson_link = State()
    waiting_for_tg_id = State()
    waiting_for_cost = State()



@tutor_router.callback_query(F.data.startswith("edit_"))
async def change_student(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.set_state(ChangeProperties.main_changing_properties)
    try:
        student_id = int(callback.data.split("_")[1])
        student = await session.get(Student, student_id)
        
        if not student:
            await callback.answer("❌ Ученик не найден")
            return
        change_kbd = get_callback_btns(
                btns={
                    "📚 Описание": f"change_umk_{student_id}",
                    "🔗 Ссылка на урок": f"change_link_{student_id}",
                    "🆔 TG ID": f"change_tgid_{student_id}",
                    "💰 Стоимость": f"change_cost_{student_id}",
                    "Назад(к студенту)": "to_student"
                },
                sizes=(2, 2, 1)
            )
        await state.update_data(selected_student_id=student_id, change_kbd = change_kbd)
        
        await callback.message.edit_text(
            "📝 Выберите параметр для изменения:",
            reply_markup=change_kbd
            )
            
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Change error: {e}")
        await callback.answer("❌ Ошибка выбора параметра")








@tutor_router.callback_query(F.data == "to_student")
async def back_to_student(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Возврат к меню действий с учеником"""
    try:
        # Завершаем обработку callback
        await callback.answer()

        # Получаем данные ученика из состояния
        data = await state.get_data()
        student_id = data.get("selected_student_id")
        
        if not student_id:
            await callback.message.answer("❌ Ученик не выбран.")
            return

        # Получаем актуальные данные ученика из БД
        student = await session.get(Student, student_id)
        if not student:
            await callback.message.answer("❌ Ученик не найден.")
            await state.clear()
            return

        # Формируем сообщение с информацией о ученике
        text = (
            f"👤 Имя: {student.name}\n"
            f"📚 Инфа: {student.umk}\n"
            f"💸 Оплачено занятий: {student.balance}"
        )

        # Создаем клавиатуру действий
        reply_markup = get_callback_btns(
            btns={
                "💸 Баланс": f"checkBalance_{student.id}",
                "🔗 Ссылка": f"lessonLink_{student.id}",
                "📚 Материалы": f"sendfile_{student.id}",
                "✏️ Изменить": f"edit_{student.id}",
                "⚙️ Дополнительно": f"additional_{student.id}",
                "◀️ Назад": "back_to_list"
            },
            sizes=(2, 2, 1)
        )

        # Редактируем текущее сообщение
        await callback.message.edit_text(
            text=text,
            reply_markup=reply_markup
        )

        # Обновляем состояние
        await state.set_state(StudentSelection.choosed_student)

    except Exception as e:
        logger.error(f"Ошибка возврата к ученику: {e}")
        await callback.message.answer("❌ Ошибка загрузки данных.")
        await state.clear()


###########################################################
# Обработчик выбора параметра для изменения
@tutor_router.callback_query(F.data.startswith("change_"))
async def handle_parameter_change(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    try:
        param = callback.data.split("_")[1]
        student_id = int(callback.data.split("_")[-1])
        
        student = await session.get(Student, student_id)
        if not student:
            await callback.answer("❌ Ученик не найден")
            return

        state_mapping = {
            "umk": ChangeProperties.waiting_for_umk,
            "link": ChangeProperties.waiting_for_lesson_link,
            "cost": ChangeProperties.waiting_for_cost,
            "tgid": ChangeProperties.waiting_for_tg_id
        }

        # Сохраняем ID исходного сообщения
        sent_msg = await callback.message.answer(f"✏️ Введите новое значение для {param}:")
        
        await state.update_data(
            selected_student_id=student_id,
            param_to_change=param,
            edit_message_id=sent_msg.message_id  # Сохраняем ID сообщения
        )
        await state.set_state(state_mapping[param])
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка обработки параметра: {e}")
        await callback.answer("❌ Произошла ошибка")

@tutor_router.message(StateFilter(
    ChangeProperties.waiting_for_umk,
    ChangeProperties.waiting_for_lesson_link,
    ChangeProperties.waiting_for_tg_id,
    ChangeProperties.waiting_for_cost
))
async def apply_changes(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    student_id = data["selected_student_id"]
    param = data["param_to_change"]
    edit_message_id = data.get("edit_message_id")
    
    try:
        async with session.begin():
            student = await session.get(Student, student_id)
            if not student:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=edit_message_id,
                    text="❌ Ученик не найден"
                )
                return

            # Валидация и обработка данных
            if param == "tgid":
                setattr(student, "tg_id", message.text)
                
            elif param == "cost":
                try:
                    setattr(student, "cost", float(message.text))
                except ValueError:
                    await message.bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=edit_message_id,
                        text="❌ Введите нормальное число"
                    )
                    return
                    
            elif param == "link":
                setattr(student, "lesson_link", message.text)
                
            else:
                setattr(student, param, message.text)

            session.add(student)

        # Редактируем исходное сообщение
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=edit_message_id,
            text=f"✅ {param} успешно обновлён!"
        )
        
    except Exception as e:
        logger.error(f"Ошибка обновления: {e}")
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=edit_message_id,
            text="❌ Ошибка при сохранении изменений"
        )
    finally:
        await state.clear()
        await message.delete()  # Удаляем сообщение с вводом




class ScheduleFSM(StatesGroup):
    main_sch = State()
    choose_day = State()    # Выбор дня
    choose_student = State()
    set_time = State() 
    set_duration = State()      
    delete_lesson = State()
    confirm_deletion = State()
     
    
cancel_inline_scheduele = get_callback_btns(btns = {"Отмена":"cancel_"})

DAYS_OF_LESSON = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье"
}

DAYS_KB = get_keyboard(
    *[day for day in DAYS_OF_LESSON.values()],"В главное меню", sizes=(2,2,3,1)
)



@tutor_router.callback_query(F.data == "cancel_")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "Действие отменено. Возврат в меню раписания:",
        reply_markup=sheduele_buttons
    )
    await state.set_state(ScheduleFSM.main_sch)
    await callback.answer()


    
    
@tutor_router.message(F.text == "📅 Расписание")
async def schedule_actions(message: Message, state: FSMContext):
    await state.set_state(ScheduleFSM.main_sch)
    await message.answer(
        text="Доступные действия:",
        reply_markup=sheduele_buttons
    )
    
    
@tutor_router.message(F.text == "➕ Добавить урок")
async def add_lesson(message: Message, session: AsyncSession, state: FSMContext):
    # Основное сообщение с reply-клавиатурой
    await message.answer(
        "Выберите день для добавления урока:",
        reply_markup=DAYS_KB
    )
    
    # Отдельное сообщение с inline-кнопкой отмены
    await message.answer(
        "👇 Отменить действие:",
        reply_markup=cancel_inline_scheduele
    )
    
    list_of_students = await get_students(session)
    await state.update_data(students=list_of_students)
    await state.set_state(ScheduleFSM.choose_day)
    
    
@tutor_router.message(ScheduleFSM.choose_day, F.text.in_(DAYS_OF_LESSON.values()))
async def day_chosen(message: Message, state: FSMContext):
    DAY_TO_NUMBER = {v: k for k, v in DAYS_OF_LESSON.items()}
    await state.update_data(day=DAY_TO_NUMBER[message.text])
    
    data = await state.get_data()
    students = data.get("students", [])
    
    if not students:
        await message.answer("Нет учеников", reply_markup=cancel_inline_scheduele)
        return
    
    students_list = "\n".join(f"{s.name} (🆔: {s.id})" for s in students)
    
    # Основное сообщение
    await message.answer(
        f"Выберите ID ученика:\n\n{students_list}",
        reply_markup=ReplyKeyboardRemove()  # Убираем reply-клавиатуру
    ) 
    # Кнопка отмены
    await message.answer(
        "👇 Отменить действие:",
        reply_markup=cancel_inline_scheduele
    )
    
    await state.set_state(ScheduleFSM.choose_student)
    
    
    
@tutor_router.message(ScheduleFSM.choose_student)
async def process_student_number(message: Message, state: FSMContext, session: AsyncSession):
    # Получаем сохранённые данные
    data = await state.get_data()
    students = data.get("students", [])
    student_ids = [student.id for student in students]
    try:
        # Пытаемся преобразовать ввод в число
        selected_num = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Ошибка! Введите только цифру.")
        return
    
    # Проверяем корректность номера
    if selected_num not in student_ids:
        await message.answer(f"❌ Некорректный номер.")
        return

    # Сохраняем ID ученика и переходим к вводу времени
    await state.update_data(student_id=selected_num)
    await message.answer(
        f"⏰ Введите время урока"
        f"Например: 14:30/09 45/1030",
        reply_markup=cancel_inline_scheduele
    )
    
    await state.set_state(ScheduleFSM.set_time)
    
    
    
def parse_time(input_time: str) -> time:
    cleaned = re.sub(r'\D', '', input_time)
    
    if len(cleaned) == 3:
        cleaned = '0' + cleaned
        
    if len(cleaned) != 4:
        raise ValueError("Неверный формат времени")

    hours = int(cleaned[:2])
    minutes = int(cleaned[2:])
    
    # Проверяем валидность времени
    if not (0 <= hours <= 23):
        raise ValueError("Часы должны быть от 00 до 23")
    if not (0 <= minutes <= 59):
        raise ValueError("Минуты должны быть от 00 до 59")
    
    return time(hour=hours, minute=minutes)  # Возвращаем объект времени


@tutor_router.message(ScheduleFSM.set_time)
async def process_time(message: Message, state: FSMContext):
    try:
        time_obj = parse_time(message.text)
    except ValueError as e:
        # Отправляем сообщение об ошибке
        await message.answer(f"❌ Ошибка: {str(e)}\nВведите время в формате ЧЧ:ММ (например: 14:30 или 0945)")
        return  # Прерываем выполнение, чтобы не менять состояние

    await state.update_data(start_time=time_obj)
    await message.answer("⏳ Введите продолжительность урока в минутах (например: 60)",reply_markup=cancel_inline_scheduele)
    await state.set_state(ScheduleFSM.set_duration)
    
    

@tutor_router.message(ScheduleFSM.set_duration)
async def save_lesson(message: Message, session: AsyncSession, state: FSMContext):
    # Получаем данные из состояния
    data = await state.get_data()
    
    try:
        duration = int(message.text)
        if duration < 15 or duration > 240:
            raise ValueError
    except ValueError:
        await message.answer("❌ Некорректная длительность (15-240 минут)")
        return
    
    # Создаем запись
    new_lesson = Schedule(
        day_of_week=data['day'],
        start_time=data['start_time'],  # Объект time
        student_id=data['student_id'],
        #name = data['name'],
        duration=duration
    )
    
    session.add(new_lesson)
    await session.commit()
    
    await message.answer("✅ Урок успешно добавлен!", reply_markup=sheduele_buttons)
    await state.clear()
    
    
    
@tutor_router.message(F.text == "📖 Показать расписание")
async def show_schedule(message: Message, session: AsyncSession):
    # Получаем все уроки с именами учеников
    query = (
        select(Schedule, Student.name)
        .join(Student, Schedule.student_id == Student.id)
        .order_by(Schedule.day_of_week, Schedule.start_time)
    )
    
    result = await session.execute(query)
    lessons = result.all()
    
    if not lessons:
        await message.answer("🗓 Расписание пока пусто!")
        return
    
    # Группируем уроки по дням недели
    schedule_dict = {}
    for lesson, student_name in lessons:
        day_name = DAYS_OF_LESSON[lesson.day_of_week]
        time_str = lesson.start_time.strftime("%H:%M")
        
        if day_name not in schedule_dict:
            schedule_dict[day_name] = []
        
        schedule_dict[day_name].append(f"• {student_name} - {time_str} ({lesson.duration} мин)")
    
    # Форматируем вывод
    response = []
    for day in DAYS_OF_LESSON.values():
        if day in schedule_dict:
            response.append(f"\n📅 **{day}:**")
            response.extend(schedule_dict[day])
    
    await message.answer(
        "🗒 Ваше расписание на неделю:\n" + "\n".join(response),
        parse_mode="Markdown"
    )
    
    
    
    
    
    
    
    
@tutor_router.message(F.text == "❌ Удалить урок")
async def start_deletion(message: Message, session: AsyncSession, state: FSMContext):
    lessons = await get_lessons(session)
    if not lessons:
        await message.answer("🗓 Расписание пусто, нечего удалять!")
        return
    
    # Формируем данные для сохранения
    lesson_data = [
        (lesson.id, DAYS_OF_LESSON[lesson.day_of_week], 
        lesson.start_time.strftime("%H:%M"), student_name)
        for lesson, student_name in lessons
    ]
    lesson_ids = [lesson.id for lesson, _ in lessons]
    
    await state.update_data(
        lesson_data=lesson_data,
        lesson_ids=lesson_ids
    )
    
    # Формируем сообщение
    lessons_list = "\n".join(
        f"ID: {id} | {day} | {student} | {time}"
        for id, day, time, student in lesson_data
    )
    
    await message.answer(
        "Выберите урок для удаления:\n\n" + lessons_list + 
        "\n\n❕ Введите ID урока из списка",
        reply_markup=cancel_inline_scheduele
    )
    
    await state.set_state(ScheduleFSM.delete_lesson)

@tutor_router.message(ScheduleFSM.delete_lesson)
async def process_deletion(message: Message, state: FSMContext):
    data = await state.get_data()
    lesson_ids = data["lesson_ids"]
    
    try:
        selected_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите число!")
        return  # Состояние не меняется

    if selected_id not in lesson_ids:
        # Повторно используем сохраненные данные
        lessons_list = "\n".join(
            f"ID: {id} | {day} | {student} | {time}"
            for id, day, time, student in data["lesson_data"]
        )
        
        await message.answer(
            f"❌ Урока с ID {selected_id} нет!\n\nДоступные уроки:\n{lessons_list}",
            reply_markup=cancel_inline_scheduele
        )
        return  # Остаемся в delete_lesson

    await message.answer(
        f"⚠️ Удалить урок {selected_id}?",
        reply_markup=get_callback_btns(btns={
            "Да": f"confirm_del_{selected_id}",
            "Нет": "cancel_del"
        })
    )
    await state.set_state(ScheduleFSM.confirm_deletion)
    

# Обработчик кнопки "Нет"
@tutor_router.callback_query(F.data == "cancel_del")
async def cancel_deletion(callback: CallbackQuery, state: FSMContext):
    # Завершаем обработку callback
    await callback.answer("❌ Удаление отменено")
    
    # Восстанавливаем список уроков
    data = await state.get_data()
    lessons_list = "\n".join(
        f"ID: {id} | {day} | {student} | {time}"
        for id, day, time, student in data.get("lesson_data", [])
    )
    
    # Редактируем сообщение с исходными данными
    await callback.message.edit_text(
        "Удаление отменено. Выберите урок:\n\n" + lessons_list,
        reply_markup=cancel_inline_scheduele
    )
    
    # Возвращаем в состояние выбора урока
    await state.set_state(ScheduleFSM.delete_lesson)

# Обработчик подтверждения удаления
@tutor_router.callback_query(F.data.startswith("confirm_del_"))
async def confirm_deletion(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    try:
        # Всегда отвечаем на callback сразу
        await callback.answer()
        
        lesson_id = int(callback.data.split("_")[-1])
        data = await state.get_data()
        
        if lesson_id not in data.get("lesson_ids", []):
            await callback.answer("❌ Урок не найден!", show_alert=True)
            return

        # Удаление урока
        await delete_lesson(session, lesson_id)
        await callback.answer("✅ Урок удалён")
        
        # Обновляем данные
        lessons = await get_lessons(session)
        if not lessons:
            await callback.message.answer(
                "🗓 Расписание теперь пусто!",
                reply_markup=sheduele_buttons
            )
            await state.clear()
            return

        # Подготавливаем новые данные
        new_data = [
            (lesson.id, DAYS_OF_LESSON[lesson.day_of_week], 
            lesson.start_time.strftime("%H:%M"), student_name)
            for lesson, student_name in lessons
        ]
        
        # Обновляем состояние
        await state.update_data(
            lesson_data=new_data,
            lesson_ids=[lesson.id for lesson, _ in lessons]
        )
        
        await state.set_state(ScheduleFSM.delete_lesson)

    except Exception as e:
        await callback.answer("⚠️ Произошла ошибка!", show_alert=True)
        await state.clear()
        logger.error(f"Deletion error: {e}")
    
    # Обновляем данные
    lessons = await get_lessons(session)
    if not lessons:
        await callback.message.answer("✅ Расписание пусто!", reply_markup=sheduele_buttons)
        await state.clear()
        return
    
    # Обновляем состояние
    new_data = [
        (lesson.id, DAYS_OF_LESSON[lesson.day_of_week], 
        lesson.start_time.strftime("%H:%M"), student_name)
        for lesson, student_name in lessons
    ]
    await state.update_data(
        lesson_data=new_data,
        lesson_ids=[lesson.id for lesson, _ in lessons]
    )
    
    await callback.message.answer(
        "✅ Урок удален! Новый список:\n\n" + 
        "\n".join(f"ID: {id} | {day} | {student} | {time}" 
                 for id, day, time, student in new_data),
        reply_markup=cancel_inline_scheduele
    )
    await state.set_state(ScheduleFSM.delete_lesson)
    
    
@tutor_router.message(F.text | F.sticker)
async def test(message):
    await message.reply("Не балуйся")
    await message.answer_sticker("CAACAgIAAxkBAAIiYmfn1cQeRZPPtXrl8xBYbgYuN8zPAAJfIQAC_AURS8u3kBUrBc55NgQ", reply_markup = TUTOR_KB)
    
