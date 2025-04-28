print("Запуск скрипта...")
import asyncio
import emoji
import requests
import pytz
import os
print("Базовые библиотеки импортированы...")
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
print("Импорт telegram библиотек...")
from telegram import ParseMode, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
print("Все библиотеки импортированы успешно!")

# Loading environment variables from .env file
load_dotenv()

# Getting token and admin ID from environment variables
ADMIN_USER_ID = 7984786953  # Admin ID
ADMIN_PASSWORD = "adminadminadmin"
API_TOKEN = "7401690820:AAHG3suZUs-YVkOxVFnkYsf7dQ9LPaOYu9o"  # Telegram bot token
BOT_USERNAME = "@nisam_stranacbot"
TARGET_USER_ID = 7984786953
OWNER_USER_ID = 7126605969
MAX_PARTICIPANTS = 200  # Maximum number of participants in each group
# Dictionary to store group data
group_data = {
    'Beginners': {'subject': '', 'time': ''},
    'Intermediate': {'subject': '', 'time': ''},
    'Advanced': {'subject': '', 'time': ''},
    'Online': {'subject': '', 'time': ''}
}
# Dictionary to store registration data (use a persistent storage instead for real applications)
registrations = {group: set() for group in group_data.keys()}
# Password for manual list clearing (replace with your desired password)
CLEAR_PASSWORD = "your_password"
# Russian translations for groups
group_translations = {
    'Beginners': 'Начинающие',
    'Intermediate': 'Продолжающие',
    'Advanced': 'Продвинутые',
    'Online': 'Онлайн'
}
# Custom data
subject_for_beginner = ''
subject_for_pro = ''
subject_for_advanced = ''
subject_for_online = ''
time_for_beginner = ''
time_for_pro = ''
time_for_advanced = ''
time_for_online = ''
next_date = ''
next_weekday = ''


# Helper functions
def keepalive():
    send_message(chat_id=ADMIN_USER_ID, text="keepalive completed")


def clear_registrations():
    global registrations
    registrations = {group: set() for group in group_data.keys()}


def send_message(chat_id, text):
    """Sends a message to the specified chat ID."""
    try:
        url = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage?chat_id={chat_id}&text={text}'
        requests.get(url)
    except Exception as e:
        print(f"Error sending message: {e}")


def admin_command(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_USER_ID:
        return
    admin_menu_command(update, context)


def button(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == 'add_new_group':
        query.edit_message_text(
            "Введите название новой группы в формате:\nadmin:add group:название группы"
        )
    elif query.data == 'delete_group':
        # Create a list of buttons for all groups
        keyboard = []
        for group in group_data.keys():
            group_ru = group_translations.get(group, group)
            keyboard.append([InlineKeyboardButton(f"Удалить {group_ru}", callback_data=f"confirm_delete:{group}")])
        keyboard.append([InlineKeyboardButton("Назад", callback_data="admin_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text("Выберите группу для удаления:", reply_markup=reply_markup)
    elif query.data.startswith('confirm_delete:'):
        group_name = query.data.split(':')[1]
        if delete_group(group_name):
            group_ru = group_translations.get(group_name, group_name)
            query.edit_message_text(f"Группа '{group_ru}' успешно удалена.")
        else:
            query.edit_message_text(f"Группа не найдена.")
    elif query.data in [group.lower() for group in group_data.keys()]:
        # Dynamically call the registration function for the selected group
        group_name = next(group for group in group_data.keys() if group.lower() == query.data)
        sign_up_command(update, context, group_name)
    elif query.data == 'cancel':
        cancel_command(update, context)
    elif query.data == 'closest_meeting':
        closest_meeting(update, context)
    elif query.data == 'check_assignments':
        check_assignments(update, context)
    elif query.data == 'menu':
        menu_command(update, context)
    elif query.data == 'admin_menu':
        admin_menu_command(update, context)
    else:
        query.edit_message_text("Данная опция не существует, пожалуйста, выберите снова.")


# Commands
def start_command(update: Update, context: CallbackContext):
    # Buttons and menu items
    keyboard = [
        [
            InlineKeyboardButton("Меню", callback_data="menu")
        ],
        [
            InlineKeyboardButton("Ближайшая встреча", callback_data="closest_meeting")
        ]
    ]
    
    # List of standard groups
    default_groups = {'Beginners', 'Intermediate', 'Advanced', 'Online'}
    
    # Add buttons for all groups
    for group in group_data.keys():
        group_ru = group_translations.get(group, group)
        button_text = f"Записаться на {group_ru}" if group in default_groups else f"Записаться на {group_ru}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=group.lower())])
    
    # Add the cancel registration button at the end
    keyboard.append([InlineKeyboardButton("Отменить запись", callback_data="cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        f"""
Привет!{emoji.emojize(':waving_hand:')}

Я бот-помощник для записи на разговорный клуб в
школе <b>"Nisam stranac"</b>.

* Разговорные клубы проходят каждую неделю.{emoji.emojize(':spiral_calendar:')}
* Адрес: Футошка 1а, 5 этаж, офис 510.{emoji.emojize(':round_pushpin:')}\n
Используйте кнопки ниже для навигации по боту.\n
Кнопка <b>"Ближайшая встреча"</b> расскажет вам о темах будущих разговорных клубов.\n
Друзья, если вы не можете прийти, пожалуйста, отмените свою регистрацию.""", reply_markup=reply_markup,
        parse_mode=ParseMode.HTML)


def menu_command(update: Update, context: CallbackContext):
    """Handles the /menu command."""
    keyboard = []
    # List of standard groups
    default_groups = {'Beginners', 'Intermediate', 'Advanced', 'Online'}
    
    for group in group_data.keys():
        group_ru = group_translations.get(group, group)
        button_text = f"Записаться на {group_ru}" if group in default_groups else f"Записаться на {group_ru}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=group.lower())])
    keyboard.append([InlineKeyboardButton("Отменить запись", callback_data="cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        update.message.reply_text("Меню", reply_markup=reply_markup)
    else:
        update.callback_query.edit_message_text("Меню", reply_markup=reply_markup)


def closest_meeting(update, context: CallbackContext):
    """Handles the /when_is_closest_meeting command."""
    keyboard = []
    # List of standard groups
    default_groups = {'Beginners', 'Intermediate', 'Advanced', 'Online'}
    
    for group in group_data.keys():
        group_ru = group_translations.get(group, group)
        button_text = f"Записаться на {group_ru}" if group in default_groups else f"Записаться на {group_ru}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=group.lower())])
    keyboard.append([InlineKeyboardButton("Меню", callback_data="menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    global next_date
    
    text = f"Следующая встреча в <b>{next_weekday}</b>, <b>{next_date}</b>.\n\n"
    for group, data in group_data.items():
        group_ru = group_translations.get(group, group)
        group_text = f"для группы {group_ru}" if group in default_groups else group_ru
        text += f"Тема {group_text} в <b>{data['time']}</b>:\n{data['subject']}\n\n"
    
    if update.message:
        update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


def sign_up_command(update: Update, context: CallbackContext, group_name: str):
    """Universal function for registration in any group"""
    user_name = update.effective_user.full_name
    user_tag = update.effective_user.username
    user_name_n_tag = f"{user_name}, @{user_tag}"
    global next_date
    
    # List of standard groups
    default_groups = {'Beginners', 'Intermediate', 'Advanced', 'Online'}
    
    keyboard = [
        [
            InlineKeyboardButton("Ближайшая встреча", callback_data="closest_meeting")
        ],
        [
            InlineKeyboardButton("Меню", callback_data="menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Format text based on group type
    group_ru = group_translations.get(group_name, group_name)
    group_text = f"для группы {group_ru}" if group_name in default_groups else group_ru

    if user_name_n_tag in registrations[group_name]:
        if update.message:
            update.message.reply_text(f"Вы уже зарегистрированы на встречу {group_text}.",
                                            reply_markup=reply_markup)
        else:
            update.callback_query.edit_message_text(text=f"Вы уже зарегистрированы на встречу {group_text}.",
                                                          reply_markup=reply_markup)
    elif registrations[group_name].__len__() >= MAX_PARTICIPANTS:
        if update.message:
            update.message.reply_text(f"Встречи для {group_text} заполнены.", reply_markup=reply_markup)
        else:
            update.callback_query.edit_message_text(text=f"Встречи для {group_text} заполнены.",
                                                          reply_markup=reply_markup)
    else:
        registrations[group_name].add(user_name_n_tag)
        if update.message:
            update.message.reply_text(
                f"""Вы успешно зарегистрировались на встречу {group_text}
{next_date} в {group_data[group_name]['time']}.""",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Отменить запись", callback_data="cancel")],
                     [InlineKeyboardButton("Меню", callback_data="menu")]]
                ))
            send_message(chat_id=TARGET_USER_ID,
                         text=f"{user_name} - зарегистрирован на встречу {group_text} {next_date}")
            send_message(chat_id=OWNER_USER_ID,
                         text=f"{user_name} - зарегистрирован на встречу {group_text} {next_date}")
        else:
            update.callback_query.edit_message_text(
                f"""Вы успешно зарегистрировались на встречу {group_text}
{next_date} в {group_data[group_name]['time']}.""",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Отменить запись", callback_data="cancel")],
                     [InlineKeyboardButton("Меню", callback_data="menu")]]
                )
            )
            send_message(chat_id=TARGET_USER_ID,
                         text=f"{user_name} - зарегистрирован на встречу {group_text} {next_date}")
            send_message(chat_id=OWNER_USER_ID,
                         text=f"{user_name} - зарегистрирован на встречу {group_text} {next_date}")


def check_assignments(update: Update, context: CallbackContext):
    """Handles the /check_assignments command."""
    user_name = update.effective_user.full_name
    user_tag = update.effective_user.username
    user_name_n_tag = f"{user_name}, @{user_tag}"
    global next_date
    keyboard = [
        [
            InlineKeyboardButton("Отменить запись", callback_data="cancel")
        ],
        [
            InlineKeyboardButton("Меню", callback_data="menu")
        ]
    ]
    keyboard2 = [
        [
            InlineKeyboardButton("Ближайшая встреча", callback_data="closest_meeting")
        ],
        [
            InlineKeyboardButton("Меню", callback_data="menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_markup2 = InlineKeyboardMarkup(keyboard2)

    is_registered_beginner = user_name_n_tag in registrations['Beginners']
    is_registered_pro = user_name_n_tag in registrations['Intermediate']

    if is_registered_beginner and is_registered_pro:
        # User is signed up for both meetings
        if update.message:
            update.message.reply_text(
                f"Вы зарегистрированы на обе встречи в пятницу, {next_date}:\n"
                f"* Для начинающих в {time_for_beginner}.\n"
                f"* Для продолжающих в {time_for_pro}.", reply_markup=reply_markup)
        else:
            update.callback_query.edit_message_text(
                f"Вы зарегистрированы на обе встречи в пятницу, {next_date}:\n"
                f"* Для начинающих в {time_for_beginner}.\n"
                f"* Для продолжающих в {time_for_pro}.", reply_markup=reply_markup)
    elif is_registered_beginner:
        # User is only signed up for beginner meeting
        if update.message:
            update.message.reply_text(
                f"Вы зарегистрированы на встречу для начинающих в пятницу, {next_date} в {time_for_beginner}.",
                reply_markup=reply_markup)
        else:
            update.callback_query.edit_message_text(
                f"Вы зарегистрированы на встречу для начинающих в пятницу, {next_date} в {time_for_beginner}.",
                reply_markup=reply_markup)
    elif is_registered_pro:
        # User is only signed up for pro meeting
        if update.message:
            update.message.reply_text(
                f"Вы зарегистрированы на встречу для продолжающих в пятницу, {next_date} в {time_for_pro}.",
                reply_markup=reply_markup)
        else:
            update.callback_query.edit_message_text(
                f"Вы зарегистрированы на встречу для продолжающих в пятницу, {next_date} в {time_for_pro}.",
                reply_markup=reply_markup)
    else:
        # User is not signed up for any meetings
        if update.message:
            update.message.reply_text("Вы не зарегистрированы ни на одну встречу.", reply_markup=reply_markup2)
        else:
            update.callback_query.edit_message_text("Вы не зарегистрированы ни на одну встречу.",
                                                          reply_markup=reply_markup2)


def cancel_command(update: Update, context: CallbackContext):
    """Handles the /cancel command."""
    user_name = update.effective_user.full_name
    user_tag = update.effective_user.username
    user_name_n_tag = f"{user_name}, @{user_tag}"
    global next_date
    keyboard = [
        [
            InlineKeyboardButton("Ближайшая встреча", callback_data="closest_meeting")
        ],
        [
            InlineKeyboardButton("Меню", callback_data="menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Check all groups
    for group_name in group_data.keys():
        if user_name_n_tag in registrations[group_name]:
            registrations[group_name].remove(user_name_n_tag)
            group_ru = group_translations.get(group_name, group_name)
            send_message(chat_id=TARGET_USER_ID,
                          text=f"{user_name} - отменил регистрацию на {group_ru} {next_date}")
            send_message(chat_id=OWNER_USER_ID,
                          text=f"{user_name} - отменил регистрацию на {group_ru} {next_date}")
            if update.message:
                update.message.reply_text("Вы больше не зарегистрированы ни на одну встречу.", reply_markup=reply_markup)
            else:
                update.callback_query.edit_message_text(text="Вы больше не зарегистрированы ни на одну встречу.", reply_markup=reply_markup)
            return

    # If the user was not found in any group
    if update.message:
        update.message.reply_text("Вы не зарегистрированы ни на одну встречу.", reply_markup=reply_markup)
    else:
        update.callback_query.edit_message_text(text="Вы не зарегистрированы ни на одну встречу.", reply_markup=reply_markup)


# Admin commands
def admin_menu_command(update: Update, context: CallbackContext):
    """Handles the /admin_menu command."""
    keyboard = [
        [
            InlineKeyboardButton("Добавить новую группу", callback_data="add_new_group"),
        ],
        [
            InlineKeyboardButton("Удалить группу", callback_data="delete_group"),
        ],
        [
            InlineKeyboardButton("Изменить тему для начинающих", callback_data="change_subject_for_beginner"),
        ],
        [
            InlineKeyboardButton("Изменить тему для продолжающих", callback_data="change_subject_for_pro"),
        ],
        [
            InlineKeyboardButton("Изменить тему для онлайн", callback_data="change_subject_for_online"),
        ],
        [
            InlineKeyboardButton("Изменить время для начинающих", callback_data="change_time_for_beginner"),
        ],
        [
            InlineKeyboardButton("Изменить время для продолжающих", callback_data="change_time_for_pro"),
        ],
        [
            InlineKeyboardButton("Изменить время для онлайн", callback_data="change_time_for_online"),
        ],
        [
            InlineKeyboardButton("Изменить дату", callback_data="change_next_friday"),
        ],
        [
            InlineKeyboardButton("Назад", callback_data="menu")
        ]
    ]
    admin_menu_keyboard = InlineKeyboardMarkup(keyboard)
    if update.message:
        update.message.reply_text("Выберите действие:", reply_markup=admin_menu_keyboard)
    else:
        update.callback_query.edit_message_text("Выберите действие:", reply_markup=admin_menu_keyboard)
    print('Открыто меню администратора')


def change_subject_for_beginner(update, context):
    """Handles the /change_subject_for_beginner command."""
    split_message = update.message.text.split(":")
    global subject_for_beginner
    subject_for_beginner = split_message[2].capitalize()
    update.message.reply_text(f"Текущая тема для начинающих: {subject_for_beginner}")


def save_subject_for_beginner(update, context):
    pass


def change_subject_for_pro(update, context):
    """Handles the /change_subject_for_pro command."""
    split_message = update.message.text.split(":")
    global subject_for_pro
    subject_for_pro = split_message[2].capitalize()
    update.message.reply_text(f"Текущая тема для продолжающих: {subject_for_pro}")


def save_subject_for_pro(update, context):
    pass


def change_time_for_beginner(update, context):
    pass


def save_time_for_beginner(update, context):
    pass


def change_time_for_pro(update, context):
    pass


def save_time_for_pro(update, context):
    pass


def change_next_friday(update, context):
    pass


def save_next_friday(update, context):
    pass


def change_subject_for_online(update, context):
    """Handles the /change_subject_for_online command."""
    split_message = update.message.text.split(":")
    global subject_for_online
    subject_for_online = split_message[2].capitalize()
    update.message.reply_text(f"Текущая тема для онлайн: {subject_for_online}")


def change_time_for_online(update, context):
    # ... similar to other functions ...
    pass


# Responses

def delete_group(group_name: str):
    """Deletes a group from the group_data and registrations dictionaries"""
    if group_name in group_data:
        del group_data[group_name]
        del registrations[group_name]
        return True
    return False


def move_group(group_name: str, position: int) -> bool:
    """Moves a group to the specified position in the list"""
    if group_name not in group_data:
        return False
    
    # Convert dictionaries to lists for easier ordering
    groups = list(group_data.keys())
    registrations_list = list(registrations.items())
    
    # Find the current index of the group
    current_index = groups.index(group_name)
    
    # Remove the group from the current position
    groups.pop(current_index)
    registrations_list.pop(current_index)
    
    # Insert the group at the new position (considering that the position starts from 1)
    new_index = min(max(0, position - 1), len(groups))
    groups.insert(new_index, group_name)
    registrations_list.insert(new_index, (group_name, registrations[group_name]))
    
    # Update dictionaries with the new order
    group_data.clear()
    registrations.clear()
    for group in groups:
        group_data[group] = {'subject': '', 'time': ''}
        registrations[group] = set()
    
    # Restore group data
    for group, reg_data in registrations_list:
        group_data[group] = {'subject': '', 'time': ''}  # Restore subject and time if they are stored separately
        registrations[group] = reg_data
    
    return True


def handle_response(text: str, context: CallbackContext, update: Update) -> str:
    """Handles admin commands."""
    processed_text = text.lower()
    # List of standard groups
    default_groups = {'Beginners', 'Intermediate', 'Advanced', 'Online'}

    # Обработка русскоязычных команд
    if processed_text in ["старт", "начать", "привет", "начало", "help", "помощь"]:
        start_command(update, context)
        return ""

    if "admin:show list" in processed_text:
        result = ""
        for group, users in registrations.items():
            group_ru = group_translations.get(group, group)
            result += f"{group_ru}:\n{', '.join(users)}\n\n"
        return result

    elif "admin:add group:" in processed_text:
        group_name = text.split(":", 2)[2].strip()
        if add_new_group(group_name):
            return f"Группа '{group_name}' успешно добавлена."
        else:
            return f"Группа '{group_name}' уже существует."

    elif "admin:delete group:" in processed_text:
        group_name = text.split(":", 2)[2].strip()
        if delete_group(group_name):
            return f"Группа '{group_name}' успешно удалена."
        else:
            return f"Группа '{group_name}' не найдена."

    elif "admin:subject" in processed_text:
        # Сначала проверяем, является ли это командой для настройки темы новой группы
        if text.startswith("admin:subject:"):
            # Обработка для новых групп (admin:subject:группа:тема)
            # Разделяем первые две части (admin:subject)
            prefix = ":".join(text.split(":", 2)[:2])
            # Получаем остаток строки после admin:subject:
            remainder = text[len(prefix)+1:]
            # Находим первое двоеточие в remainder, это разделитель между группой и темой
            if ":" in remainder:
                separator_index = remainder.find(":")
                group = remainder[:separator_index].strip()
                subject = remainder[separator_index+1:].strip()
                
                if group in group_data and group not in default_groups:
                    group_data[group]['subject'] = subject
                    return f"Тема для группы '{group}' обновлена: {subject}"
                elif group not in group_data:
                    return f"Группа '{group}' не найдена."
                else:
                    return "Используйте другой формат команды для стандартных групп."
            else:
                return "Неверный формат команды. Используйте: admin:subject:группа:тема"
        # Стандартный формат для предустановленных групп (admin:subject группа:тема)
        else:
            parts = text.split(":", 2)
            if len(parts) >= 2:
                # admin:subject группа:тема (первая часть "admin:subject группа", вторая - "тема")
                first_part = parts[0]
                group_parts = first_part.split()
                if len(group_parts) >= 2 and group_parts[0].lower() == "admin:subject":
                    group = group_parts[1]
                    subject = parts[1]
                    if len(parts) > 2:  # Если есть еще части в теме
                        subject += ":" + ":".join(parts[2:])
                    
                    if group in default_groups:
                        group_data[group]['subject'] = subject
                        return f"Тема для группы '{group}' обновлена: {subject}"
            
            return "Неверный формат команды. Для стандартных групп используйте: admin:subject группа:тема"

    elif "admin:time" in processed_text:
        # Сначала проверяем, является ли это командой для настройки времени
        if text.startswith("admin:time:"):
            # Обработка для новых групп (admin:time:группа:время)
            # Разделяем первые две части (admin:time)
            prefix = ":".join(text.split(":", 2)[:2])
            # Получаем остаток строки после admin:time:
            remainder = text[len(prefix)+1:]
            # Находим первое двоеточие в remainder, это разделитель между группой и временем
            if ":" in remainder:
                separator_index = remainder.find(":")
                group = remainder[:separator_index].strip()
                time = remainder[separator_index+1:].strip()
                
                if group in group_data and group not in default_groups:
                    group_data[group]['time'] = time
                    return f"Время для группы '{group}' обновлено: {time}"
                elif group not in group_data:
                    return f"Группа '{group}' не найдена."
                else:
                    return "Используйте другой формат команды для стандартных групп."
            else:
                return "Неверный формат команды. Используйте: admin:time:группа:время"
        # Стандартный формат для предустановленных групп (admin:time группа:время)
        else:
            parts = text.split(":", 2)
            if len(parts) >= 2:
                # admin:time группа:время (первая часть "admin:time группа", вторая - "время")
                first_part = parts[0]
                group_parts = first_part.split()
                if len(group_parts) >= 2 and group_parts[0].lower() == "admin:time":
                    group = group_parts[1]
                    time = parts[1]
                    if len(parts) > 2:  # Если есть еще части (например, секунды)
                        time += ":" + ":".join(parts[2:])
                    
                    if group in default_groups:
                        group_data[group]['time'] = time
                        return f"Время для группы '{group}' обновлено: {time}"
            
            return "Неверный формат команды. Для стандартных групп используйте: admin:time группа:время"

    elif "admin:next date:" in processed_text:
        global next_date
        next_date = text.split(":", 2)[2].strip()
        return f"Текущая дата: {next_date}"

    elif "admin:next weekday:" in processed_text:
        global next_weekday
        next_weekday = text.split(":", 2)[2].strip()
        return f"Текущий день недели: {next_weekday}"

    elif "admin:clear list" in processed_text:
        clear_registrations()
        return "Все регистрации очищены."

    elif "admin:move group:" in processed_text:
        parts = text.split(":")
        if len(parts) == 4:  # admin:move group:название:позиция
            group_name = parts[2].strip()
            try:
                position = int(parts[3].strip())
                if move_group(group_name, position):
                    return f"Группа '{group_name}' успешно перемещена на позицию {position}."
                else:
                    return f"Группа '{group_name}' не найдена."
            except ValueError:
                return "Неверный формат позиции. Используйте число."
        return "Неверный формат команды. Используйте: admin:move group:название группы:позиция"

    else:
        return "Я не знаю, как ответить на это. Используйте команду /start для вызова главного меню или нажмите на одну из кнопок ниже."


def handle_message(update: Update, context: CallbackContext):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f"User ({update.message.chat.id}) in {message_type} says: '{text}'")

    if message_type == "group":
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, "").strip()
            responce: str = handle_response(new_text, context, update)
        else:
            return
    else:
        responce: str = handle_response(text, context, update)
        print("Registered users:")
        for group, users in registrations.items():
            print(f"- {group}: {', '.join(user.split(', ')[0] for user in users)}")

    print('Bot say: ' + responce)
    update.message.reply_text(responce)


def error(update: Update, context: CallbackContext):
    print(f"Update {update} caused error {context.error}")


def add_new_group(group_name: str):
    """Добавляет новую группу в словари group_data и registrations"""
    if group_name not in group_data:
        group_data[group_name] = {'subject': '', 'time': ''}
        registrations[group_name] = set()
        return True
    return False


if __name__ == '__main__':
    print('Бот запускается...')
    updater = Updater(API_TOKEN)
    dispatcher = updater.dispatcher

    # Commands
    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CommandHandler('satrt', start_command))  # Обработка опечатки
    dispatcher.add_handler(CommandHandler('closest_meeting', closest_meeting))
    dispatcher.add_handler(CommandHandler('check_assignments', check_assignments))
    dispatcher.add_handler(CommandHandler('cancel_assignment', cancel_command))
    dispatcher.add_handler(CommandHandler('cancel', cancel_command))  # Альтернативная команда для отмены
    # Work in progress
    dispatcher.add_handler(CommandHandler('admin', admin_command))
    dispatcher.add_handler(CommandHandler('change_subject_for_beginner', change_subject_for_beginner))
    dispatcher.add_handler(CommandHandler('change_subject_for_pro', change_subject_for_pro))
    dispatcher.add_handler(CommandHandler('change_time_for_beginner', change_time_for_beginner))
    dispatcher.add_handler(CommandHandler('change_time_for_pro', change_time_for_pro))
    dispatcher.add_handler(CommandHandler('change_next_friday', change_next_friday))
    dispatcher.add_handler(CommandHandler('change_subject_for_online', change_subject_for_online))
    dispatcher.add_handler(CommandHandler('change_time_for_online', change_time_for_online))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Conf scheduler
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Europe/Moscow'))
    scheduler.add_job(keepalive, 'interval', minutes=150)
    scheduler.start()

    # Buttons
    dispatcher.add_handler(CallbackQueryHandler(button))

    # Messages
    dispatcher.add_handler(MessageHandler(Filters.text, handle_message))

    # Errors
    dispatcher.add_error_handler(error)
    
    # Polls the bot
    print('Опрос начат...')
    updater.start_polling(poll_interval=1)
    updater.idle()
