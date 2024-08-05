import nltk
from nltk.chat.util import Chat, reflections
from chatbot.patterns_handler import PatternsHandler


class ChatBot:
    def __init__(self, db_handler, utils):
        self.chat_bot = None
        self.utils = utils
        self.db_handler = db_handler
        self.patterns_handler = PatternsHandler(db_handler)
        self._initialize_bot()

    def _initialize_bot(self):
        patterns = self.patterns_handler.get_patterns()
        self.chat_bot = Chat(patterns, reflections)
        self.utils.logger.info("ChatBot initialized successfully")

    def respond(self, user_input):
        if self.chat_bot:
            response = self.chat_bot.respond(user_input.lower())
            if not response:
                return "Sorry, I don't have information on that specific topic. If you need help, type 'help' in the chat."
            return response

        self.utils.logger.error("ChatBot was not initialized properly")
        return "Something went wrong... Please try again later"
