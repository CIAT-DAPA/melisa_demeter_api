from enum import Enum

class ReplyKindEnum(Enum):
    HI = 1
    HELP = 2
    BYE = 3
    THANKS = 4
    NEW_USER = 5
    WAIT = 6

class ReplyErrorEnum(Enum):
    MISSING_LOCALITIES = 1
    ERROR_ACLIMATE = 2
    LOCALITY_NOT_FOUND = 3
    ERROR_ACLIMATE_CLIMATOLOGY = 4
    ERROR_ACLIMATE_FORECAST_CLIMATE = 5
    ERROR_ACLIMATE_FORECAST_YIELD = 6
    QUESTION_NOT_FORMAT = 7

class ReplyGeographicEnum(Enum):
    STATE = 1
    MUNICIPALITIES_STATE = 2
    WS_MUNICIPALITY = 3
    WEATHER_STATION = 4

class ReplyCultivarsEnum(Enum):
    CROP_MULTIPLE = 1
    CROP_CULTIVAR = 2
    CULTIVARS_MULTIPLE = 3

class ReplyHistoricalEnum(Enum):
    CLIMATOLOGY = 1

class ReplyForecastEnum(Enum):
    CLIMATE = 1
    YIELD_PERFORMANCE = 2
    YIELD_DATE = 3

class ReplyFormEnum(Enum):
    QUESTION = 1
    RECEIVED_OK = 2
    RECEIVED_ERROR = 3

class Reply():

    def __init__(self, type = None, values = None, tag = None):
        self.type = type
        self.values = values
        self.tag = tag