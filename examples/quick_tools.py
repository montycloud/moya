from typing import Dict, Any
from datetime import datetime
import json

class QuickTools:

    user_id = "42"
    user_name = "Marvin"

    @staticmethod
    def get_conversation_context()->str:
        """
        Get the current context for the conversation like thread ID, user id and user name.

        :return: The conversation context
        """
        # Thread id will be like user_id-date_hours (24 hour format) so a new thread is formed every hour.
        thread_id = f"{QuickTools.user_id}-{datetime.now().strftime("%Y%m%d%H")}"
        return json.dumps({
            "thread_id": thread_id,
            "user_id": "42",
            "user_name": "Marvin"
        })
    
    @staticmethod
    def set_user_id(user_id: str)->str:
        """
        Set the user ID for the conversation.

        :param user_id: The user ID
        :return: Success message
        """
        QuickTools.user_id = user_id
        return f"User ID set to {user_id}."

