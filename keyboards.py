from vkbottle import Keyboard, Text, KeyboardButtonColor, OpenLink

from config import question_answer

back_keyboard = (
    Keyboard(one_time=True, inline=False)
    .add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
)

question_frequent = (
    Keyboard(one_time=True, inline=False)
)
for el in question_answer:
    question_frequent.add(Text(el), color=KeyboardButtonColor.PRIMARY)
    question_frequent.row()
question_frequent.add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)

tech_support_keyboard = (
    Keyboard(one_time=False, inline=False)
    .add(Text("Вопрос решен"), color=KeyboardButtonColor.POSITIVE)
).get_json()

choice_polygon_keyboard = (
    Keyboard(one_time=True, inline=False)
    .add(OpenLink("https://vk.com/topic-218785093_49262342", "Домодедово"), color=KeyboardButtonColor.PRIMARY)
    .add(OpenLink("https://vk.com/topic-218785093_50861865", "Южный"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
).get_json()

unknown_keyboard = (
    Keyboard(one_time=True, inline=False)
    .add(Text("В главное меню"), color=KeyboardButtonColor.PRIMARY)
).get_json()

admin_start_keyboard = (
    Keyboard(one_time=True, inline=False)
    .add(Text("Информация"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Аренда"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Помощь"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Панель администратора"), color=KeyboardButtonColor.PRIMARY)
).get_json()

admin_menu_keyboard = (
    Keyboard(one_time=True, inline=False)
    .add(Text("Список всей аренды"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Отменить аренду человеку"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Список тех. специалистов"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Добавить тех. специалиста"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Удалить тех. специалиста"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
).get_json()

start_keyboard = (
    Keyboard(one_time=True, inline=False)
    .add(Text("Информация"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Аренда"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Помощь"), color=KeyboardButtonColor.PRIMARY)
).get_json()

help_menu_keyboard = (
    Keyboard(one_time=True, inline=False)
    .add(Text("Техническая поддержка"), color=KeyboardButtonColor.PRIMARY)
    .add(Text("Частые вопросы"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
).get_json()

information_keyboard = (
    Keyboard(one_time=True, inline=False)
    .add(OpenLink("https://vk.com/uslugi-218785093?screen=group", "Услуги"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Как добраться?"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(OpenLink("https://vk.com/topic-218785093_49290691", "Правила"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(OpenLink("https://vk.com/airsoft_pd?z=album-218785093_301260832", "Фото полигона"),
         color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(OpenLink("https://vk.com/topic-218785093_49318795", "Отзывы/Предложения"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
).get_json()

lease_keyboard = (
    Keyboard(one_time=True, inline=False)
    .add(Text("Аренда вещей"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Цены на аренду"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Количество оставшейся аренды"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Мои арендованные вещи"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Отменить аренду"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
).get_json()
