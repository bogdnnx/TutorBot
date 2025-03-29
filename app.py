from aiogram import Bot, Dispatcher
import asyncio
import logging
from aiogram.types import BotCommandScopeAllPrivateChats
from dotenv import find_dotenv, load_dotenv
import os

load_dotenv(find_dotenv())

from middlewares.db import DataBaseSession
from database.engine import create_db, drop_db, sessionmaker
from handlers import user_private,user_group,tutor
from common.bot_commads_list import private


bot  = Bot(token=os.getenv("TOKEN"))

bot.my_admins_list = []
bot.tutors_list = list(map(int, os.getenv("TUTORS_LIST", "").split(',')))
dp = Dispatcher()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
 

dp.include_routers(tutor.tutor_router,user_private.user_private_router)


async def on_startup(bot):
    run_param = False
    if run_param:
        await drop_db()
   
    await create_db() 


async def on_shutdown(bot):
    print("bot leg")

    
async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.update.middleware(DataBaseSession(session_pool=sessionmaker))
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=private, scope =BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot)
    
    
    
asyncio.run(main())

