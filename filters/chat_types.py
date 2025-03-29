from aiogram.filters import Filter
from aiogram import types,Bot


class ChatTypeFilter(Filter):
    def __init__(self,chat_types):
        self.chat_types = chat_types
        
    async def __call__(self, message:types.Message):
        return message.chat.type in self.chat_types

    
class IsTutor(Filter):
    def __init__(self):
        pass
    
    async def __call__(self, message:types.Message,bot:Bot):
        return message.from_user.id in bot.tutors_list