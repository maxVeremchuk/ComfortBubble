from pydantic import BaseModel, ConfigDict, Field, model_validator


class Point(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class ImageDimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class Wall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    start: Point
    end: Point
    thickness: float = Field(gt=0, le=0.1)
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def has_length(self):
        if self.start == self.end:
            raise ValueError("wall start and end must differ")
        return self


class Window(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    start: Point
    end: Point
    wallId: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class FloorPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    image: ImageDimensions
    walls: list[Wall]
    windows: list[Window]

    @model_validator(mode="after")
    def references_known_walls(self):
        ids = {wall.id for wall in self.walls}
        invalid = [window.wallId for window in self.windows if window.wallId not in ids]
        if invalid:
            raise ValueError("windows must reference a detected wall")
        return self
