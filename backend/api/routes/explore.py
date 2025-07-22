# api/routes/explore.py
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from db.session import get_session
from sqlalchemy import text, bindparam
from sqlalchemy.ext.asyncio import AsyncSession
from utils.jwt_utils import verify_jwt
from typing import Optional, List, Tuple
from utils.response_utils import not_implemented, dict_keys_to_camel
from utils.http_utils import upgrade_to_https
from pydantic import BaseModel
from collections import defaultdict


class LibraryMinified(BaseModel):
    id: int
    name: str
    zip_code: str
    distance: float
class Book(BaseModel):
    id: int
    title: str
    authors: List[str]
    thumbnail: str
    description: str
    library: LibraryMinified
class Library(BaseModel):
    id: int
    name: str
    zip_code: str
    owner_first_name: str
    num_books: int
    distance: float

router = APIRouter()

async def get_user_zip(
    user_id: int = Depends(verify_jwt),
    session: AsyncSession = Depends(get_session),
):
  statement = text("SELECT zip_code FROM users WHERE id = :user_id")
  bindings = { "user_id": user_id }
  result = await session.execute(statement, bindings)
  zip_code = result.scalar_one()
  return zip_code

async def get_zip_codes_within_radius(zip_code: str, radius: int, session: AsyncSession = Depends(get_session)):
    statement = text(
      "SELECT zl2.zip zip_code, "
      "haversine(zl1.lat, zl1.lng, zl2.lat, zl2.lng) AS distance "
      "FROM zip_locations zl1 "
      "JOIN zip_locations zl2 ON zl1.zip = :zip_code "
      "WHERE zl1.zip <> zl2.zip "
      "AND haversine(zl1.lat, zl1.lng, zl2.lat, zl2.lng) <= :radius"
    )
    result = await session.execute(statement, { "zip_code": zip_code, "radius": radius })
    return result.mappings().all() + [{ "zip_code": zip_code, "distance": 0.0 }]

async def get_nearby_libraries_and_books(nearby_user_ids: List[str], user_id: int, zip_mapping: dict, session: AsyncSession = Depends(get_session)) -> Tuple[List[Library], List[Book]]:
  # Get library information
  statement = text(
    "SELECT "
    "users.id, first_name, zip_code, library_name, COUNT(user_editions.id) num_books "
    "FROM "
    "users "
    "INNER JOIN "
    "user_editions "
    "ON "
    "users.id = user_editions.user_id "
    "WHERE "
    "users.id IN :user_ids "
    "AND "
    "users.id != :user_id "
    "GROUP BY users.id"
  ).bindparams(
    bindparam("user_ids", expanding=True)
  )
  result = await session.execute(statement, { "user_ids": nearby_user_ids, "user_id": user_id })
  library_rows = result.mappings().all()
  libraries = {}
  for row in library_rows:
    id = row["id"]
    libraries[id] = Library(
      id=id,
      name=row["library_name"],
      zip_code=row["zip_code"],
      owner_first_name=row["first_name"],
      num_books=row["num_books"],
      distance = zip_mapping[row["zip_code"]]
    )
  # Get user editions
  statement = text(
    "SELECT "
    "user_editions.user_id, user_editions.id, title, array_agg(authors.name) authors, thumbnail, description "
    "FROM "
    "user_editions "
    "INNER JOIN "
    "editions "
    "ON "
    "user_editions.edition_id = editions.id "
    "INNER JOIN "
    "works "
    "ON "
    "editions.work_id = works.id "
    "INNER JOIN "
    "work_authors "
    "ON "
    "works.id = work_authors.work_id "
    "INNER JOIN "
    "authors "
    "ON "
    "work_authors.author_id = authors.id "
    "WHERE "
    "user_editions.user_id IN :user_ids "
    "AND "
    "user_editions.user_id != :user_id "
    "GROUP BY "
    "user_id, user_editions.id, title, thumbnail, description"
  ).bindparams(
    bindparam("user_ids", expanding=True)
  )
  result = await session.execute(statement, { "user_ids": nearby_user_ids, "user_id": user_id })
  book_rows = result.mappings().all()
  books = []
  for row in book_rows:
    library = libraries[row["user_id"]]
    books.append(
      Book(
        id=row["id"],
        title=row["title"],
        authors=row["authors"],
        thumbnail=row["thumbnail"],
        description=row["description"],
        library=LibraryMinified(
          id=library.id,
          name=library.name,
          zip_code=library.zip_code,
          distance=library.distance
        )
      )
    )
  return (list(libraries.values()), books)

@router.get("/explore")
async def explore(
    user_id: int = Depends(verify_jwt),
    zip_code: str = Depends(get_user_zip),
    search: Optional[str] = None,
    radius: int = 10,
    session: AsyncSession = Depends(get_session),
):
    nearby_zip_data = await get_zip_codes_within_radius(zip_code, radius, session)
    zip_mapping = {}
    for zip in nearby_zip_data:
       zip_mapping[zip["zip_code"]] = zip["distance"]
    nearby_zips = [z['zip_code'] for z in nearby_zip_data]

    if search:
        return not_implemented()
        # Libraries matching search
        library_matches = db.query(Library).filter(
            Library.zip_code.in_(nearby_zips),
            Library.name.ilike(f"%{search}%")
        ).all()

        # Books matching search
        book_matches = db.query(Book).join(Library).filter(
            Library.zip_code.in_(nearby_zips),
            or_(
                Book.title.ilike(f"%{search}%"),
                Book.author.ilike(f"%{search}%")
            )
        ).all()

        return {
            "libraries": [lib.to_dict() for lib in library_matches],
            "books": [book.to_dict(include_library=True) for book in book_matches]
        }

    # Not all users will have books
    statement = text("SELECT id FROM users WHERE zip_code IN :zip_codes").bindparams(
      bindparam("zip_codes", expanding=True)
    )
    result = await session.execute(statement, { "zip_codes": nearby_zips })
    nearby_user_ids = result.scalars().all()

    (libraries, books) = await get_nearby_libraries_and_books(nearby_user_ids, user_id, zip_mapping, session)

    return JSONResponse({
      "zipCode": zip_code,
      "radius": radius,
      "results": {
          "libraries": [dict_keys_to_camel(lib.model_dump()) for lib in libraries],
          "books": [dict_keys_to_camel(book.model_dump()) for book in books],
      }
    })

@router.get("/libraries/{library_id}")
async def get_library(
  library_id: int,
  user_id: int = Depends(verify_jwt),
  session: AsyncSession = Depends(get_session)
):
  statement = text(
    "SELECT "
      "user_editions.id, "
      "title, "
      "authors.name author, "
      "thumbnail, "
      "description "
    "FROM "
      "user_editions "
    "INNER JOIN "
      "editions "
    "ON "
      "user_editions.edition_id = editions.id "
    "INNER JOIN "
      "works "
    "ON "
      "editions.work_id = works.id "
    "INNER JOIN "
      "work_authors "
    "ON "
      "work_authors.work_id = works.id "
    "INNER JOIN "
      "authors "
    "ON "
      "authors.id = work_authors.author_id "
    "WHERE "
      "user_id = :library_id"
  )
  result = await session.execute(statement, { "library_id": library_id })

  rows = result.fetchall()

  # Group by work
  works_map = defaultdict(lambda: {
    "id": None,
    "title": "",
    "authors": [],
    "thumbnail": "",
    "description": "",
  })

  for id, title, author, thumbnail, description in rows:
      works_map[id]["id"] = id
      works_map[id]["title"] = title
      works_map[id]["authors"].append(author)
      works_map[id]["thumbnail"] = upgrade_to_https(thumbnail)
      works_map[id]["description"] = description
  works_list = list(works_map.values())
  return works_list 
