# Import built-in Python modules and methods
import os
from time import sleep
from datetime import datetime

# Import third-party modules, classes and methods
from telethon import TelegramClient
from telethon.tl.types import InputPeerChannel, Chat
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

    def __init__(self):

        # Connect the Telegram client
        self.client = TelegramClient('ssn', api_id=self.get_api_id(), api_hash=self.get_api_hash())
        self.client.connect()

    @staticmethod
    def get_api_id():
        """Returns an api identifier from the global variables"""
        return os.environ['API_ID']

    @staticmethod
    def get_api_hash():
        """Returns an api hash code from the global variables"""
        return os.environ['API_HASH']

    @staticmethod
    def get_chains():
        """Returns a list of all channels from database"""
        return ChannelChain.query.all()

    def check_auth(self):
        return self.client.is_user_authorized()

    def logout(self):
        """"
        Recreates a new Telegram session
        """
        try:
            self.client.log_out()
            self.client.disconnect()
            with open('ssn.session', 'w') as f:
                f.write('')

            self.client = TelegramClient('ssn', api_id=self.get_api_id(), api_hash=self.get_api_hash())
            self.client.connect()
        except Exception as e:
            return str(e)

    def send_code(self, phone):
        """
        Check if session has already been created (and returns False) 
        or sends confirmation code and returns True if this's not.
        """

        if self.check_auth():
            self.logout()

        try:
            self.client.send_code_request(phone=phone)
            return True
        except Exception as e:
            return str(e)

    def confirm(self, code):
        # Sign in a user using received code
        return self.client.sign_in(code=code)

    def get_all_chats(self):
        """
        Tries to receive all user's chats and return them.
        If the query catches an error the method returns an empty list
        """
        try:
            return self.client(GetAllChatsRequest(except_ids=[])).chats
        except Exception as e:
            print(e)
            return []

    @staticmethod
    def get_channel_chain(chats, name_from, name_to):
        """
        Finds needed channels and save them into the ChannelChain class object.
        If there is an error the method return an error string
        """
        chain = ChannelChain()

        for chat in chats:
            try:
                if chat.title == name_from:
                    chain.from_id = chat.id
                    chain.from_title = chat.title
                    chain.from_access_hash = chat.access_hash
                elif chat.title == name_to:
                    chain.to_id = chat.id
                    chain.to_title = chat.title
                    chain.to_access_hash = chat.access_hash
            except Exception as e:
                return str(e)

        # Check if a channel is not found and return an error text
        if (chain.from_title is None) or (chain.to_title is None):
            return 'Канал с данным названием не найден. Проверьте, что оба названия введены верно.'

        return chain

    def get_last_message(self, chain):
        """Returns the last message id of outgoing channel."""

        # Create incoming channel peer for requesting the last message id
        peer = InputPeerChannel(channel_id=int(chain.from_id),
                                access_hash=int(chain.from_access_hash))

        # Get all messages
        messages = self.client(GetHistoryRequest(
            peer=peer,
            offset_id=0,
            offset_date=datetime.now(),
            add_offset=0,
            limit=1,
            max_id=-1,
            min_id=0
        )).messages

        # Return the last message id
        if len(messages) > 0:
            return messages[0].id

        return 0

    @staticmethod
    def save_into_db(chain):
        """
        Saves the chain into the database and commits db changes.  
        """
        try:
            db.session.add(chain)
            db.session.commit()
            return True
        except Exception as e:
            return str(e)

    def add_chain(self, from_channel_name, to_channel_name):
        """
        Creates a new chain of channels
        :param from_channel_name: str - Outgoing channel name
        :param to_channel_name: str - Incoming channel name
        :return: True if operation is successful or an error string  
        """

        try:
            # Get all chats
            chats = self.get_all_chats()

            # Get chain of needed channels
            chain = self.get_channel_chain(chats=chats, name_from=from_channel_name, name_to=to_channel_name)
            if not isinstance(chain, ChannelChain):
                return chain

            # Set the last message identifier into the ChannelChain class object
            chain.last_message= self.get_last_message(chain=chain)

            # Save chain into db
            return self.save_into_db(chain=chain)
        except Exception as e:
            return str(e)

    def new_message_ids(self, peer, last_id):
        try:
            msgs = self.client(GetHistoryRequest(
                            peer=peer,
                            offset_id=0,
                            offset_date=datetime.now(),
                            add_offset=0,
                            limit=1000,
                            max_id=-1,
                            min_id=last_id
                        )).messages
            ids = [msg.id for msg in msgs][::-1]
            return ids
        except Exception as e:
            print(str(e))
            return []

    def forward_messages(self, messages, peer_from, peer_to):
        try:
            self.client(ForwardMessagesRequest(
                from_peer=peer_from,
                to_peer=peer_to,
                id=messages
            ))
        except Exception as e:
            return str(e)

        return True

    def run_loop(self):
        while True:
            for chain in self.get_chains():

                # Setup peers for the incoming channel and the outgoing channel
                peer_from = InputPeerChannel(channel_id=int(chain.from_id), access_hash=int(chain.from_access_hash))
                peer_to = InputPeerChannel(channel_id=int(chain.to_id), access_hash=int(chain.to_access_hash))

                # Get the last forwarded message id
                last_message_id = chain.last_message

                # Get messages for forwarding
                messages_to_fwd = self.new_message_ids(peer=peer_from, last_id=last_message_id)

                # Forward all messages
                if len(messages_to_fwd) > 0:
                    if self.forward_messages(messages=messages_to_fwd, peer_from=peer_from, peer_to=peer_to) is True:

                        # Update the last message id in the database
                        chain.last_message = max(messages_to_fwd)
                        self.save_into_db(chain=chain)

                # Anti-flood sleeping
                sleep(2)

            sleep(2)

    def start_monitoring(self):
        """Monitors new messages in channels and forward them into needed channels.
        """
        if not self.check_auth():
            self.client = TelegramClient('ssn', api_id=self.get_api_id(), api_hash=self.get_api_hash())
            self.client.connect()

        self.run_loop()
