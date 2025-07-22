from fastapi import FastAPI
from api.routes import books, users, explore, borrow_requests

app = FastAPI()
app.include_router(books.router)
app.include_router(users.router)
app.include_router(explore.router)
app.include_router(borrow_requests.router)

@app.get("/")
def read_root():
    return {"message": "Hello, world"}
