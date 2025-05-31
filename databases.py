from pymongo import MongoClient

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
            self.client = MongoClient('mongodb://localhost:27017/')
            self.db = self.client['my_database']
            self.warns_collection = self.db['server_warns']
            self.banned_words_collection = self.db['banned_words']
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            self.client = None
            self.db = None
            self.warns_collection = None
            self.banned_words_collection = None
        
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
            result = self.warns_collection.delete_one({
                'server_id': warn.server_id,
                'user_id': warn.user_id
            })
            return result.deleted_count > 0
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
    