from fastapi.responses import JSONResponse
import httpx
from schemas import ISBN, EditionData

async def get_edition_data_from_google_books(isbn: ISBN):
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn.isbn}"
    print(f"Making request to URL: {url}")
    response = httpx.get(url)
    if response.status_code >= 400:
        message = f"Request to Google Books API failed with status code {response.status_code}."
        print(message)
        return JSONResponse(
          status_code=500,
          content={"userSafeErrorMessage": message}
        )
    data = response.json()
    if data["totalItems"] == 0:
      message = "Edition not found for ISBN {isbn.isbn}."
      print(message)
      return JSONResponse(
        status_code=404,
        content={"userSafeErrorMessage": message }
      ) 

    title = ""
    authors = []
    publisher = ""
    published_date = ""
    description = ""
    thumbnail = ""

    # Get first instance of data from all items 
    for item in data["items"]:
      book_data = item["volumeInfo"]
      if title == "":
        title = book_data.get("title", "")
      if authors == []:
        authors = book_data.get("authors", [])
      if publisher == "":
        publisher = book_data.get("publisher", "")
      if published_date == "":
        published_date = book_data.get("publishedDate", "")
      if description == "":
        description = book_data.get("description", "")
      if thumbnail == "":
        thumbnail = book_data.get("imageLinks", {}).get("thumbnail", "")

    return EditionData(
      title=title,
      publisher=publisher,
      published_date=published_date,
      description=description,
      thumbnail=thumbnail,
      authors=authors
    )