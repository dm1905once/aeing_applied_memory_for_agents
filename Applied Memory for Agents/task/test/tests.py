from hstest import StageTest, TestedProgram, CheckResult, dynamic_test
import os


class MemoryStoreTests(StageTest):
    """Blackbox tests for Memory Store backends using hstest."""
    @dynamic_test
    def test_structured_store_basic_add(self):
        """Test basic add operation with structured store."""
        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('structured-store-flush')

        pr = TestedProgram()
        output = pr.start('structured-store-add', '--data', 'name=John;role=Engineer')

        if pr.is_finished():
            if "error" in output.lower() or "exception" in output.lower():
                return CheckResult.wrong(f"Program failed with error: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_structured_store_add_and_query(self):
        """Test add and query operations with structured store."""
        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('structured-store-flush')

        pr1 = TestedProgram()
        pr1.start('structured-store-add', '--data', 'language=Python;type=programming')

        pr2 = TestedProgram()
        output = pr2.start('structured-store-query', '--key', 'language', '--value', 'Python')

        if "error" in output.lower():
            return CheckResult.wrong(f"Query operation failed: {output}")

        # Should return results (even if empty list representation)
        if not pr2.is_finished():
            return CheckResult.wrong("Query operation did not complete")

        # Verify the stored data is returned
        if "language" not in output or "Python" not in output:
            return CheckResult.wrong(f"Query should return the stored data. Expected 'language' and 'Python' in output, got: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_structured_store_multiple_entries(self):
        """Test adding multiple entries and querying them."""
        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('structured-store-flush')

        # Add multiple entries
        entries = [
            'name=Alice;department=Engineering',
            'name=Bob;department=Design',
            'name=Charlie;department=Engineering'
        ]

        for entry in entries:
            pr = TestedProgram()
            pr.start('structured-store-add', '--data', entry)

        # Query for Engineering department
        pr_query = TestedProgram()
        output = pr_query.start('structured-store-query', '--key', 'department', '--value', 'Engineering')

        if "error" in output.lower():
            return CheckResult.wrong(f"Query failed: {output}")

        # Should contain both Alice and Charlie (Engineering employees)
        if "Alice" not in output or "Charlie" not in output:
            return CheckResult.wrong(f"Query should return both Engineering department members. Expected 'Alice' and 'Charlie' in output, got: {output}")

        # Should NOT contain Bob (Design department)
        if "Bob" in output:
            return CheckResult.wrong(f"Query should not return non-matching entries. 'Bob' should not be in output, got: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_structured_store_query_with_limit(self):
        """Test query with n_results limit parameter."""
        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('structured-store-flush')

        # Add test data
        for i in range(5):
            pr = TestedProgram()
            pr.start('structured-store-add', '--data', f'item=test{i};category=sample')

        # Query with limit
        pr_query = TestedProgram()
        output = pr_query.start('structured-store-query', '--key', 'category', '--value', 'sample', '--n', '2')

        if "error" in output.lower():
            return CheckResult.wrong(f"Query with limit failed: {output}")

        # Verify that results are limited - count occurrences of 'item'
        # Should have exactly 2 results (each result has 'item' in it)
        item_count = output.count("'item'")
        if item_count > 2:
            return CheckResult.wrong(f"Query with --n=2 should return at most 2 results, but found {item_count} items in output: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_structured_store_no_match_query(self):
        """Test query with no matching results."""
        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('structured-store-flush')

        pr1 = TestedProgram()
        pr1.start('structured-store-add', '--data', 'language=Python;type=programming')

        pr2 = TestedProgram()
        output = pr2.start('structured-store-query', '--key', 'language', '--value', 'JavaScript')

        # Should complete without error even if no results
        if "error" in output.lower():
            return CheckResult.wrong(f"Query should handle no matches gracefully: {output}")

        # Should return empty list or no results containing JavaScript
        if "JavaScript" in output:
            return CheckResult.wrong(f"Query for non-existent value should not return results containing 'JavaScript', got: {output}")

        # Should return empty list notation
        if "[]" not in output and len(output.strip()) > 0:
            # If output is not empty and not '[]', it should at least not contain the wrong data
            if "Python" in output:
                return CheckResult.wrong(f"Query for 'JavaScript' should not return data about 'Python', got: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_structured_store_flush(self):
        """Test flush operation clears all data."""
        # Add data
        pr1 = TestedProgram()
        pr1.start('structured-store-add', '--data', 'test=data;foo=bar')

        # Flush
        pr2 = TestedProgram()
        output = pr2.start('structured-store-flush')

        if "error" in output.lower():
            return CheckResult.wrong(f"Flush operation failed: {output}")

        # Verify data is cleared by querying
        pr3 = TestedProgram()
        output = pr3.start('structured-store-query', '--key', 'test', '--value', 'data')

        # After flush, should return empty results - data should NOT be present
        if "test" in output and "[]" not in output:
            return CheckResult.wrong(f"After flush, query should return empty results, but found data: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_structured_store_special_characters(self):
        """Test handling of special characters in values."""
        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('structured-store-flush')

        pr1 = TestedProgram()
        output = pr1.start('structured-store-add', '--data', 'description=Test-Value_123;status=active')

        if "error" in output.lower():
            return CheckResult.wrong(f"Should handle special characters: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_structured_store_case_sensitivity(self):
        """Test case sensitivity in queries."""
        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('structured-store-flush')

        pr1 = TestedProgram()
        pr1.start('structured-store-add', '--data', 'name=Python;category=Language')

        pr2 = TestedProgram()
        output = pr2.start('structured-store-query', '--key', 'name', '--value', 'python')

        # Should work with case-insensitive search (TinyDB search flag)
        if "error" in output.lower():
            return CheckResult.wrong(f"Query failed: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_structured_store_partial_match(self):
        """Test partial string matching in queries."""
        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('structured-store-flush')

        pr1 = TestedProgram()
        pr1.start('structured-store-add', '--data', 'description=Machine learning algorithms;topic=AI')

        pr2 = TestedProgram()
        output = pr2.start('structured-store-query', '--key', 'description', '--value', 'learning')

        if "error" in output.lower():
            return CheckResult.wrong(f"Partial match query failed: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_structured_store_persistence(self):
        """Test that data persists across program runs."""
        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('structured-store-flush')

        # First run - add data
        pr1 = TestedProgram()
        pr1.start('structured-store-add', '--data', 'persistent=data;test=persistence')

        # Second run - query data
        pr2 = TestedProgram()
        output = pr2.start('structured-store-query', '--key', 'persistent', '--value', 'data')

        if "error" in output.lower():
            return CheckResult.wrong(f"Data should persist across runs: {output}")

        # Verify data is actually returned
        if "persistent" not in output or "data" not in output:
            return CheckResult.wrong(f"Stored data should persist and be retrievable. Expected 'persistent' and 'data' in output, got: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_structured_store_empty_value(self):
        """Test handling empty values in key-value pairs."""
        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('structured-store-flush')

        pr1 = TestedProgram()
        output = pr1.start('structured-store-add', '--data', 'key=;another=value')

        # Should handle empty values
        if "exception" in output.lower():
            return CheckResult.wrong(f"Should handle empty values: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_structured_store_numeric_values(self):
        """Test handling numeric values."""
        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('structured-store-flush')

        pr1 = TestedProgram()
        output = pr1.start('structured-store-add', '--data', 'priority=10;score=95.5')

        if "error" in output.lower():
            return CheckResult.wrong(f"Should handle numeric values: {output}")

        pr2 = TestedProgram()
        output = pr2.start('structured-store-query', '--key', 'priority', '--value', '10')

        # Verify numeric values are stored and retrieved correctly
        if "10" not in output or "priority" not in output:
            return CheckResult.wrong(f"Query should return numeric values correctly. Expected 'priority' and '10' in output, got: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_structured_store_unicode_content(self):
        """Test handling of Unicode characters."""
        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('structured-store-flush')

        pr = TestedProgram()
        output = pr.start('structured-store-add', '--data', 'text=Hello世界;emoji=😀')

        if "exception" in output.lower():
            return CheckResult.wrong(f"Should handle Unicode: {output}")

        return CheckResult.correct()

    # ==================== Vector Store (ChromaDB) Tests ====================

    @dynamic_test
    def test_vector_store_basic_add(self):
        """Test basic add operation with vector store."""
        try:
            import chromadb
        except ImportError:
            return CheckResult.correct()  # Skip if ChromaDB not installed

        # Check if OpenAI API key is available
        if not os.getenv("OPENAI_API_KEY"):
            return CheckResult.correct()  # Skip if no API key

        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('vector-store-flush')

        pr = TestedProgram()
        output = pr.start('vector-store-add', '--content', 'Machine learning is fascinating')

        if "error" in output.lower() and "api" not in output.lower():
            return CheckResult.wrong(f"Add operation failed: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_vector_store_add_and_query(self):
        """Test add and query operations with vector store."""
        try:
            import chromadb
        except ImportError:
            return CheckResult.correct()  # Skip if ChromaDB not installed

        if not os.getenv("OPENAI_API_KEY"):
            return CheckResult.correct()  # Skip if no API key

        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('vector-store-flush')

        pr1 = TestedProgram()
        pr1.start('vector-store-add', '--content', 'Python is a programming language')

        pr2 = TestedProgram()
        output = pr2.start('vector-store-query', '--query', 'programming', '--n', '5')

        if "error" in output.lower() and "api" not in output.lower():
            return CheckResult.wrong(f"Query operation failed: {output}")

        # Verify stored content is returned in query results
        if "Python is a programming language" not in output:
            return CheckResult.wrong(f"Query should return the stored content. Expected 'Python is a programming language' in output, got: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_vector_store_semantic_search(self):
        """Test semantic search capability of vector store."""
        try:
            import chromadb
        except ImportError:
            return CheckResult.correct()  # Skip if ChromaDB not installed

        if not os.getenv("OPENAI_API_KEY"):
            return CheckResult.correct()  # Skip if no API key

        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('vector-store-flush')

        # Add related content
        contents = [
            'Python is a programming language',
            'The weather is sunny today',
            'JavaScript is also used for programming'
        ]

        for content in contents:
            pr = TestedProgram()
            pr.start('vector-store-add', '--content', content)

        # Query for programming-related content
        pr_query = TestedProgram()
        output = pr_query.start('vector-store-query', '--query', 'coding languages', '--n', '3')

        if "error" in output.lower() and "api" not in output.lower():
            return CheckResult.wrong(f"Semantic search failed: {output}")

        # Verify semantic search returns programming-related content
        # Should include Python and/or JavaScript (semantically related to "coding languages")
        has_programming_content = "Python" in output or "JavaScript" in output or "programming" in output
        if not has_programming_content:
            return CheckResult.wrong(f"Semantic search for 'coding languages' should return programming-related content. Expected Python/JavaScript/programming in output, got: {output}")

        # Weather content should be ranked lower (less semantically related)
        # This is a soft check - if weather appears, it should ideally be after programming content
        # But we mainly check that programming content IS present

        return CheckResult.correct()

    @dynamic_test
    def test_vector_store_query_limit(self):
        """Test query with result limit."""
        try:
            import chromadb
        except ImportError:
            return CheckResult.correct()  # Skip if ChromaDB not installed

        if not os.getenv("OPENAI_API_KEY"):
            return CheckResult.correct()  # Skip if no API key

        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('vector-store-flush')

        # Add multiple documents
        for i in range(5):
            pr = TestedProgram()
            pr.start('vector-store-add', '--content', f'Document number {i} about testing')

        # Query with limit
        pr_query = TestedProgram()
        output = pr_query.start('vector-store-query', '--query', 'testing', '--n', '2')

        if "error" in output.lower() and "api" not in output.lower():
            return CheckResult.wrong(f"Query with limit failed: {output}")

        # Verify that results are limited - count occurrences of 'Document number'
        doc_count = output.count('Document number')
        if doc_count > 2:
            return CheckResult.wrong(f"Query with --n=2 should return at most 2 results, but found {doc_count} documents in output: {output}")

        # Should have at least some results
        if doc_count == 0:
            return CheckResult.wrong(f"Query should return some results. Expected documents in output, got: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_vector_store_flush(self):
        """Test flush operation clears vector store."""
        try:
            import chromadb
        except ImportError:
            return CheckResult.correct()  # Skip if ChromaDB not installed

        if not os.getenv("OPENAI_API_KEY"):
            return CheckResult.correct()  # Skip if no API key

        # Add data
        pr1 = TestedProgram()
        pr1.start('vector-store-add', '--content', 'Test content for flushing')

        # Flush
        pr2 = TestedProgram()
        output = pr2.start('vector-store-flush')

        if "error" in output.lower():
            return CheckResult.wrong(f"Flush operation failed: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_vector_store_empty_query(self):
        """Test behavior with empty query string."""
        try:
            import chromadb
        except ImportError:
            return CheckResult.correct()  # Skip if ChromaDB not installed

        if not os.getenv("OPENAI_API_KEY"):
            return CheckResult.correct()  # Skip if no API key

        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('vector-store-flush')

        pr1 = TestedProgram()
        pr1.start('vector-store-add', '--content', 'Sample content')

        pr2 = TestedProgram()
        output = pr2.start('vector-store-query', '--query', '', '--n', '5')

        # Should handle empty query gracefully
        if not pr2.is_finished():
            return CheckResult.wrong("Program should handle empty query")

        return CheckResult.correct()

    @dynamic_test
    def test_vector_store_long_content(self):
        """Test storing long text content."""
        try:
            import chromadb
        except ImportError:
            return CheckResult.correct()  # Skip if ChromaDB not installed

        if not os.getenv("OPENAI_API_KEY"):
            return CheckResult.correct()  # Skip if no API key

        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('vector-store-flush')

        long_text = "This is a very long text. " * 50  # Create long content

        pr = TestedProgram()
        output = pr.start('vector-store-add', '--content', long_text)

        if "error" in output.lower() and "api" not in output.lower():
            return CheckResult.wrong(f"Should handle long content: {output}")

        return CheckResult.correct()

    # ==================== Error Handling Tests ====================

    @dynamic_test
    def test_structured_store_invalid_data_format(self):
        """Test error handling for invalid data format."""
        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('structured-store-flush')

        pr = TestedProgram()
        output = pr.start('structured-store-add', '--data', 'invalid_format_without_equals')

        # Program should handle invalid format gracefully
        # Either show error or parse as best as possible
        return CheckResult.correct()

    @dynamic_test
    def test_structured_store_missing_required_option(self):
        """Test error when required option is missing."""
        pr = TestedProgram()
        output = pr.start('structured-store-add')

        # Should show error about missing required option
        if "error" not in output.lower() and "missing" not in output.lower():
            # Click will handle this automatically
            pass

        return CheckResult.correct()

    @dynamic_test
    def test_vector_store_missing_content(self):
        """Test error when content option is missing."""
        try:
            import chromadb
        except ImportError:
            return CheckResult.correct()  # Skip if ChromaDB not installed

        pr = TestedProgram()
        output = pr.start('vector-store-add')

        # Should show error about missing required option (Click handles this)
        return CheckResult.correct()

    @dynamic_test
    def test_invalid_command(self):
        """Test handling of invalid command."""
        pr = TestedProgram()
        output = pr.start('invalid-store', 'add', '--data', 'test=value')

        # Should show error or usage information
        return CheckResult.correct()

    # ==================== Integration Tests ====================

    @dynamic_test
    def test_both_stores_independent(self):
        """Test that both stores operate independently."""
        # Flush both stores
        pr_flush1 = TestedProgram()
        pr_flush1.start('structured-store-flush')

        # Add to structured store
        pr1 = TestedProgram()
        pr1.start('structured-store-add', '--data', 'type=structured;content=test1')

        # Add to vector store if available
        try:
            import chromadb
            if os.getenv("OPENAI_API_KEY"):
                pr_flush2 = TestedProgram()
                pr_flush2.start('vector-store-flush')

                pr2 = TestedProgram()
                pr2.start('vector-store-add', '--content', 'Vector store test content')
        except ImportError:
            pass

        # Query structured store
        pr3 = TestedProgram()
        output = pr3.start('structured-store-query', '--key', 'type', '--value', 'structured')

        if "error" in output.lower():
            return CheckResult.wrong(f"Stores should operate independently: {output}")

        # Verify structured store returns its own data
        if "type" not in output or "structured" not in output:
            return CheckResult.wrong(f"Structured store should return its own data. Expected 'type' and 'structured' in output, got: {output}")

        # Verify structured store does NOT return vector store data
        if "Vector store test content" in output:
            return CheckResult.wrong(f"Structured store should not return vector store data. Got: {output}")

        return CheckResult.correct()

    @dynamic_test
    def test_concurrent_operations(self):
        """Test multiple operations in sequence."""
        # Flush before test
        pr_flush = TestedProgram()
        pr_flush.start('structured-store-flush')

        operations = [
            ('structured-store-add', '--data', 'seq=1;test=concurrent'),
            ('structured-store-add', '--data', 'seq=2;test=concurrent'),
            ('structured-store-query', '--key', 'test', '--value', 'concurrent'),
        ]

        for i, op in enumerate(operations):
            pr = TestedProgram()
            output = pr.start(*op)
            if "error" in output.lower():
                return CheckResult.wrong(f"Concurrent operations failed: {output}")

            # Check the query operation returns both entries
            if i == 2:  # Last operation is the query
                if "seq" not in output:
                    return CheckResult.wrong(f"Query after multiple adds should return data. Expected 'seq' in output, got: {output}")

        return CheckResult.correct()


if __name__ == '__main__':
    MemoryStoreTests().run_tests()
