"""
chat_history.py

This module provides functions to insert and retrieve chat history for users in a MongoDB database.
"""
from pymongo.database import Database


class ChatHistoryInterface:
    """
    A class to interact with chat history in a MongoDB database.

    This class provides methods to insert, retrieve, and clear chat history
    for users in a MongoDB database. It requires a MongoDB database object
    to be passed during initialization.

    Attributes:
        db (Database): The MongoDB database object used for storing chat history.
    """

    def __init__(self, database: Database):
        self.db = database

    def insert_chat_history(self, username: str, new_chat_history: list[list[str]]) -> None:
        """
        Insert or update the chat history for a user in the MongoDB database.

        Args:
            username (str): The username to associate with the chat history.
            new_chat_history (list[list[str]]): A list of chat history entries, where each entry is a list containing a
                prompt and an answer.
        """
        history_collection = self.db['history']
        history_collection.create_index([("username", 1)], unique=True)

        result = history_collection.update_one(
            {'username': username},
            {'$push': {'chat_history': {'$each': new_chat_history}}},
            upsert=True
        )
        # TODO: add logging

        if result.matched_count == 0:
            print(f"New user added: {username}.")
        else:
            print(f"Existing user: {username} updated.")

    def retrieve_chat_history(self, username: str) -> list[dict[str, str]]:
        """
        Retrieve the chat history for a user from the MongoDB database. Note that this is structured to support the
        OpenAI GPT chat history format.

        Args:
            username (str): The username whose chat history is to be retrieved.

        Returns:
            list[dict[str, str]]: A list of dictionaries representing the chat history, where each dictionary contains a
                role ('user' or 'assistant') and the corresponding text.
        """
        history_collection = self.db['history']

        # Find the document for the given username
        document = history_collection.find_one({'username': username})
        # TODO: add logging

        # Check if the document was found
        if document:
            print(f"Found chat history for username: {username}")
            # Return the chat history if available
            history = document['chat_history']
            formatted_history = []
            for prompt, answer in history:
                formatted_history.append({'role': 'user', 'content': prompt})
                formatted_history.append({'role': 'assistant', 'content': answer})
            return formatted_history

        else:
            # Return an empty list if no history is found
            print(f"No chat history found for username: {username}")
            return []

    def clear_chat_history(self, username: str) -> None:
        """
        Clear the chat history for a specific user from the MongoDB database.

        Args:
            username (str): The username whose chat history should be cleared.
        """
        history_collection = self.db['history']

        result = history_collection.delete_one({'username': username})
        if result.deleted_count > 0:
            print(f"Cleared chat history for user '{username}' successfully.")
        else:
            print(f"No chat history found for username: '{username}'.")


# Example usage:
if __name__ == "__main__":
    from utils import setup_mongo_db

    db = setup_mongo_db()
    chat_history_interface = ChatHistoryInterface(db)
    chat_history_interface.insert_chat_history('boss', [['hi', 'yes']])
    chat_history_interface.insert_chat_history('boss', [['s', 'yes'], ['a', 'aaaa']])
    print(chat_history_interface.retrieve_chat_history('boss'))
    chat_history_interface.clear_chat_history('boss')
    print(chat_history_interface.retrieve_chat_history('boss'))
    chat_history_interface.clear_chat_history('boss')
