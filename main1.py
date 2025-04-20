import asyncio
import emoji
import requests
import pytz
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.constants import ParseMode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, \
    CallbackContext

# Loading environment variables from .env file
load_dotenv()

# Getting token and admin ID from environment variables
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))  # Admin ID
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "adminadminadmin")
API_TOKEN = os.getenv("API_TOKEN")  # Telegram bot token
BOT_USERNAME = os.getenv("BOT_USERNAME")
TARGET_USER_ID = int(os.getenv("TARGET_USER_ID", ADMIN_USER_ID))
OWNER_USER_ID = int(os.getenv("OWNER_USER_ID", ADMIN_USER_ID))
MAX_PARTICIPANTS = int(os.getenv("MAX_PARTICIPANTS", "100"))  # Maximum number of participants in each group
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


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_USER_ID:
        return
    await admin_menu_command(update, context)


async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == 'add_new_group':
        await query.edit_message_text(
            "Enter the name of the new group in the format:\nadmin:add group:group name"
        )
    elif query.data == 'delete_group':
        # Create a list of buttons for all groups
        keyboard = []
        for group in group_data.keys():
            keyboard.append([InlineKeyboardButton(f"Delete {group}", callback_data=f"confirm_delete:{group}")])
        keyboard.append([InlineKeyboardButton("Back", callback_data="admin_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Select a group to delete:", reply_markup=reply_markup)
    elif query.data.startswith('confirm_delete:'):
        group_name = query.data.split(':')[1]
        if delete_group(group_name):
            await query.edit_message_text(f"Group '{group_name}' successfully deleted.")
        else:
            await query.edit_message_text(f"Group '{group_name}' not found.")
    elif query.data in [group.lower() for group in group_data.keys()]:
        # Dynamically call the registration function for the selected group
        group_name = next(group for group in group_data.keys() if group.lower() == query.data)
        await sign_up_command(update, context, group_name)
    elif query.data == 'cancel':
        await cancel_command(update, context)
    elif query.data == 'closest_meeting':
        await closest_meeting(update, context)
    elif query.data == 'check_assignments':
        await check_assignments(update, context)
    elif query.data == 'menu':
        await menu_command(update, context)
    elif query.data == 'admin_menu':
        await admin_menu_command(update, context)
    else:
        await query.edit_message_text("This option does not exist, please choose again.")


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Buttons and menu items
    keyboard = [
        [
            InlineKeyboardButton("Menu", callback_data="menu")
        ],
        [
            InlineKeyboardButton("Next meeting", callback_data="closest_meeting")
        ]
    ]
    
    # List of standard groups
    default_groups = {'Beginners', 'Intermediate', 'Advanced', 'Online'}
    
    # Add buttons for all groups
    for group in group_data.keys():
        button_text = f"Register for {group}" if group in default_groups else f"Register for {group}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=group.lower())])
    
    # Add the cancel registration button at the end
    keyboard.append([InlineKeyboardButton("Cancel registration", callback_data="cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"""
Hello!{emoji.emojize(':waving_hand:')}

I am a helper bot for registering for the conversation club at
<b>"Nisam stranac"</b> school.

* Conversation clubs are held every week.{emoji.emojize(':spiral_calendar:')}
* Address: Futoška 1a, 5th floor, office 510.{emoji.emojize(':round_pushpin:')}\n
Use the buttons below to navigate the bot.\n
The <b>"Next meeting"</b> button will tell you about the topics of future conversation clubs.\n
Friends, if you can't make it, please cancel your registration.""", reply_markup=reply_markup,
        parse_mode=ParseMode.HTML)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /menu command."""
    keyboard = []
    # List of standard groups
    default_groups = {'Beginners', 'Intermediate', 'Advanced', 'Online'}
    
    for group in group_data.keys():
        button_text = f"Register for {group}" if group in default_groups else f"Register for {group}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=group.lower())])
    keyboard.append([InlineKeyboardButton("Cancel registration", callback_data="cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Menu", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("Menu", reply_markup=reply_markup)


async def closest_meeting(update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /when_is_closest_meeting command."""
    keyboard = []
    # List of standard groups
    default_groups = {'Beginners', 'Intermediate', 'Advanced', 'Online'}
    
    for group in group_data.keys():
        button_text = f"Register for {group}" if group in default_groups else f"Register for {group}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=group.lower())])
    keyboard.append([InlineKeyboardButton("Menu", callback_data="menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    global next_date
    
    text = f"Next meeting is on <b>{next_weekday}</b>, <b>{next_date}</b>.\n\n"
    for group, data in group_data.items():
        group_text = f"for {group}" if group in default_groups else group
        text += f"Topic {group_text} at <b>{data['time']}</b>:\n{data['subject']}\n\n"
    
    if update.message:
        await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


async def sign_up_command(update: Update, context: ContextTypes.DEFAULT_TYPE, group_name: str):
    """Universal function for registration in any group"""
    user_name = update.effective_user.full_name
    user_tag = update.effective_user.username
    user_name_n_tag = f"{user_name}, @{user_tag}"
    global next_date
    
    # List of standard groups
    default_groups = {'Beginners', 'Intermediate', 'Advanced', 'Online'}
    
    keyboard = [
        [
            InlineKeyboardButton("Next meeting", callback_data="closest_meeting")
        ],
        [
            InlineKeyboardButton("Menu", callback_data="menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Format text based on group type
    group_text = f"for {group_name}" if group_name in default_groups else group_name

    if user_name_n_tag in registrations[group_name]:
        if update.message:
            await update.message.reply_text(f"You are already registered for the meeting {group_text}.",
                                            reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(text=f"You are already registered for the meeting {group_text}.",
                                                          reply_markup=reply_markup)
    elif registrations[group_name].__len__() >= MAX_PARTICIPANTS:
        if update.message:
            await update.message.reply_text(f"Meetings for {group_text} are full.", reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(text=f"Meetings for {group_text} are full.",
                                                          reply_markup=reply_markup)
    else:
        registrations[group_name].add(user_name_n_tag)
        if update.message:
            await update.message.reply_text(
                f"""You have successfully registered for the meeting {group_text}
{next_date} at {group_data[group_name]['time']}.""",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Cancel registration", callback_data="cancel")],
                     [InlineKeyboardButton("Menu", callback_data="menu")]]
                ))
            send_message(chat_id=TARGET_USER_ID,
                         text=f"{user_name} - registered for the meeting {group_text} {next_date}")
            send_message(chat_id=OWNER_USER_ID,
                         text=f"{user_name} - registered for the meeting {group_text} {next_date}")
        else:
            await update.callback_query.edit_message_text(
                f"""You have successfully registered for the meeting {group_text}
{next_date} at {group_data[group_name]['time']}.""",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Cancel registration", callback_data="cancel")],
                     [InlineKeyboardButton("Menu", callback_data="menu")]]
                )
            )
            send_message(chat_id=TARGET_USER_ID,
                         text=f"{user_name} - registered for the meeting {group_text} {next_date}")
            send_message(chat_id=OWNER_USER_ID,
                         text=f"{user_name} - registered for the meeting {group_text} {next_date}")


async def check_assignments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /check_assignments command."""
    user_name = update.effective_user.full_name
    user_tag = update.effective_user.username
    user_name_n_tag = f"{user_name}, @{user_tag}"
    global next_date
    keyboard = [
        [
            InlineKeyboardButton("Cancel registration", callback_data="cancel")
        ],
        [
            InlineKeyboardButton("Menu", callback_data="menu")
        ]
    ]
    keyboard2 = [
        [
            InlineKeyboardButton("Next meeting", callback_data="closest_meeting")
        ],
        [
            InlineKeyboardButton("Menu", callback_data="menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_markup2 = InlineKeyboardMarkup(keyboard2)

    is_registered_beginner = user_name_n_tag in registrations['Beginners']
    is_registered_pro = user_name_n_tag in registrations['Intermediate']

    if is_registered_beginner and is_registered_pro:
        # User is signed up for both meetings
        if update.message:
            await update.message.reply_text(
                f"You are registered for both meetings on Friday, {next_date}:\n"
                f"* For beginners in {time_for_beginner}.\n"
                f"* For continuers in {time_for_pro}.", reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(
                f"You are registered for both meetings on Friday, {next_date}:\n"
                f"* For beginners in {time_for_beginner}.\n"
                f"* For continuers in {time_for_pro}.", reply_markup=reply_markup)
    elif is_registered_beginner:
        # User is only signed up for beginner meeting
        if update.message:
            await update.message.reply_text(
                f"You are registered for the beginner meeting on Friday, {next_date} at {time_for_beginner}.",
                reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(
                f"You are registered for the beginner meeting on Friday, {next_date} at {time_for_beginner}.",
                reply_markup=reply_markup)
    elif is_registered_pro:
        # User is only signed up for pro meeting
        if update.message:
            await update.message.reply_text(
                f"You are registered for the pro meeting on Friday, {next_date} at {time_for_pro}.",
                reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(
                f"You are registered for the pro meeting on Friday, {next_date} at {time_for_pro}.",
                reply_markup=reply_markup)
    else:
        # User is not signed up for any meetings
        if update.message:
            await update.message.reply_text("You are not registered for any meetings.", reply_markup=reply_markup2)
        else:
            await update.callback_query.edit_message_text("You are not registered for any meetings.",
                                                          reply_markup=reply_markup2)


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /cancel command."""
    user_name = update.effective_user.full_name
    user_tag = update.effective_user.username
    user_name_n_tag = f"{user_name}, @{user_tag}"
    global next_date
    keyboard = [
        [
            InlineKeyboardButton("Next meeting", callback_data="closest_meeting")
        ],
        [
            InlineKeyboardButton("Menu", callback_data="menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Check all groups
    for group_name in group_data.keys():
        if user_name_n_tag in registrations[group_name]:
            registrations[group_name].remove(user_name_n_tag)
            send_message(chat_id=TARGET_USER_ID,
                          text=f"{user_name} - canceled registration for {group_name} {next_date}")
            send_message(chat_id=OWNER_USER_ID,
                          text=f"{user_name} - canceled registration for {group_name} {next_date}")
            if update.message:
                await update.message.reply_text("You are no longer registered for any meetings.", reply_markup=reply_markup)
            else:
                await update.callback_query.edit_message_text(text="You are no longer registered for any meetings.", reply_markup=reply_markup)
            return

    # If the user was not found in any group
    if update.message:
        await update.message.reply_text("You are no longer registered for any meetings.", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text="You are no longer registered for any meetings.", reply_markup=reply_markup)


# Admin commands
async def admin_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /admin_menu command."""
    keyboard = [
        [
            InlineKeyboardButton("Add new group", callback_data="add_new_group"),
        ],
        [
            InlineKeyboardButton("Delete group", callback_data="delete_group"),
        ],
        [
            InlineKeyboardButton("Change topic for beginners", callback_data="change_subject_for_beginner"),
        ],
        [
            InlineKeyboardButton("Change topic for continuers", callback_data="change_subject_for_pro"),
        ],
        [
            InlineKeyboardButton("Change topic for online", callback_data="change_subject_for_online"),
        ],
        [
            InlineKeyboardButton("Change time for beginners", callback_data="change_time_for_beginner"),
        ],
        [
            InlineKeyboardButton("Change time for continuers", callback_data="change_time_for_pro"),
        ],
        [
            InlineKeyboardButton("Change time for online", callback_data="change_time_for_online"),
        ],
        [
            InlineKeyboardButton("Change date", callback_data="change_next_friday"),
        ],
        [
            InlineKeyboardButton("Back", callback_data="menu")
        ]
    ]
    admin_menu_keyboard = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Choose action:", reply_markup=admin_menu_keyboard)
    else:
        await update.callback_query.edit_message_text("Choose action:", reply_markup=admin_menu_keyboard)
    print('Admin menu opened')


async def change_subject_for_beginner(update, context):
    """Handles the /change_subject_for_beginner command."""
    split_message = update.message.text.split(":")
    global subject_for_beginner
    subject_for_beginner = split_message[2].capitalize()
    await update.message.reply_text(f"Current topic for beginners: {subject_for_beginner}")


async def save_subject_for_beginner(update, context):
    pass


async def change_subject_for_pro(update, context):
    """Handles the /change_subject_for_pro command."""
    split_message = update.message.text.split(":")
    global subject_for_pro
    subject_for_pro = split_message[2].capitalize()
    await update.message.reply_text(f"Current topic for continuers: {subject_for_pro}")


async def save_subject_for_pro(update, context):
    pass


async def change_time_for_beginner(update, context):
    pass


async def save_time_for_beginner(update, context):
    pass


async def change_time_for_pro(update, context):
    pass


async def save_time_for_pro(update, context):
    pass


async def change_next_friday(update, context):
    pass


async def save_next_friday(update, context):
    pass


async def change_subject_for_online(update, context):
    """Handles the /change_subject_for_online command."""
    split_message = update.message.text.split(":")
    global subject_for_online
    subject_for_online = split_message[2].capitalize()
    await update.message.reply_text(f"Current topic for online: {subject_for_online}")


async def change_time_for_online(update, context):
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


def handle_response(text: str, context: ContextTypes.DEFAULT_TYPE, update: Update) -> str:
    """Handles admin commands."""
    processed_text = text.lower()
    # List of standard groups
    default_groups = {'Beginners', 'Intermediate', 'Advanced', 'Online'}

    if "admin:show list" in processed_text:
        result = ""
        for group, users in registrations.items():
            result += f"{group}:\n{', '.join(users)}\n\n"
        return result

    elif "admin:add group:" in processed_text:
        group_name = text.split(":", 2)[2].strip()
        if add_new_group(group_name):
            return f"Group '{group_name}' successfully added."
        else:
            return f"Group '{group_name}' already exists."

    elif "admin:delete group:" in processed_text:
        group_name = text.split(":", 2)[2].strip()
        if delete_group(group_name):
            return f"Group '{group_name}' successfully deleted."
        else:
            return f"Group '{group_name}' not found."

    elif "admin:subject" in processed_text:
        parts = text.split(":")
        # Проверяем формат команды для новых групп (admin:subject:группа:тема)
        if len(parts) == 4 and parts[1].strip() == "subject":
            group = parts[2].strip()
            subject = parts[3].strip()
            if group in group_data and group not in default_groups:
                group_data[group]['subject'] = subject
                return f"Topic for group '{group}' updated: {subject}"
            elif group not in group_data:
                return f"Group '{group}' not found."
            else:
                return "Use a different command format for standard groups."
        # Стандартный формат для предустановленных групп (admin:subject группа:тема)
        elif len(parts) == 3:
            group = parts[1].strip()
            subject = parts[2].strip()
            if group in default_groups:
                group_data[group]['subject'] = subject
                return f"Topic for group '{group}' updated: {subject}"
        return "Invalid command format"

    elif "admin:time" in processed_text:
        parts = text.split(":")
        # Проверяем формат команды для новых групп (admin:time:группа:время)
        if len(parts) == 4 and parts[1].strip() == "time":
            group = parts[2].strip()
            time = parts[3].strip()
            if group in group_data and group not in default_groups:
                group_data[group]['time'] = time
                return f"Time for group '{group}' updated: {time}"
            elif group not in group_data:
                return f"Group '{group}' not found."
            else:
                return "Use a different command format for standard groups."
        # Стандартный формат для предустановленных групп (admin:time группа:время)
        elif len(parts) == 3:
            group = parts[1].strip()
            time = parts[2].strip()
            if group in default_groups:
                group_data[group]['time'] = time
                return f"Time for group '{group}' updated: {time}"
        return "Invalid command format"

    elif "admin:next date:" in processed_text:
        global next_date
        next_date = text.split(":", 2)[2].strip()
        return f"Current date: {next_date}"

    elif "admin:next weekday:" in processed_text:
        global next_weekday
        next_weekday = text.split(":", 2)[2].strip()
        return f"Current day of the week: {next_weekday}"

    elif "admin:clear list" in processed_text:
        clear_registrations()
        return "Registrations cleared."

    elif "admin:move group:" in processed_text:
        parts = text.split(":")
        if len(parts) == 4:  # admin:move group:название:позиция
            group_name = parts[2].strip()
            try:
                position = int(parts[3].strip())
                if move_group(group_name, position):
                    return f"Group '{group_name}' successfully moved to position {position}."
                else:
                    return f"Group '{group_name}' not found."
            except ValueError:
                return "Invalid position format. Use a number."
        return "Invalid command format. Use: admin:move group:group name:position"

    else:
        return "I don't know how to respond to that."


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text(responce)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")


def add_new_group(group_name: str):
    """Добавляет новую группу в словари group_data и registrations"""
    if group_name not in group_data:
        group_data[group_name] = {'subject': '', 'time': ''}
        registrations[group_name] = set()
        return True
    return False


if __name__ == '__main__':
    print('Bot starting...')
    application = Application.builder().token(API_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('closest_meeting', closest_meeting))
    application.add_handler(CommandHandler('check_assignments', check_assignments))
    application.add_handler(CommandHandler('cancel_assignment', cancel_command))
    # Work in progress
    application.add_handler(CommandHandler('admin', admin_command))
    application.add_handler(CommandHandler('change_subject_for_beginner', change_subject_for_beginner))
    application.add_handler(CommandHandler('change_subject_for_pro', change_subject_for_pro))
    application.add_handler(CommandHandler('change_time_for_beginner', change_time_for_beginner))
    application.add_handler(CommandHandler('change_time_for_pro', change_time_for_pro))
    application.add_handler(CommandHandler('change_next_friday', change_next_friday))
    application.add_handler(CommandHandler('change_subject_for_online', change_subject_for_online))
    application.add_handler(CommandHandler('change_time_for_online', change_time_for_online))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Conf scheduler
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Europe/Moscow'))
    scheduler.add_job(keepalive, 'interval', minutes=150)
    scheduler.start()

    # Buttons
    application.add_handler(CallbackQueryHandler(button))

    # Messages
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    application.add_error_handler(error)
    # Polls the bot
    print('Polling...')
    application.run_polling(poll_interval= 1)
