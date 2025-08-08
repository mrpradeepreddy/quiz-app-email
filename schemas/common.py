from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')

class PaginationParams(BaseModel):
    page: int = 1
    size: int = 10

class PaginatedResponse(BaseModel,Generic[T]):
    items:List[T]
    total:int
    page:int
    size:int
    pages:int

#"message": "User deleted successfully"
class MessageResponse(BaseModel):
    message:str

#"detail": "Item with that ID not found"
class ErrorResponse(BaseModel):
    detail:str



# Pagination parameters, in the context of APIs and web development, 
# refer to the specific parameters included in a request that control
# how a large dataset is divided and returned in smaller, manageable "pages."


# Not quite. It's better to think of it this way:
# Imagine you have a single large assessment with 50 questions.
# size is the number of questions you want to show at a time.
# size = 10 means "Show me 10 questions per screen."
# page is which group of those questions you want to see.
# page = 1 would show questions 1-10.
# page = 2 would show questions 11-20.
# page = 3 would show questions 21-30.