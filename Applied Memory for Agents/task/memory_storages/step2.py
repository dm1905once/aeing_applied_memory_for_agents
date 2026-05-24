import click
import chromadb
import uuid
from openai import OpenAI
from tinydb import TinyDB, Query
import os
from typing import List


class StructuredStore:
    """TODO: implement with TinyDB"""
    def __init__(self):
        pass
    
    def store(self, content: dict):
        pass
    
    def query(self, key: str, value: str, n_results: int = 5) -> List[dict]:
        pass
    
    def flush(self):
        pass


class VectorStore:
    """TODO: implement with ChromaDB"""
    def __init__(self):
        self.vectorizer = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        pass
    
    def store(self, content: str):
        pass
    
    def query(self, query: str, n_results: int = 5) -> List[str]:
        pass
    
    def flush(self):
        pass
    
    def _embed(self, text: str) -> List[float]:
        """Supporting funciton to generate embeddings"""
        response = self.vectorizer.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding


@click.command('vector-store-add')
@click.option("--content", "content", help="Add a memory with this content", required=True)
def vector_store_add(content: str=None):
    VectorStore().store(content)

@click.command('vector-store-query')
@click.option("--query", "query", help="Search for memories matching this query", required=True)
@click.option("--n", "n", default=5, help="Number of results to return")
def vector_store_query(query: str=None, n: int=5):
    print(VectorStore().query(query, n_results=n))

@click.command('vector-store-flush')
def vector_store_flush():
    VectorStore().flush()


@click.command('structured-store-add')
@click.option("--data", "data", help="Add a memory with this data format: key1=value1;key2=value2", required=True)
def structured_store_add(data: str=None):
    # print("Adding to structured store...")
    try:
        data = data.split(';')
        data = {key: value for key, value in (item.split('=') for item in data)}
        StructuredStore().store(data)
    except Exception as e:
        print(f"Error adding to structured store: {e}")

@click.command('structured-store-query')
@click.option("--key", "key", help="Search for memories matching this key", required=True)
@click.option("--value", "value", help="Search for memories containing this value", required=True)
@click.option("--n", "n", default=5, help="Number of results to return")
def structured_store_query(key: str=None, value: str=None, n: int=5):
    # print("Querying structured store...")
    print(StructuredStore().query(key, value, n_results=n))

@click.command('structured-store-flush')
def structured_store_flush():
    # print("Flushing structured store...")
    StructuredStore().flush()


@click.group()
def cli():
    """Memory storage CLI with vector and structured stores"""
    pass


# Register all commands
cli.add_command(vector_store_add)
cli.add_command(vector_store_query)
cli.add_command(vector_store_flush)
cli.add_command(structured_store_add)
cli.add_command(structured_store_query)
cli.add_command(structured_store_flush)


if __name__ == "__main__":
    cli()
