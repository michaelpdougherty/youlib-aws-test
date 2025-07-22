from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import Edition, EditionData, ISBN
from external.google_books import get_edition_data_from_google_books
from external.open_library import get_edition_data_from_open_library
from utils.response_utils import not_implemented

async def get_edition_by_id(edition_id: int, session: AsyncSession) -> Edition:
    statement = text("SELECT works.id work_id, title, publisher, published_date, description, thumbnail FROM works INNER JOIN editions ON editions.work_id = works.id WHERE editions.id = :edition_id")
    result = await session.execute(statement, {
      "edition_id": edition_id,
    })
    row = result.mappings().fetchone()
    work_id = row["work_id"]
    title = row["title"]
    publisher = row["publisher"]
    published_date = row["published_date"]
    description = row["description"]
    thumbnail = row["thumbnail"]

    statement = text("SELECT name FROM authors INNER JOIN work_authors ON authors.id = work_authors.author_id WHERE work_id = :work_id")
    result = await session.execute(statement, {
        "work_id": work_id,
    })
    authors = result.scalars().all()

    return Edition(
      id=edition_id,
      work_id=work_id,
      title=title,
      publisher=publisher,
      published_date=published_date,
      description=description,
      thumbnail=thumbnail,
      authors=authors
    )

# For now just pick one or the other, not merging them.
async def get_best_possible_edition_data(isbn: ISBN) -> EditionData | JSONResponse:
  open_library_data = await get_edition_data_from_open_library(isbn=isbn)
  print("open library data:")
  print(open_library_data)
  google_books_data = await get_edition_data_from_google_books(isbn=isbn)
  print("google books data:")
  print(google_books_data)
  if isinstance(google_books_data, JSONResponse) and isinstance(open_library_data, JSONResponse):
     # complete failure, return "error"
     print("Both returned errors, skipping")
     return google_books_data
  elif isinstance(open_library_data, JSONResponse):
    print("Open Library returned an error, have to use Google Books")
    return google_books_data
  elif isinstance(google_books_data, JSONResponse):
    print("Google Books returned an error, have to use Open Library")
    return open_library_data

  # Here, we can actually attempt to merge them
  final_data = open_library_data
  if google_books_data.description != "" and final_data.description == "":
    final_data.description = google_books_data.description
  if google_books_data.thumbnail != "" and final_data.thumbnail == "":
    final_data.thumbnail = google_books_data.thumbnail
  if final_data.authors[0] == "Unknown Author":
    final_data.authors = google_books_data.authors

  return final_data

"""
TODO - Differentiate "work authors" and "editions authors" 
TODO - Handle cases where two different works have the same title
Currently we assume if two ISBNs bring up the same title, then it's
two editions of the same work. 

TODO - Throw proper errors rather than return a JSONResponse.
For now, the return value being a JSONResponse means it's an error,
and we should return it from the API as-is.

TODO - Separate network, data transformation, and caching. This function does all of it. 

TODO - Ensure we're returning an object that can be accessed with dot notation (BaseModel)
and has the keys we expect.
"""
async def get_edition_from_third_party_api(isbn: ISBN, session: AsyncSession) -> Edition | JSONResponse:
    book_data = await get_best_possible_edition_data(isbn)
    if isinstance(book_data, JSONResponse):
       # error
       return book_data

    # unpack variables
    title=book_data.title
    publisher=book_data.publisher
    published_date=book_data.published_date
    description=book_data.description
    thumbnail=book_data.thumbnail
    authors=book_data.authors

    # Ensure we have an author ID for all authors
    author_ids = []
    for author in authors:
      statement = text("INSERT INTO authors (name) VALUES (:author_name) ON CONFLICT (name) DO NOTHING")
      await session.execute(statement, { "author_name": author })
      await session.commit()

      # Fetch the author ID either way
      statement = text("SELECT id FROM authors WHERE name = :author_name")
      result = await session.execute(statement, {"author_name": author})
      author_id = result.scalar_one()
      author_ids.append(author_id)

    # Check if we already have a work with a matching title
    statement = text("SELECT COUNT(*) FROM works WHERE title = :title")
    result = await session.execute(statement, {"title": title})
    matching_title = result.scalar_one() > 0
    if not matching_title:
      # Add the work and tie the authors to it in work_authors
      statement = text("INSERT INTO works (title, description) VALUES (:title, :description) RETURNING id")
      result = await session.execute(statement, { "title": title, "description": description })
      work_id = result.scalar_one()
      await session.commit()

      for author_id in author_ids:
        statement = text("INSERT INTO work_authors (work_id, author_id) VALUES (:work_id, :author_id)")
        await session.execute(statement, {
            "work_id": work_id,
            "author_id": author_id,
        })
        await session.commit()
    else:
      # System-wide scanning two editions (ISBNs) of the same work is not supported
      # See function header for explanation
      # This is a huge TODO
      return not_implemented()

    # Insert the new edition
    statement = text("INSERT INTO editions (work_id, isbn, publisher, published_date, thumbnail) VALUES (:work_id, :isbn, :publisher, :published_date, :thumbnail) RETURNING id")
    result = await session.execute(statement, {
      "work_id": work_id,
      "isbn": isbn.isbn,
      "publisher": publisher,
      "published_date": published_date,
      "thumbnail": thumbnail,
    })
    edition_id = result.scalar_one()
    await session.commit()

    return Edition(
      id=edition_id,
      work_id=work_id,
      title=title,
      publisher=publisher,
      published_date=published_date,
      description=description,
      thumbnail=thumbnail,
      authors=authors
    )

async def fetch_book_data(isbn: ISBN, session: AsyncSession) -> Edition | JSONResponse:
    edition_id = await get_edition_id_by_isbn(isbn=isbn, session=session)
    print("Returning", edition_id, type(edition_id), "for ISBN", isbn.isbn)
    if edition_id != False:
      return await get_edition_by_id(edition_id=edition_id, session=session)
    else:
      return await get_edition_from_third_party_api(isbn=isbn, session=session)

# Returns ID if found, else false
# Used to check if an edition exists in the DB
async def get_edition_id_by_isbn(isbn: ISBN, session: AsyncSession) -> int | bool:
    # TODO - first check the `editions` table for a matching ISBN
    statement = text("SELECT id FROM editions WHERE isbn = :isbn")
    bindings = { "isbn": isbn.isbn }
    result = await session.execute(statement, bindings)
    edition_id = result.scalar_one_or_none()
    if edition_id == None:
       return False
    print("Returned edition_id: ", edition_id, type(edition_id))
    return edition_id