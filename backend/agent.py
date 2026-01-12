# agent.py
class SimpleAgent:
    
    def think(self, user_input: str) -> str:
        user_input = user_input.lower()

        if "hello" in user_input:
            return "Hey! I am your FastAPI agent 👋"

        if "weather" in user_input:
            return "I can't check real weather yet, but it's always sunny in code 😄"

        if "bye" in user_input:
            return "Goodbye bro 👋"

        return "I don't understand that yet."
    
