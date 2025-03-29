from aiogram import Router,types,F
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart,Command
from aiogram.filters import or_f
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.utils.formatting import Bold,as_marked_section,as_list
import time

from filters.chat_types import ChatTypeFilter
from keyboard.reply import get_keyboard


user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(['private']))

@user_private_router.message()
async def greeting_not_student(message: Message, state: FSMContext):
    # Получаем текущее состояние счетчика
    data = await state.get_data()
    cnt = data.get("cnt", 0)

    if cnt == 0:
        # Обновляем счетчик в состоянии
        await state.update_data(cnt=1)
        
        await message.answer("Сейчас происходит проверка того, кто вы есть ⌛️....")
        time.sleep(2)  # Асинхронная задержка
        
        await message.answer_sticker("CAACAgIAAx0Cd0LlaQACAXdn59Gbd_52xZUINF1dEAdolz4nUgAC0EoAAqBmSEl0fjImBeb1GTYE")
        await message.answer("Я в недоумении...\nТебя нет в списке приглашеных пользователей, если ты ученик - обратись к репетитору")
    else:
        await message.answer_sticker("CAACAgIAAxkBAAIiYmfn1cQeRZPPtXrl8xBYbgYuN8zPAAJfIQAC_AURS8u3kBUrBc55NgQ")