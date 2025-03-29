from aiogram.types import KeyboardButton,ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder




def get_keyboard(*btns: str, placeholder = None, request_contact:bool = None, request_location:bool = None,sizes = (2,)):
    keyboard = ReplyKeyboardBuilder()
    for index,text in enumerate(btns, start=1):
        if request_contact and request_contact == index:
            keyboard.add(KeyboardButton(text = text, request_contact=True))
        elif request_location and request_location==index:
            keyboard.add(KeyboardButton(text = text, request_location= True))
        else:
            keyboard.add(KeyboardButton(text=text))
        
    return keyboard.adjust(*sizes).as_markup(resize_keyboard = True, input_field_placeholder = placeholder)




# start_kb = ReplyKeyboardMarkup(
#     keyboard=[
#         [
#             KeyboardButton(text="Стартовое меню"),
#             KeyboardButton(text="Способы оплаты"),
            
#         ],
#         [
#             KeyboardButton(text="О репетиторе")
#         ]
#     ],
#     resize_keyboard=True,
#     input_field_placeholder="anuka",
    
# )
# del_kbd = ReplyKeyboardRemove()


# another_keyboard = ReplyKeyboardBuilder()
# another_keyboard.add(
#     KeyboardButton(text="Стартовое меню"),
#     KeyboardButton(text="Способы оплаты"),
#     KeyboardButton(text="О репетиторе"),
#     KeyboardButton(text = "назад")
# )
# another_keyboard.adjust(2,2)


# kb3 = ReplyKeyboardBuilder()
# kb3.attach(another_keyboard)
# kb3.add(KeyboardButton(text = "stairway to heaven"))



# test_kb = ReplyKeyboardMarkup(
#     keyboard= [
#         [
#             KeyboardButton(text = "get yors location",request_location=True),
#             KeyboardButton(text = "gets your number",request_contact=True)
#         ],
        
#         [
#             KeyboardButton(text = "создать опрос", request_poll=KeyboardButtonPollType())
#         ]
        
#     ], resize_keyboard= True
# )

