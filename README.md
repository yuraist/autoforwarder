# Autoforwarder

### About the project

Autoforwarder is an application based on Telegram API. 
The main function of the app is forward messages from secret channels in the Telegram messenger into your own chats.

### How does it work

- I use the **Flask** framework for the application backend. It handles web requests and launches monitoring of new messages.
- I use the **Telethon** library that allows to quickly work with Telegram Client API.
- I use the **Redis Queue** (redis-rq) for working with background tasks.
- I use the **PostgreSQL** database and Flask-SQLAlchemy to store information about user's channels.