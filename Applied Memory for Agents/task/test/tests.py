from hstest import StageTest, TestedProgram, CheckResult, dynamic_test
import ast
import json

class ConversationManagerTests(StageTest):
    """Blackbox tests for ConversationManager using hstest."""

    @dynamic_test
    def test_keep_all_strategy_basic(self):
        """Test keep_all strategy keeps all messages."""
        pr = TestedProgram()
        pr.start('--strategy', 'keep_all')

        # Add multiple messages and end
        pr.execute("Hello")
        pr.execute("Hi there!")
        pr.execute("How are you?")
        output = pr.execute("END")

        # Parse output as list of dicts
        try:
            messages = ast.literal_eval(output)
        except:
            return CheckResult.wrong(f"Could not parse output: {output}. JSON expected.")

        if len(messages) != 3:
            return CheckResult.wrong(f"keep_all strategy should keep all 3 messages, got {len(messages)}")

        if "Hello" not in str(messages):
            return CheckResult.wrong("First message not found in context")

        return CheckResult.correct()

    @dynamic_test
    def test_keep_all_strategy_many_messages(self):
        """Test keep_all strategy with many messages."""
        pr = TestedProgram()
        pr.start('--strategy', 'keep_all')

        # Add 20 messages
        for i in range(20):
            pr.execute(f"Message{i}")

        output = pr.execute("END")

        try:
            messages = ast.literal_eval(output)
        except:
            return CheckResult.wrong(f"Could not parse output: {output}")

        if len(messages) != 20:
            return CheckResult.wrong(f"keep_all should keep all 20 messages, got {len(messages)}")

        # Check first and last messages exist
        output_str = str(messages)
        if "Message0" not in output_str:
            return CheckResult.wrong("First message should be retained")

        if "Message19" not in output_str:
            return CheckResult.wrong("Last message should be retained")

        return CheckResult.correct()

    @dynamic_test
    def test_sliding_window_default_size(self):
        """Test sliding_window strategy with default window size (10)."""
        pr = TestedProgram()
        pr.start('--strategy', 'sliding_window')

        # Add 15 messages
        for i in range(15):
            pr.execute(f"Msg{i}")

        output = pr.execute("END")

        try:
            messages = ast.literal_eval(output)
        except:
            return CheckResult.wrong(f"Could not parse output: {output}")

        if len(messages) != 10:
            return CheckResult.wrong(f"sliding_window should keep only 10 messages with default size, got {len(messages)}")

        # Should have messages 5-14
        output_str = str(messages)
        if "Msg5" not in output_str:
            return CheckResult.wrong("Should keep message from position 5")

        if "Msg4" in output_str:
            return CheckResult.wrong("Should not keep message from position 4")

        if "Msg14" not in output_str:
            return CheckResult.wrong("Should keep the last message")

        return CheckResult.correct()

    @dynamic_test
    def test_sliding_window_custom_size(self):
        """Test sliding_window strategy with custom window size."""
        pr = TestedProgram()
        pr.start('--strategy', 'sliding_window', '--window-size', '3')

        # Add 6 messages
        for i in range(6):
            pr.execute(f"Item{i}")

        output = pr.execute("END")

        try:
            messages = ast.literal_eval(output)
        except:
            return CheckResult.wrong(f"Could not parse output: {output}")

        if len(messages) != 3:
            return CheckResult.wrong(f"sliding_window with size=3 should keep only 3 messages, got {len(messages)}")

        # Should have last 3: Item3, Item4, Item5
        output_str = str(messages)
        if "Item3" not in output_str:
            return CheckResult.wrong("Should keep Item3")

        if "Item2" in output_str:
            return CheckResult.wrong("Should not keep Item2")

        return CheckResult.correct()

    @dynamic_test
    def test_sliding_window_below_limit(self):
        """Test sliding_window when message count is below window size."""
        pr = TestedProgram()
        pr.start('--strategy', 'sliding_window', '--window-size', '10')

        # Add only 3 messages
        pr.execute("First")
        pr.execute("Second")
        pr.execute("Third")

        output = pr.execute("END")

        try:
            messages = ast.literal_eval(output)
        except:
            return CheckResult.wrong(f"Could not parse output: {output}")

        if len(messages) != 3:
            return CheckResult.wrong(f"Should keep all 3 messages when below window size, got {len(messages)}")

        return CheckResult.correct()

    @dynamic_test
    def test_summarize_below_threshold(self):
        """Test summarize strategy when below threshold."""
        pr = TestedProgram()
        pr.start('--strategy', 'summarize', '--threshold', '10')

        # Add 5 messages (below threshold)
        for i in range(5):
            pr.execute(f"Text{i}")

        output = pr.execute("END")

        try:
            messages = ast.literal_eval(output)
        except:
            return CheckResult.wrong(f"Could not parse output: {output}")

        if len(messages) != 5:
            return CheckResult.wrong(f"Should keep all messages when below threshold, got {len(messages)}")

        output_str = str(messages).lower()
        if "summary" in output_str:
            return CheckResult.wrong("Should not summarize when below threshold")

        return CheckResult.correct()

    @dynamic_test
    def test_summarize_exceeds_threshold(self):
        """Test summarize strategy when exceeding threshold."""
        pr = TestedProgram()
        pr.start('--strategy', 'summarize', '--threshold', '10')

        # Add 11 messages to exceed threshold
        for i in range(11):
            pr.execute(f"Topic{i}")

        output = pr.execute("END")

        try:
            messages = ast.literal_eval(output)
        except:
            return CheckResult.wrong(f"Could not parse output: {output}")

        output_str = str(messages).lower()
        if "summary" not in output_str:
            return CheckResult.wrong("Should create summary when exceeding threshold")

        # After summarization: 1 summary + remaining half (6) = 7 messages
        if len(messages) != 7:
            return CheckResult.wrong(f"Should have 7 messages after summarization (1 summary + 6 remaining), got {len(messages)}")

        # Check if first message has system role
        if messages[0]['role'] != 'system':
            return CheckResult.wrong("Summary should have role 'system'")

        return CheckResult.correct()

    @dynamic_test
    def test_summarize_with_keywords(self):
        """Test that summarize extracts keywords from messages."""
        pr = TestedProgram()
        pr.start('--strategy', 'summarize', '--threshold', '6')

        # Add messages with clear keywords
        pr.execute("Talk about python programming")
        pr.execute("Python is great")
        pr.execute("Python functions")
        pr.execute("Functions use def")
        pr.execute("Python classes")
        pr.execute("Classes keyword")
        pr.execute("More questions")

        output = pr.execute("END")

        try:
            messages = ast.literal_eval(output)
        except:
            return CheckResult.wrong(f"Could not parse output: {output}")

        output_str = str(messages).lower()
        if "summary" not in output_str:
            return CheckResult.wrong("Should create summary when exceeding threshold")

        # Check that keyword "python" appears in summary
        if "python" not in output_str:
            return CheckResult.wrong("Summary should contain extracted keyword 'python'")

        return CheckResult.correct()

    @dynamic_test
    def test_invalid_strategy(self):
        """Test that invalid strategy produces error."""
        pr = TestedProgram()

        # Try to start with invalid strategy - should fail
        try:
            pr.start('--strategy', 'invalid_strategy_name')
            pr.execute("Hello")
            pr.execute("END")
            # If we got here without exception, the program accepted invalid strategy
            return CheckResult.wrong("Should produce error for invalid strategy")
        except:
            # Expected to fail
            return CheckResult.correct()

    @dynamic_test
    def test_zero_window_size(self):
        """Test sliding window with zero size."""
        pr = TestedProgram()
        pr.start('--strategy', 'sliding_window', '--window-size', '0')

        pr.execute("Message")
        output = pr.execute("END")

        try:
            messages = ast.literal_eval(output)
        except:
            return CheckResult.wrong(f"Could not parse output: {output}")

        if len(messages) != 0:
            return CheckResult.wrong(f"Window size 0 should keep no messages, got {len(messages)}")

        return CheckResult.correct()

    @dynamic_test
    def test_empty_conversation(self):
        """Test operations on empty conversation."""
        pr = TestedProgram()
        pr.start('--strategy', 'keep_all')

        output = pr.execute("END")

        try:
            messages = ast.literal_eval(output)
        except:
            return CheckResult.wrong(f"Could not parse output: {output}")

        if len(messages) != 0:
            return CheckResult.wrong(f"Empty conversation should have 0 messages, got {len(messages)}")

        return CheckResult.correct()

    @dynamic_test
    def test_message_order_preserved(self):
        """Test that message order is preserved."""
        pr = TestedProgram()
        pr.start('--strategy', 'keep_all')

        pr.execute("First")
        pr.execute("Second")
        pr.execute("Third")

        output = pr.execute("END")

        try:
            messages = ast.literal_eval(output)
        except:
            return CheckResult.wrong(f"Could not parse output: {output}")

        if len(messages) != 3:
            return CheckResult.wrong(f"Should have 3 messages, got {len(messages)}")

        # Check order by looking at positions
        output_str = output.lower()
        first_pos = output_str.find("first")
        second_pos = output_str.find("second")
        third_pos = output_str.find("third")

        if first_pos == -1 or second_pos == -1 or third_pos == -1:
            return CheckResult.wrong("All messages should be present")

        if not (first_pos < second_pos < third_pos):
            return CheckResult.wrong("Messages should maintain chronological order")

        return CheckResult.correct()


if __name__ == '__main__':
    ConversationManagerTests().run_tests()
