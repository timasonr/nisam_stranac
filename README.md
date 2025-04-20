# "Nisam stranac" Conversation Club Bot

Telegram bot for managing registrations for Serbian language conversation clubs at "Nisam stranac" school.

## Features

- Registration of participants for conversation clubs of various levels
- View information about upcoming meetings
- Management of topics and meeting times
- Dynamic creation of new groups
- Administrative interface for managing groups and registrations

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file and add the following data:
```
API_TOKEN=your_bot_token
ADMIN_USER_ID=your_telegram_id
BOT_USERNAME=@your_bot_username
```

## Launch

Run the bot with the command:
```bash
python main1.py
```

## Administrative commands

The bot supports the following administrative commands:

1. `admin:show list` - show the list of registered participants
2. `admin:subject beginner:new topic` - change the topic for beginners
3. `admin:subject pro:new topic` - change the topic for continuing students
4. `admin:subject advanced:new topic` - change the topic for advanced students
5. `admin:subject online:new topic` - change the topic for online sessions
6. `admin:time beginner:new time` - change the time for beginners
7. `admin:time pro:new time` - change the time for continuing students
8. `admin:time advanced:new time` - change the time for advanced students
9. `admin:time online:new time` - change the time for online sessions
10. `admin:next date:new date` - change the meeting date
11. `admin:next weekday:weekday` - change the meeting weekday
12. `admin:clear list` - clear the list of registered participants
13. `admin:add group:group name` - add a new group
14. `admin:delete group:group name` - delete a group
15. `admin:subject:group name:new topic` - change the topic for a new group
16. `admin:time:group name:new time` - change the time for a new group
17. `admin:move group:group name:position` - move a group to the specified position

## Security

Confidential data (bot token, administrator ID) are stored in the `.env` file, which is not included in the repository.

## License

MIT
