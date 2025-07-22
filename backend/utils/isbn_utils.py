from schemas import ISBN

def is_valid_isbn_check(isbn: ISBN) -> bool:
  # Just a simple Y/N for now
  # TODO support 10-digit ISBN
  # TODO validate isbn to be digits only
  return len(isbn.isbn) == 13
