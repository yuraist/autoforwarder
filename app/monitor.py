# Import built-in Python modules and methods
import os
from time import sleep
from datetime import datetime

# Import third-party modules, classes and methods
from telethon import TelegramClient
from telethon.tl.types import InputPeerChannel
from telethon.tl.functions.messages import GetHistoryRequest, ForwardMessagesRequest, GetAllChatsRequest

# Import my objects and classes
from app import db
from app.models import ChannelChain


class Monitor:
    """
    The Monitor class is used for monitoring new messages in channels and forwarding them into needed channels.
    Use this class only if you have valid session for a user. If you have not the session, create it using phone number 
     and code sent by Telegram (confirm it using web-form).
    """
    api_id = os.environ['API_ID']
    api_hash = os.environ['API_HASH']

    def __init__(self):

        # Get channels chains
        self.chains = ChannelChain.query.all()

        # Connect the Telegram client
        self.client = TelegramClient('ssn', api_id=self.api_id, api_hash=self.api_hash)
        self.client.connect()

    def update_chains(self):
        # Get all chains for now
        self.chains = ChannelChain.query.all()

    def send_code(self, phone):
        """Check if session has already been created (and returns False) 
        or sends confirmation code and returns True if it's not.
        """
        self.client.disconnect()
        self.client = TelegramClient('ssn', api_id=self.api_id, api_hash=self.api_hash)
        self.client.connect()

        if self.client.is_user_authorized():
            return False

        self.client.send_code_request(phone=phone)
        return True

    def confirm(self, code):
        # Sign in a user
        return self.client.sign_in(code=code)

    def add_chain(self, from_channel_name, to_channel_name):
        # Request all user's chats
        chats = self.client(GetAllChatsRequest(except_ids=[])).chats

        # Create a channel chain
        channel_chain = ChannelChain()

        # Get needed channels info
        for chat in chats:
            if from_channel_name in chat.title:
                channel_chain.from_title = chat.title
                channel_chain.from_id = chat.id
                channel_chain.from_access_hash = chat.access_hash
            elif to_channel_name in chat.title:
                channel_chain.to_title = chat.title
                channel_chain.to_id = chat.id
                channel_chain.to_access_hash = chat.access_hash

        # Check if a channel is not found and return an error text
        if (channel_chain.from_title is None) or (channel_chain.to_title is None):
            return 'Канал с данным названием не найден. Проверьте, что оба названия введены верно.'

        # Call the save_channel_chain method to add the last message property and save the chain into db
        return self.save_channel_chain(channel_chain)

    def save_channel_chain(self, channel_chain):
        # Create incoming channel peer for requesting the last message id
        peer = InputPeerChannel(channel_id=int(channel_chain.from_id), access_hash=int(channel_chain.from_access_hash))

        # Get the last message
        last_message = self.client(GetHistoryRequest(
            peer=peer,
            offset_id=0,
            offset_date=datetime.now(),
            add_offset=0,
            limit=1,
            max_id=-1,
            min_id=0
        )).messages

        # Get the last message id and set it to the channel_chain
        if len(last_message) > 0:
            channel_chain.last_message = last_message[0].id
        else:
            channel_chain.last_message = 0

        # Add the channel chain into the database
        db.session.add(channel_chain)
        db.session.commit()

        # Update the chain list
        self.update_chains()
        print(f'New chains: {self.chains}')
        return True

    def start_monitoring(self, phone):
        """Monitors new messages in channels and forward them into needed channels.
        """
        if not self.client.is_user_authorized():
            self.client = TelegramClient('ssn', api_id=self.api_id, api_hash=self.api_hash)
            self.client.connect()

        while True:
            for chain in self.chains:
                try:
                    # Setup peers for incoming channel and outgoing channel
                    from_id = int(chain.from_id)
                    from_access_hash = int(chain.from_access_hash)
                    to_id = int(chain.to_id)
                    to_access_hash = int(chain.to_access_hash)

                    from_peer = InputPeerChannel(channel_id=from_id, access_hash=from_access_hash)
                    to_peer = InputPeerChannel(channel_id=to_id, access_hash=to_access_hash)

                    last_message = chain.last_message

                    # Get new messages (not forwarded)
                    new_messages = self.client(GetHistoryRequest(
                        peer=from_peer,
                        offset_id=0,
                        offset_date=datetime.now(),
                        add_offset=0,
                        limit=1000,
                        max_id=-1,
                        min_id=last_message
                    )).messages

                    # Get the new message ids for further forwarding
                    ids = [message.id for message in new_messages][::-1]

                    if len(ids) > 0:
                        # Forward new messages
                        self.client(ForwardMessagesRequest(
                            from_peer=from_peer,
                            to_peer=to_peer,
                            id=ids
                        ))

                        # Update last forwarded message in the database
                        max_id = max(ids)
                        chain.last_message = max_id

                        db_session = db.object_session(chain)
                        if db_session is None:
                            db_session = db.session
                        db_session.add(chain)
                        db_session.commit()
                except Exception as e:
                    print(str(e))
                    return e

                # Check if new chains has been added or old has been removed
                self.update_chains()

                # Sleep for anti-flood
                sleep(3)
            # Sleep for 2 second
            sleep(2)
