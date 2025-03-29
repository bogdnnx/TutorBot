from string import punctuation
from aiogram import F,types,Router, Bot
from filters.chat_types import ChatTypeFilter
from aiogram.filters import Command
from filters.chat_types import ChatTypeFilter, IsTutor


user_group_router = Router()
user_group_router.message.filter(ChatTypeFilter(['group','supergroup']), IsTutor())

restricted_words = {"кабан", 'хомяк'}

@user_group_router.message(Command("admin"))
async def get_admins(message: types.Message, bot: Bot):
    chat_id = message.chat.id
    admins_list = await bot.get_chat_administrators(chat_id)
    #просмотреть все данные и свойства полученных объектов
    #print(admins_list)
    # Код ниже это генератор списка, как и этот x = [i for i in range(10)]
    admins_list = [
        member.user.id
        for member in admins_list
        if member.status == "creator" or member.status == "administrator"
    ]
    bot.my_admins_list = admins_list
    if message.from_user.id in admins_list:
        await message.delete()


def clean_text(text:str):
    return text.translate(str.maketrans('','',punctuation))






@user_group_router.edited_message()
@user_group_router.message()
async def start_cmd(message: types.Message):
    if restricted_words.intersection(clean_text(message.text.lower()).split()):
        await message.answer(f"Пользователь {message.from_user.first_name} соблюдайте порядок")
        await message.delete()  