from pydantic import BaseModel, Field


class DecomposedQueries(BaseModel):
    queries: list[str] = Field(
        min_length=1, 
        max_length=4,
        description="1 to 4 short, standalone search queries in English"
    )