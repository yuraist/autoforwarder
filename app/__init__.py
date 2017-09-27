import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from rq import Queue
from worker import conn

# Setup an app
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

# Setup a database
db = SQLAlchemy(app)

# Setup a queue
q = Queue('default', connection=conn)

# Create a Monitor instance with connected instance of the TelegramClient class
from app.monitor import Monitor
monitor = Monitor()

from app import views, models
