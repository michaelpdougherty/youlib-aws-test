# api/routes/books.py
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from utils.jwt_utils import verify_jwt
from utils.http_utils import upgrade_to_https
from utils.isbn_utils import is_valid_isbn_check
from utils.response_utils import client_error
from db.session import get_session
from collections import defaultdict
from schemas import ISBN

# This is the problem.
#from services.edition_service import fetch_book_data

router = APIRouter()

@router.get("/books/")
async def get_books(user_id: int = Depends(verify_jwt), session: AsyncSession = Depends(get_session)):
    statement = text(" " \
    "SELECT " \
      "user_editions.id, " \
      "title, " \
      "authors.name author, " \
      "thumbnail " \
    "FROM " \
      "user_editions " \
    "INNER JOIN " \
      "editions " \
    "ON " \
      "user_editions.edition_id = editions.id " \
    "INNER JOIN " \
      "works " \
    "ON " \
      "editions.work_id = works.id " \
    "INNER JOIN " \
      "work_authors " \
    "ON " \
      "work_authors.work_id = works.id " \
    "INNER JOIN " \
      "authors " \
    "ON " \
      "authors.id = work_authors.author_id " \
    "WHERE " \
      "user_id = :user_id ")
    result = await session.execute(statement, { "user_id": user_id })

    rows = result.fetchall()

    # Group by work
    works_map = defaultdict(lambda: {
      "id": None,
      "title": "",
      "authors": [],
      "thumbnail": "",
    })

    for id, title, author, thumbnail in rows:
        works_map[id]["id"] = id
        works_map[id]["title"] = title
        works_map[id]["authors"].append(author)
        works_map[id]["thumbnail"] = upgrade_to_https(thumbnail)
    works_list = list(works_map.values())
    return works_list 

# We have a bad pattern throughout the functions here
# If the response of any function is a JSONResponse,
# that means it's an error.
@router.post("/books/")
async def add_book(isbn: ISBN, user_id: int = Depends(verify_jwt), session: AsyncSession = Depends(get_session)):
    # time.sleep(1)
    is_valid_isbn = is_valid_isbn_check(isbn=isbn)
    if not is_valid_isbn:
      return JSONResponse(
        status_code=400,
        content={"userSafeErrorMessage": "Invalid ISBN"}
      )

    # TODO - We should really make sure the user hasn't added the edition already HERE
    # before we pull everything from the DB if we're just going to return an error. 

    return {"message": "Fix this shit"}
    # edition = await fetch_book_data(isbn=isbn, session=session)
    if isinstance(edition, JSONResponse):
      # Assumed error body
      return edition

    # Unpack variables
    edition_id = edition.id
    title = edition.title
    authors = edition.authors
    thumbnail = edition.thumbnail

    # Ensure the user has not already added the edition
    # See above comment for where to move this eventually
    statement = text("SELECT COUNT(*) FROM user_editions WHERE user_id = :user_id AND edition_id = :edition_id")
    result = await session.execute(statement, {
        "user_id": user_id,
        "edition_id": edition_id
    })
    user_already_added_edition = result.scalar_one() > 0
    if user_already_added_edition:
        return client_error("Edition already added")

    # MOST IMPORTANT STEP
    # create `user_editions` row for the added book
    statement = text("INSERT INTO user_editions (edition_id, user_id) VALUES (:edition_id, :user_id) RETURNING id")
    result = await session.execute(statement, {
      "edition_id": edition_id,
      "user_id": user_id,
    })
    user_edition_id = result.scalar_one()
    await session.commit()

    # TODO make a JSON-encodable model (UserEdition)
    return {
      "id": user_edition_id,
      "title": title,
      "authors": authors,
      "thumbnail": upgrade_to_https(thumbnail),
    }

# Delete library 
@router.delete("/books/")
async def register(user_id: int = Depends(verify_jwt), session: AsyncSession = Depends(get_session)):
  statement = text("DELETE FROM user_editions WHERE user_id = :user_id")
  await session.execute(statement, { "user_id": user_id })
  await session.commit()
  return JSONResponse(
     status_code=200,
     content={
        "message": "Successfully deleted library"
     }
  )

# Hit our APIs and see what we would have gotten (for testing / eventually refreshing)
@router.get("/books/fetch")
async def fetch_book(isbn: str, user_id: int = Depends(verify_jwt), session: AsyncSession = Depends(get_session)):
  data = await get_best_possible_edition_data(ISBN(isbn=isbn))
  return data
