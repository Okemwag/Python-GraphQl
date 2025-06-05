# GraphQL Client Examples with Python

import asyncio
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.requests import RequestsHTTPTransport
import requests

# --- Basic HTTP Client (using requests) ---
class SimpleGraphQLClient:
    def __init__(self, endpoint: str, headers: Optional[Dict[str, str]] = None):
        self.endpoint = endpoint
        self.headers = headers or {}
    
    def execute(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query synchronously"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        response = requests.post(
            self.endpoint,
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# --- Advanced GQL Client ---
class AdvancedGraphQLClient:
    def __init__(self, endpoint: str, headers: Optional[Dict[str, str]] = None):
        self.endpoint = endpoint
        self.headers = headers or {}
        
        # Setup transport
        transport = AIOHTTPTransport(
            url=endpoint,
            headers=self.headers
        )
        
        # Create client with transport
        self.client = Client(transport=transport, fetch_schema_from_transport=True)
    
    async def execute_async(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute GraphQL query asynchronously"""
        parsed_query = gql(query)
        result = await self.client.execute_async(parsed_query, variable_values=variables)
        return result
    
    def execute_sync(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute GraphQL query synchronously"""
        # Use requests transport for sync
        sync_transport = RequestsHTTPTransport(
            url=self.endpoint,
            headers=self.headers
        )
        sync_client = Client(transport=sync_transport)
        
        parsed_query = gql(query)
        result = sync_client.execute(parsed_query, variable_values=variables)
        return result

# --- Type-Safe Client with Dataclasses ---
@dataclass
class Author:
    id: int
    name: str
    birth_year: int
    books: Optional[List['Book']] = None

@dataclass
class Book:
    id: int
    title: str
    genre: str
    published_year: int
    author: Optional[Author] = None

class TypedGraphQLClient:
    def __init__(self, endpoint: str):
        self.client = SimpleGraphQLClient(endpoint)
    
    def get_all_books(self) -> List[Book]:
        """Get all books with type safety"""
        query = """
        query GetAllBooks {
            books {
                id
                title
                genre
                publishedYear
                author {
                    id
                    name
                    birthYear
                }
            }
        }
        """
        
        result = self.client.execute(query)
        books_data = result.get("data", {}).get("books", [])
        
        books = []
        for book_data in books_data:
            author_data = book_data.get("author")
            author = None
            if author_data:
                author = Author(
                    id=author_data["id"],
                    name=author_data["name"],
                    birth_year=author_data["birthYear"]
                )
            
            book = Book(
                id=book_data["id"],
                title=book_data["title"],
                genre=book_data["genre"],
                published_year=book_data["publishedYear"],
                author=author
            )
            books.append(book)
        
        return books
    
    def get_book_by_id(self, book_id: int) -> Optional[Book]:
        """Get specific book by ID"""
        query = """
        query GetBook($bookId: Int!) {
            book(id: $bookId) {
                id
                title
                genre
                publishedYear
                author {
                    id
                    name
                    birthYear
                }
            }
        }
        """
        
        variables = {"bookId": book_id}
        result = self.client.execute(query, variables)
        book_data = result.get("data", {}).get("book")
        
        if not book_data:
            return None
        
        author_data = book_data.get("author")
        author = None
        if author_data:
            author = Author(
                id=author_data["id"],
                name=author_data["name"],
                birth_year=author_data["birthYear"]
            )
        
        return Book(
            id=book_data["id"],
            title=book_data["title"],
            genre=book_data["genre"],
            published_year=book_data["publishedYear"],
            author=author
        )
    
    def create_book(self, title: str, author_id: int, genre: str, published_year: int) -> Optional[Book]:
        """Create a new book"""
        mutation = """
        mutation CreateBook($title: String!, $authorId: Int!, $genre: String!, $publishedYear: Int!) {
            createBook(title: $title, authorId: $authorId, genre: $genre, publishedYear: $publishedYear) {
                book {
                    id
                    title
                    genre
                    publishedYear
                    author {
                        id
                        name
                        birthYear
                    }
                }
            }
        }
        """
        
        variables = {
            "title": title,
            "authorId": author_id,
            "genre": genre,
            "publishedYear": published_year
        }
        
        result = self.client.execute(mutation, variables)
        book_data = result.get("data", {}).get("createBook", {}).get("book")
        
        if not book_data:
            return None
        
        author_data = book_data.get("author")
        author = None
        if author_data:
            author = Author(
                id=author_data["id"],
                name=author_data["name"],
                birth_year=author_data["birthYear"]
            )
        
        return Book(
            id=book_data["id"],
            title=book_data["title"],
            genre=book_data["genre"],
            published_year=book_data["publishedYear"],
            author=author
        )

# --- Subscription Client (WebSocket) ---
import websockets

class GraphQLSubscriptionClient:
    def __init__(self, ws_endpoint: str):
        self.ws_endpoint = ws_endpoint
    
    async def subscribe(self, subscription_query: str, variables: Optional[Dict[str, Any]] = None):
        """Subscribe to GraphQL subscription"""
        async with websockets.connect(self.ws_endpoint, subprotocols=["graphql-ws"]) as websocket:
            # Send connection init
            await websocket.send(json.dumps({
                "type": "connection_init"
            }))
            
            # Wait for connection ack
            response = await websocket.recv()
            
            # Send subscription
            await websocket.send(json.dumps({
                "id": "1",
                "type": "start",
                "payload": {
                    "query": subscription_query,
                    "variables": variables or {}
                }
            }))
            
            # Listen for data
            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "data":
                    yield data.get("payload", {}).get("data", {})

# --- Error Handling ---
class GraphQLError(Exception):
    def __init__(self, errors: List[Dict[str, Any]]):
        self.errors = errors
        super().__init__(f"GraphQL errors: {errors}")

class RobustGraphQLClient:
    def __init__(self, endpoint: str, max_retries: int = 3):
        self.client = SimpleGraphQLClient(endpoint)
        self.max_retries = max_retries
    
    def execute_with_retry(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute query with retry logic and error handling"""
        for attempt in range(self.max_retries):
            try:
                result = self.client.execute(query, variables)
                
                # Check for GraphQL errors
                if "errors" in result:
                    raise GraphQLError(result["errors"])
                
                return result
            
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise e
                print(f"Request failed, retrying... ({attempt + 1}/{self.max_retries})")
                continue
        
        raise Exception("Max retries exceeded")

# --- Caching Client ---
from functools import lru_cache
import hashlib

class CachedGraphQLClient:
    def __init__(self, endpoint: str, cache_size: int = 128):
        self.client = SimpleGraphQLClient(endpoint)
        self.cache_size = cache_size
    
    def _cache_key(self, query: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key from query and variables"""
        content = query + json.dumps(variables or {}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    @lru_cache(maxsize=128)
    def _execute_cached(self, query: str, variables_json: str) -> str:
        """Cached execution (only works with immutable types)"""
        variables = json.loads(variables_json) if variables_json else None
        result = self.client.execute(query, variables)
        return json.dumps(result)
    
    def execute(self, query: str, variables: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> Dict[str, Any]:
        """Execute with optional caching"""
        if not use_cache:
            return self.client.execute(query, variables)
        
        variables_json = json.dumps(variables or {}, sort_keys=True)
        result_json = self._execute_cached(query, variables_json)
        return json.loads(result_json)

# --- Usage Examples ---
async def main():
    # Basic usage
    simple_client = SimpleGraphQLClient("http://localhost:8000/graphql")
    
    # Simple query
    query = """
    query {
        books {
            id
            title
            author {
                name
            }
        }
    }
    """
    
    result = simple_client.execute(query)
    print("Simple query result:", result)
    
    # Query with variables
    query_with_vars = """
    query GetBook($id: Int!) {
        book(id: $id) {
            title
            genre
            author {
                name
            }
        }
    }
    """
    
    result = simple_client.execute(query_with_vars, {"id": 1})
    print("Query with variables:", result)
    
    # Type-safe client
    typed_client = TypedGraphQLClient("http://localhost:8000/graphql")
    books = typed_client.get_all_books()
    print("Typed books:", books)
    
    # Create new book
    new_book = typed_client.create_book(
        title="Fahrenheit 451",
        author_id=1,
        genre="Dystopian",
        published_year=1953
    )
    print("New book:", new_book)
    
    # Advanced async client
    advanced_client = AdvancedGraphQLClient("http://localhost:8000/graphql")
    async_result = await advanced_client.execute_async(query)
    print("Async result:", async_result)
    
    # Subscription example
    subscription_client = GraphQLSubscriptionClient("ws://localhost:8000/graphql")
    subscription_query = """
    subscription {
        bookAdded {
            id
            title
            author {
                name
            }
        }
    }
    """
    
    print("Listening for book additions...")
    async for data in subscription_client.subscribe(subscription_query):
        print("New book added:", data)
        break  # Exit after first event for demo

# --- Batch Query Client ---
class BatchGraphQLClient:
    def __init__(self, endpoint: str):
        self.client = SimpleGraphQLClient(endpoint)
    
    def execute_batch(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple queries in a single request"""
        # Note: This requires server support for query batching
        response = requests.post(
            self.client.endpoint,
            json=queries,
            headers=self.client.headers
        )
        response.raise_for_status()
        return response.json()

# --- Fragment Builder ---
class FragmentBuilder:
    @staticmethod
    def book_fragment() -> str:
        return """
        fragment BookDetails on Book {
            id
            title
            genre
            publishedYear
        }
        """
    
    @staticmethod
    def author_fragment() -> str:
        return """
        fragment AuthorDetails on Author {
            id
            name
            birthYear
        }
        """
    
    def build_query_with_fragments(self) -> str:
        return f"""
        {self.book_fragment()}
        {self.author_fragment()}
        
        query GetBooksWithAuthors {{
            books {{
                ...BookDetails
                author {{
                    ...AuthorDetails
                }}
            }}
        }}
        """

if __name__ == "__main__":
    # Run the async example
    asyncio.run(main())