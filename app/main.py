from agents import function_tool, Agent
from dotenv import load_dotenv

load_dotenv()

@function_tool
def get_weather(location: str):
    return f"The weather in {location} is cloudy"

agent = Agent(
    "Assistent",
    instructions="You are a helpful assistant, and always answer with good energy",
    model
    
)
    
if __name__ == "__main__":
    user_input = input("Enter your message: ")
