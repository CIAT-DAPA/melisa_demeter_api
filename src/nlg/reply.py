# Importing Enum class from the enum module
from enum import Enum

# Enumerates different kinds of replies
class ReplyKindEnum(Enum):
    HI = 1
    HELP = 2
    BYE = 3
    THANKS = 4
    NEW_USER = 5
    WAIT = 6

# Enumerates different error types in replies
class ReplyErrorEnum(Enum):
    MISSING_LOCALITIES = 1
    ERROR_ACLIMATE = 2
    LOCALITY_NOT_FOUND = 3
    ERROR_ACLIMATE_CLIMATOLOGY = 4
    ERROR_ACLIMATE_FORECAST_CLIMATE = 5
    ERROR_ACLIMATE_FORECAST_YIELD = 6
    QUESTION_NOT_FORMAT = 7

# Enumerates different geographic reply types
class ReplyGeographicEnum(Enum):
    STATE = 1
    MUNICIPALITIES_STATE = 2
    WS_MUNICIPALITY = 3
    WEATHER_STATION = 4

# Enumerates different cultivar-related reply types
class ReplyCultivarsEnum(Enum):
    CROP_MULTIPLE = 1
    CROP_CULTIVAR = 2
    CULTIVARS_MULTIPLE = 3

# Enumerates different historical reply types
class ReplyHistoricalEnum(Enum):
    CLIMATOLOGY = 1

# Enumerates different forecast reply types
class ReplyForecastEnum(Enum):
    CLIMATE = 1
    YIELD_PERFORMANCE = 2
    YIELD_DATE = 3

# Enumerates different reply form types
class ReplyFormEnum(Enum):
    QUESTION = 1
    RECEIVED_OK = 2
    RECEIVED_ERROR = 3
    RECEIVED_DATA_SHEET = 4
    
class ReplyFormCroppieEnum(Enum):
    FAILED_ESTIMATION = 1
    FINISHED_ESTIMATION = 2


# Class representing a generic reply
class Reply():

    # Constructor for the Reply class
    def __init__(self, type=None, values=None, tag=None):
        """
        Initializes a new instance of the Reply class.

        Parameters:
        - type: Type of the reply (uses enums defined above).
        - values: Additional values or data associated with the reply.
        - tag: Optional text
        """
        self.type = type
        self.values = values
        self.tag = tag