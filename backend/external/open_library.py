from fastapi.responses import JSONResponse
import httpx
from schemas import ISBN, EditionData

async def get_edition_data_from_open_library(isbn: ISBN) -> EditionData | JSONResponse:
    url = f"https://openlibrary.org/isbn/{isbn.isbn}.json"
    print(f"Making request to URL: {url}")
    response = httpx.get(url, follow_redirects=True)
    if response.status_code >= 400:
        message = f"Request to Open Library API failed with status code {response.status_code} for ISBN {isbn.isbn}."
        print(message)
        return JSONResponse(
          status_code=500,
          content={"userSafeErrorMessage": message}
        )
    data = response.json()
    error = data.get("error")
    if error == "notfound":
       message = f"Request to Open Library API returned no results for ISBN {isbn.isbn}."
       print(message)
       return JSONResponse(
          status_code=500,
          content={"userSafeErrorMessage": message}
       )
    
    title = data["title"]

    # Could be authors or contributors 
    authors = [c["name"] for c in data.get("contributors", []) if c.get("role") == "Author"]
    if len(authors) == 0:
       author_keys = [a["key"] for a in data.get("authors", []) if a.get("key") != None]
       assumed_author_key = author_keys[0] if len(author_keys) > 0 else None
       if assumed_author_key != None:
          # Make another query
          author_url = f"https://openlibrary.org{assumed_author_key}.json"
          author_response = httpx.get(author_url, follow_redirects=True)
          if author_response.status_code < 400:
            author_data = author_response.json()
            author_name = author_data.get("name")
            if author_name != None:
               authors = [author_name]

    # Make sure we always have data at least
    if len(authors) == 0:
       authors = ["Unknown Author"]

    publisher = data["publishers"][0]
    published_date = data["publish_date"]

    covers = data.get("covers")
    cover = covers[0] if covers else None
    thumbnail = f"https://covers.openlibrary.org/b/id/{cover}.jpg" if cover else ""

    # Get the description from the work page
    # TODO get cover from work page if it's there
    description = ""
    works = data.get("works")
    work = works[0] if works else None
    work_key = work.get("key", "")
    work_url = f"https://openlibrary.org{work_key}.json" if work else None
    if work_url != None:
      print(f"Making request to {work_url}")
      work_response = httpx.get(work_url, follow_redirects=True)
      if work_response.status_code < 400:
        work_data = work_response.json()
        test_description = work_data.get("description", "")
        if isinstance(test_description, dict):
          description = test_description.get("value", "")
        else:
           description = test_description
      
      if thumbnail == "":
        covers = work_data.get("covers")
        cover = covers[0] if covers and isinstance(covers, list) and len(covers) > 0 else None
        thumbnail = f"https://covers.openlibrary.org/b/id/{cover}.jpg" if cover else ""

    return EditionData(
      title=title,
      authors=authors,
      publisher=publisher,
      published_date=published_date,
      description=description,
      thumbnail=thumbnail
    )