from openai import OpenAI
import os
import dotenv
from tinydb import TinyDB, Query
from enum import Enum

dotenv.load_dotenv()

CLIENT = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY")
)

class ContextManager:
    def __init__(self):
        self.messages: list[dict] = []
        
    def add_user_message(self, message: str):
        self.messages.append({
            "role": "user", "content": message
        })
    
    def update_messages(self, messages: list[dict]):
        self.messages = messages
        
    def get_repr(self):
        """Function for showing context for easier solving of optional tasks"""
        msgs = []
        for elem in self.messages:
            if type(elem) is dict:
                if 'role' in elem:
                    msgs.append(elem['role'] + ': ' + elem['content'][:15] + '...')
                else:
                    msgs.append(elem['type'] + ': ' + elem['output'][:15] + '...')
            else:
                msgs.append(str(elem.type))
        return 'Context:\n\t' + "\n\t".join(msgs) + '\n-------'
    
    def get_context(self) -> list[dict]:
        return self.messages.copy()

    def compact(self):
        """
        OPTIONAL TASK
        
        If you use get_repr() function after each call to LLM, 
        you will see that context is getting bigger and bigger. Not only with messages, but also with function calls and their outputs. 
        
        Your task is to implement compact() function to remove all non-message items from context.
        """
        pass
    
    def reset(self):
        self.messages = []
        
class MatchType(Enum):
    EQ = "eq"
    CONTAINS = "contains"
    
  
class TasksStore:
    def __init__(self):
        self.db = TinyDB('tasks.json')
        
    def create_task(self, name: str, status: str) -> str:
        """
        TODO: implement task creation
        
        Returns:
            str: Task creation message
        """
        pass
        
    def find_task(self, key: str, value: str, match: MatchType = MatchType.EQ) -> str:
        """
        TODO: implement task search by field value or by field value pattern.
        
        Tip 1: use tinydb search functionality. 
        Also, use regex for pattern matching (MatchType.Contains).

        Tip 2: remember to select match by value, not by name.
        i.e.
        -> match == MatchType.EQ is not correct
        -> match == MatchType.EQ.value is correct
        
        Returns:
            str: Task search result
        """
        pass
        
    def update_task_status(self, name: str, new_status: str) -> str:
        """
        TODO: implement task status update

        Tip: use self.db.update(...) with 2 params: field and query.
        Field - field to update
        Query - ability to select portion of data to update
        
        Returns:
            str: Task status update message
        """
        pass
  
    def flush(self):
        """
        TODO: clear database 
        """
        pass
    
    
class PersonalAssistant:
    def __init__(self):
        """
        TODO: fill tools list with correct tool descriptions. Match tool names to function names. And tool parameters to function parameters.
        
        As a hint, check how tool_result is obtained during tool call phase.
        """
        self.tools = [
            {
                "type": "function",
                "name": "find_task",
            },
            {
                "type": "function",
                "name": "create_task",
            },
            {
                "type": "function",
                "name": "update_task_status",
            }
        ]
        # to store data
        self.tasks_store = TasksStore()
        
        self.tool_map = {
            "find_task": self.tasks_store.find_task,
            "create_task": self.tasks_store.create_task,
            "update_task_status": self.tasks_store.update_task_status
        }
        # to manage context
        self.context_manager = ContextManager()
        
    def send_message(self, message: str) -> str:
        self.context_manager.add_user_message(message)
        context = self.context_manager.get_context()
        context = self._call_llm(context)
        self.context_manager.update_messages(context)
        return context[-1].content[0].text
    
    def _call_llm(self, messages: list[dict]) -> list[dict]:
        response = CLIENT.responses.create(
            model="gpt-4o-mini",
            input=messages,
            tools=self.tools
        )
        messages += response.output
        
        if response.output[0].type == "message":
            return messages

        # if not message, execute tool calls
        for item in response.output:
            if item.type == "function_call":
                tool_result = self.tool_map[item.name](
                    **eval(item.arguments)
                )
                """
                TODO: Fill parameters of messages.append to make it work. messages.append requires tool result in special format. Check openai responses docs for more info
                """
                messages.append(
                    
                )
        """
        TODO: Change return value to make it work
        
        Something seems wrong here. 
        If we return the context messages right away, something will break. What can we do here, to continue the loop?
        """
        return messages
    
    def flush(self):
        self.tasks_store.flush()
        self.context_manager.reset()
        

def main():
    """Main conversation loop"""
    assistant = PersonalAssistant()
    while True:
        try:
            user_input = input("User: ").strip()
            if not user_input:
                continue
            
            # Process special commands
            if user_input == "/q":
                break
            elif user_input == "/flush":
                assistant.flush()
                print("[INFO] Flushed")
                continue
            
            # Process normal message
            response = assistant.send_message(user_input)
            print(f"Assistant: {response}")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
