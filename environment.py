import os

class Environment:
    
    @staticmethod
    def is_production():
        return os.environ.get('SERVER_SOFTWARE','').startswith('Goog')
        
    @staticmethod
    def is_development():
         return os.environ.get('SERVER_SOFTWARE','').startswith('Devel')

    @staticmethod
    def twitter_credentials():
        if Environment.is_development():
            return {
                'consumer_key': '42mPrPcIeaaNr9cqlFA',
                'consumer_secret': '17c9BZNkvJ7D300WErI4cexeab304SweRcmzB7b9dJc',
                }
        else:
            return {
                'consumer_key': 'QQN4ne5yAfqqV0BSffgwKA',
                'consumer_secret': 'i47YAhBhKi9KrWT8o00MAEeU4jBnAgSrKEpxDDIM8',
            }
