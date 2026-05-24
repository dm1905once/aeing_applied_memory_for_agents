from decimal import getcontext

import click
from datetime import datetime
from openai import OpenAI
import os
import dotenv
import json

dotenv.load_dotenv()

client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY")
)


class ConversationManager:
    def __init__(self, strategy: str = "keep_all", **strategy_params):
        self.strategy = strategy
        self.strategy_params = strategy_params
        self.messages = []

    def add_message(self, role: str, content: str) -> None:
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        }
        self.messages.append(message)

        # Apply strategy
        if self.strategy == "keep_all":
            self.messages = keep_all_strategy(self.messages, **self.strategy_params)
        elif self.strategy == "sliding_window":
            self.messages = sliding_window_strategy(self.messages, **self.strategy_params)
        elif self.strategy == "summarize":
            self.messages = summarize_strategy(self.messages, **self.strategy_params)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    def get_context(self) -> list[dict]:
        return self.messages.copy()


def keep_all_strategy(messages: list[dict], **params) -> list[dict]:
    """
    Keep all messages in history.

    Args:
        messages: Current message list
        **params: Unused

    Returns:
        Unmodified message list
    """
    return messages


def sliding_window_strategy(messages: list[dict], window_size: int = 10, **params) -> list[dict]:
    """
    Keep only the last N messages.

    Args:
        messages: Current message list
        window_size: Number of messages to keep
        **params: Additional unused parameters

    Returns:
        Last window_size messages
    """
    if window_size == 0:
        return []
    elif len(messages) > window_size:
        messages = messages[-window_size:]
    return messages


def summarize_strategy(messages: list[dict], threshold: int = 20, **params) -> list[dict]:
    """
    Summarize old messages when count exceeds threshold.

    When messages exceed threshold, replace first half (len(messages) // 2) with a summary message.
    Summary format: "Summary: <summary>"

    To summarize, use gpt-4.1-nano model

    Args:
        messages: Current message list
        threshold: Trigger summarization when exceeding this count
        **params: Additional unused parameters

    Returns:
        Messages with old ones summarized if threshold exceeded
    """
    if len(messages) < threshold:
        return messages
    else:
        messages_to_summarize: list[dict] = messages[:len(messages) // 2]
        remaining_messages: list[dict] = messages[-len(messages) // 2:]
        response = client.responses.create(
            model="gpt-4.1-nano",
            input=[
                {"role": "user", "content": f"Summarize this list of context messages into one string: {messages_to_summarize} "},
            ]
        )
        content_summary: str = response.output_text

        # Create summary message
        summary = {
            "role": "system",
            "content": "Summary: " + content_summary,
            "timestamp": messages_to_summarize[0]["timestamp"]
        }
        return [summary] + remaining_messages


@click.command()
@click.option('--strategy', default='keep_all', help='Memory strategy',
              type=click.Choice(['keep_all', 'sliding_window', 'summarize']))
@click.option('--window-size', default=10, help='Sliding window size', type=int)
@click.option('--threshold', default=20, help='Summarize threshold', type=int)
def run_conversation(strategy: str, **params):
    conversation = ConversationManager(strategy, **params)
    while True:
        user_input = input()
        if user_input == 'END':
            break
        else:
            conversation.add_message('user', user_input)
    print(json.dumps(conversation.get_context(), default=str))


if __name__ == '__main__':
    run_conversation()


