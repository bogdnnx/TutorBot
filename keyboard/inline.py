from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_callback_btns(*,btns:dict[str,str], sizes= (2,)):
    keyboard = InlineKeyboardBuilder()
    
    for text,data in btns.items():
        if "://" in data:
            keyboard.add(InlineKeyboardButton(text=text, url = data.split("_")[1]))            
        else:
            keyboard.add(InlineKeyboardButton(text=text, callback_data=data))
    return keyboard.adjust(*sizes).as_markup()