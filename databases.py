from pymongo import MongoClient
import os
from dotenv import load_dotenv
import datetime
import discord

class server_setting:
    def __init__(self, server_id: int, auto_moderation: bool = False, show_auto_moderation_messages: bool = False, audit_channel: int = None):
        self.server_id : int = server_id
        self.auto_moderation : bool = auto_moderation
        self.show_auto_moderation_messages : bool = show_auto_moderation_messages
        self.audit_channel : int = audit_channel

    def from_dict(data: dict):
        instance = server_setting(data['server_id'])
        instance.auto_moderation = data.get('auto_moderation', False)
        instance.show_auto_moderation_messages = data.get('show_auto_moderation_messages', False)
        instance.audit_channel = data.get('audit_channel', None)
        return instance
    
class caveman_challenge:
    def __init__(self):
        self.start_time: datetime.datetime = discord.utils.utcnow()
        self.fail_time: datetime.datetime | None = None

    @staticmethod
    def ensure_utc(dt: datetime.datetime | None) -> datetime.datetime | None:
        if dt is None:
            return None

        # If datetime is naive, assume it is UTC and attach timezone
        if dt.tzinfo is None:
            return dt.replace(tzinfo=datetime.timezone.utc)

        # If it already has timezone info, convert it to UTC
        return dt.astimezone(datetime.timezone.utc)

    @staticmethod
    def from_dict(data: dict):
        instance = caveman_challenge()

        start_time = data.get('start_time')
        fail_time = data.get('fail_time')

        instance.start_time = caveman_challenge.ensure_utc(start_time) or discord.utils.utcnow()
        instance.fail_time = caveman_challenge.ensure_utc(fail_time)

        return instance

class server_warn:
    def __init__(self, server_id: int, user_id: int):
        self.server_id = server_id
        self.user_id = user_id
        self.count = 1
    
    @staticmethod
    def from_dict(data: dict):
        instance = server_warn(data['server_id'], data['user_id'])
        instance.count = data.get('count', 0)
        return instance
    
class banned_word:
    def __init__(self, word: str, server_id: int):
        self.word = word
        self.server_id = server_id
    
    @staticmethod
    def from_dict(data: dict):
        return banned_word(data['word'], data['server_id'])
    
class database:
    def __init__(self):
        try:
            self.client = MongoClient(os.getenv('MongoDB_URI'))
            self.db = self.client['my_database']
            self.warns_collection = self.db['server_warns']
            self.banned_words_collection = self.db['banned_words']
            self.server_settings_collection = self.db['server_settings']
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            self.client = None
            self.db = None
            self.warns_collection = None
            self.banned_words_collection = None
            self.server_settings_collection = None

    #get 10 results of caveman challenges sorted by longest time to fail
    def get_caveman_challenges(self) -> list[caveman_challenge]:
        try:
            challenges = self.db['caveman_challenges'].find()
            sorted_challenges = sorted(challenges, key=lambda x: (x['fail_time'] - x['start_time']) if x['fail_time'] else datetime.timedelta.max, reverse=True)
            return [caveman_challenge.from_dict(challenge) for challenge in sorted_challenges[:10]]
        except Exception as e:
            print(f"Error retrieving caveman challenges: {e}")
            return []

    def add_caveman_challenge(self) -> bool:
        try:
            challenge_data = {
                'start_time': discord.utils.utcnow(),
                'fail_time': None
            }
            self.db['caveman_challenges'].insert_one(challenge_data)
            return True
        except Exception as e:
            print(f"Error adding caveman challenge: {e}")
            return False
    
    #get the last caveman challenge and return it as a caveman_challenge object
    def get_caveman_challenge(self) -> caveman_challenge | None:
        try:
            last_challenge = self.db['caveman_challenges'].find_one(sort=[('start_time', -1)])
            if last_challenge:
                return caveman_challenge.from_dict(last_challenge)
            return None
        except Exception as e:
            print(f"Error retrieving caveman challenge: {e}")
            return None
        
    #get the last caveman challenge and set the fail time to now
    def fail_caveman_challenge(self) -> bool:
        try:
            last_challenge = self.db['caveman_challenges'].find_one(sort=[('start_time', -1)])
            if last_challenge and not last_challenge.get('fail_time'):
                self.db['caveman_challenges'].update_one(
                    {'_id': last_challenge['_id']},
                    {'$set': {'fail_time': discord.utils.utcnow()}}
                )
                return True
            return False
        except Exception as e:
            print(f"Error failing caveman challenge: {e}")
            return False

    def add_server_setting(self, setting: server_setting) -> bool:
        try:
            existing_setting = self.server_settings_collection.find_one({
                'server_id': setting.server_id
            })
            if existing_setting:
                self.server_settings_collection.update_one(
                    {'_id': existing_setting['_id']},
                    {'$set': {
                        'auto_moderation': setting.auto_moderation,
                        'audit_channel': setting.audit_channel
                    }}
                )
                return True
            setting_data = {
                'server_id': setting.server_id,
                'auto_moderation': setting.auto_moderation,
                'audit_channel': setting.audit_channel
            }
            self.server_settings_collection.insert_one(setting_data)
            return True
        except Exception as e:
            print(f"Error adding server setting: {e}")
            return False
        
    def remove_server_setting(self, server_id: int) -> bool:
        try:
            result = self.server_settings_collection.delete_one({
                'server_id': server_id
            })
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error removing server setting: {e}")
            return False
        
    def get_server_setting(self, server_id: int) -> server_setting | None:
        try:
            setting_data = self.server_settings_collection.find_one({
                'server_id': server_id
            })
            if setting_data:
                return server_setting.from_dict(setting_data)
            return None
        except Exception as e:
            print(f"Error retrieving server setting: {e}")
            return None
        
    def edit_server_setting(self, setting: server_setting) -> bool:
        try:
            result = self.server_settings_collection.update_one(
                {'server_id': setting.server_id},
                {'$set': {
                    'auto_moderation': setting.auto_moderation,
                    'audit_channel': setting.audit_channel,
                    'show_auto_moderation_messages': setting.show_auto_moderation_messages
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error editing server setting: {e}")
            return False
        
    def get_warns(self, server_id: int, user_id: int) -> server_warn | None:
        try:
            warn_data = self.warns_collection.find_one({
                'server_id': server_id,
                'user_id': user_id
            })
            if warn_data:
                return server_warn.from_dict(warn_data)
            return None
        except Exception as e:
            print(f"Error retrieving warns: {e}")
            return None
        
    def add_warn(self, warn: server_warn) -> bool:
        try:
            #check if warn already exists
            existing_warn = self.warns_collection.find_one({
                'server_id': warn.server_id,
                'user_id': warn.user_id
            })
            if existing_warn:
                # Increment the count if it exists
                new_count = existing_warn['count'] + 1
                self.warns_collection.update_one(
                    {'_id': existing_warn['_id']},
                    {'$set': {'count': new_count}}
                )
                return True
            warn_data = {
                'server_id': warn.server_id,
                'user_id': warn.user_id,
                'count': warn.count
            }
            self.warns_collection.insert_one(warn_data)
            return True
        except Exception as e:
            print(f"Error adding warn: {e}")
            return False
        
    def remove_warn(self, warn: server_warn) -> bool:
        try:
            existing = self.warns_collection.find_one({
                'server_id': warn.server_id,
                'user_id': warn.user_id
            })
            if not existing:
                return False

            current_count = existing.get('count', 0)
            if current_count <= 1:
                result = self.warns_collection.delete_one({'_id': existing['_id']})
                return result.deleted_count > 0

            result = self.warns_collection.update_one(
                {'_id': existing['_id']},
                {'$set': {'count': current_count - 1}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error removing warn: {e}")
            return False
        
    def add_banned_word(self, word: banned_word) -> bool:
        try:
            # Check if the word already exists
            existing_word = self.banned_words_collection.find_one({
                'word': word.word,
                'server_id': word.server_id
            })
            if existing_word:
                return False
            word_data = {
                'word': word.word,
                'server_id': word.server_id
            }
            self.banned_words_collection.insert_one(word_data)
            return True
        except Exception as e:
            print(f"Error adding banned word: {e}")
            return False
        
    def does_word_contain_banned_word(self, content: str, server_id: int) -> bool:
        try:
            if server_id is None:
                return False
            banned_words = self.banned_words_collection.find({
                'server_id': server_id
            })
            for banned_word in banned_words:
                if banned_word['word'] in content:
                    return True
            return False
        except Exception as e:
            print(f"Error checking banned words in content: {e}")
            return False
        
    def is_word_banned(self, word: str, server_id: int) -> bool:
        try:
            if server_id is None:
                return False
            return self.banned_words_collection.find_one({
                'word': word,
                'server_id': server_id
            }) is not None 
        except Exception as e:
            print(f"Error checking if word is banned: {e}")
            return False
        
    def remove_banned_word(self, word: str, server_id: int) -> bool:
        try:
            result = self.banned_words_collection.delete_one({
                'word': word,
                'server_id': server_id
            })
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error removing banned word: {e}")
            return False
    
    def remove_all_banned_words(self, server_id: int) -> bool:
        try:
            result = self.banned_words_collection.delete_many({
                'server_id': server_id
            })
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error removing all banned words: {e}")
            return False
    
