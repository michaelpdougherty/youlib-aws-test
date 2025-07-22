from fastapi.responses import JSONResponse

def not_implemented():
  return JSONResponse(
    status_code=500,
    content={"userSafeErrorMessage": "Sorry, this feature is not available yet. Please contact support for more details."}
  )

def client_error(message: str = "client error"):
   return JSONResponse(
      status_code=400,
      content={"userSafeErrorMessage": message}
   )

def to_camel(snake_str: str) -> str:
    parts = snake_str.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])

def dict_keys_to_camel(d):
    if isinstance(d, list):
        return [dict_keys_to_camel(i) if isinstance(i, (dict, list)) else i for i in d]
    if not isinstance(d, dict):
        return d
    new_dict = {}
    for k, v in d.items():
        new_key = to_camel(k)
        new_dict[new_key] = dict_keys_to_camel(v) if isinstance(v, (dict, list)) else v
    return new_dict