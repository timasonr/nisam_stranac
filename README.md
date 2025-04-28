# "Nisam stranac" Conversation Club Bot

Telegram bot for managing registrations for Serbian language conversation clubs at "Nisam stranac" school.

## Features

- Registration of participants for conversation clubs of various levels
- View information about upcoming meetings
- Management of topics and meeting times
- Dynamic creation of new groups
- Administrative interface for managing groups and registrations
- Automatic notifications to administrators about registrations and cancellations

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root directory and add the following variables:
```
API_TOKEN=your_bot_token_here
BOT_USERNAME=@your_bot_username
ADMIN_USER_ID=your_admin_telegram_id
ADMIN_PASSWORD=your_admin_password
TARGET_USER_ID=your_target_telegram_id
OWNER_USER_ID=your_owner_telegram_id
MAX_PARTICIPANTS=200
```

## Launch

Run the bot with the command:
```bash
python main.py
```

## User Commands

1. `/start` - start working with the bot
2. `/menu` - open main menu
3. `/closest_meeting` - information about the next meeting
4. `/check_assignments` - check your registrations
5. `/cancel` - cancel registration

## Administrative Commands

1. `admin:show list` - show the list of registered participants
2. `admin:subject beginner:new topic` - change the topic for beginners
3. `admin:subject pro:new topic` - change the topic for intermediate students
4. `admin:subject advanced:new topic` - change the topic for advanced students
5. `admin:subject online:new topic` - change the topic for online sessions
6. `admin:time beginner:new time` - change the time for beginners
7. `admin:time pro:new time` - change the time for intermediate students
8. `admin:time advanced:new time` - change the time for advanced students
9. `admin:time online:new time` - change the time for online sessions
10. `admin:next date:new date` - change the meeting date
11. `admin:next weekday:weekday` - change the meeting weekday
12. `admin:clear list` - clear the list of registrations
13. `admin:add group:group name` - add a new group
14. `admin:delete group:group name` - delete a group
15. `admin:subject:group name:new topic` - change the topic for a new group
16. `admin:time:group name:new time` - change the time for a new group
17. `admin:move group:group name:position` - move a group to the specified position

## Security

- All sensitive data (bot token, administrator IDs, passwords) are stored in the `.env` file
- The `.env` file is excluded from the repository via `.gitignore`
- Make sure to keep your `.env` file secure and never commit it to the repository

## License

MIT
