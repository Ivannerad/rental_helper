Plan project and write this implemention plan in PROJECT_PLAN.MD.

The project is telegram user bot that answer on users messages like rental agent.

The project should have:
1) Telegram bot
 - Admin pannel there user can add telegram account to connect this account to chat bot. 
 - Ability start/stop chat bot on account.
 - Bound public group for each account. 
 - Able to handle many users.
 - Viewing schedule. 

2) Telegram user bot
 - Get messages from telegram users and send it to rabbitmq to chat bot 
 - Get rabbitmq messages from chat bot and if it have action to forward messages from telegram group it should forward this message to user.

3) Chat bot
 - Get messages from telegram user bots by rabbitmq.
 - Make requests to LLM with context.
 - Send response with message or action to telegram user bot via rabbitmq.
 - Language is Russian.

Chat bot have 4 stage of user conversation:
 1) Collecting. Сlarifying rent estate needs like budget, location (center/west/east/north), number of rooms.
 2) Serching. Searching estate options and if user reject options search new. 
 3) Viewing. Ask user about time and date then user want to see estate option.
 4) Upsell. Search one similar option in location and ask user to see this option.  

