# server.py - GraphQL Server
# Run with: python server.py

from graphene import ObjectType, String, Int, List as GrapheneList, Field, Mutation, Schema
from fastapi import FastAPI
from starlette_graphene3 import GraphQLApp

import uvicorn

# --- Data Models (In real app, use SQLAlchemy/database) ---
books_data = [
    {"id": 1, "title": "The Great Gatsby", "author_id": 1, "genre": "Fiction", "published_year": 1925},
    {"id": 2, "title": "To Kill a Mockingbird", "author_id": 2, "genre": "Fiction", "published_year": 1960},
    {"id": 3, "title": "1984", "author_id": 3, "genre": "Dystopian", "published_year": 1949},
]

authors_data = [
    {"id": 1, "name": "F. Scott Fitzgerald", "birth_year": 1896},
    {"id": 2, "name": "Harper Lee", "birth_year": 1926},
    {"id": 3, "name": "George Orwell", "birth_year": 1903},
]

# --- GraphQL Types ---
class Author(ObjectType):
    id = Int()
    name = String()
    birth_year = Int()
    books = GrapheneList(lambda: Book)
    
    def resolve_books(self, info):
        return [Book(**book) for book in books_data if book["author_id"] == self.id]

class Book(ObjectType):
    id = Int()
    title = String()
    genre = String()
    published_year = Int()
    author = Field(Author)
    
    def resolve_author(self, info):
        author_id = next((book["author_id"] for book in books_data if book["id"] == self.id), None)
        author_data = next((author for author in authors_data if author["id"] == author_id), None)
        return Author(**author_data) if author_data else None

# --- Queries ---
class Query(ObjectType):
    books = GrapheneList(Book)
    book = Field(Book, id=Int(required=True))
    authors = GrapheneList(Author)
    author = Field(Author, id=Int(required=True))
    books_by_genre = GrapheneList(Book, genre=String(required=True))
    
    def resolve_books(self, info):
        return [Book(**book) for book in books_data]
    
    def resolve_book(self, info, id):
        book_data = next((book for book in books_data if book["id"] == id), None)
        return Book(**book_data) if book_data else None
    
    def resolve_authors(self, info):
        return [Author(**author) for author in authors_data]
    
    def resolve_author(self, info, id):
        author_data = next((author for author in authors_data if author["id"] == id), None)
        return Author(**author_data) if author_data else None
    
    def resolve_books_by_genre(self, info, genre):
        filtered_books = [book for book in books_data if book["genre"].lower() == genre.lower()]
        return [Book(**book) for book in filtered_books]

# --- Mutations ---
class CreateBook(Mutation):
    class Arguments:
        title = String(required=True)
        author_id = Int(required=True)
        genre = String(required=True)
        published_year = Int(required=True)
    
    book = Field(Book)
    
    def mutate(self, info, title, author_id, genre, published_year):
        new_id = max([book["id"] for book in books_data]) + 1 if books_data else 1
        new_book = {
            "id": new_id,
            "title": title,
            "author_id": author_id,
            "genre": genre,
            "published_year": published_year
        }
        books_data.append(new_book)
        return CreateBook(book=Book(**new_book))

class UpdateBook(Mutation):
    class Arguments:
        id = Int(required=True)
        title = String()
        genre = String()
        published_year = Int()
    
    book = Field(Book)
    
    def mutate(self, info, id, title=None, genre=None, published_year=None):
        book_data = next((book for book in books_data if book["id"] == id), None)
        if not book_data:
            return None
        
        if title:
            book_data["title"] = title
        if genre:
            book_data["genre"] = genre
        if published_year:
            book_data["published_year"] = published_year
        
        return UpdateBook(book=Book(**book_data))

class Mutation(ObjectType):
    create_book = CreateBook.Field()
    update_book = UpdateBook.Field()

# --- Schema ---
schema = Schema(query=Query, mutation=Mutation)

# --- FastAPI App ---
app = FastAPI(title="GraphQL Library API")

# Add GraphQL endpoint
app.add_route("/graphql", GraphQLApp(schema=schema))

# GraphQL Playground interface
@app.get("/")
async def graphql_playground():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>GraphQL Playground</title>
        <style>
            body { margin: 0; font-family: Arial, sans-serif; }
            .container { max-width: 800px; margin: 50px auto; padding: 20px; }
            .endpoint { background: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>GraphQL Library API</h1>
            <p>Welcome to the GraphQL Library API!</p>
            
            <div class="endpoint">
                <h3>GraphQL Endpoint</h3>
                <p><strong>POST</strong> <code>http://localhost:8000/graphql</code></p>
            </div>
            
            <h3>Example Queries:</h3>
            <pre><code>
# Get all books with authors
{
  books {
    id
    title
    genre
    author {
      name
      birthYear
    }
  }
}

# Get specific book
{
  book(id: 1) {
    title
    author {
      name
    }
  }
}

# Create new book (mutation)
mutation {
  createBook(
    title: "Brave New World"
    authorId: 3
    genre: "Science Fiction"
    publishedYear: 1932
  ) {
    book {
      id
      title
    }
  }
}
            </code></pre>
            
            <p>Use tools like GraphiQL, Insomnia, or Postman to interact with the API.</p>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    print("Starting GraphQL Server...")
    print("Server will be available at: http://localhost:8001")
    print("GraphQL endpoint: http://localhost:8001/graphql")
    uvicorn.run(app, host="0.0.0.0", port=8001)