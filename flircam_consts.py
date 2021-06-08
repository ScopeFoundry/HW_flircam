from collections import OrderedDict
from enum import Enum

FlirCamErrors = OrderedDict([
    ('SPINNAKER_ERR_SUCCESS', 0),
    ('SPINNAKER_ERR_ERROR', -1001),
    ('SPINNAKER_ERR_NOT_INITIALIZED', -1002),
    ('SPINNAKER_ERR_NOT_IMPLEMENTED', -1003),
    ('SPINNAKER_ERR_RESOURCE_IN_USE', -1004),
    ('SPINNAKER_ERR_ACCESS_DENIED', -1005),
    ('SPINNAKER_ERR_INVALID_HANDLE', -1006),
    ('SPINNAKER_ERR_INVALID_ID', -1007),
    ('SPINNAKER_ERR_NO_DATA', -1008),
    ('SPINNAKER_ERR_INVALID_PARAMETER', -1009),
    ('SPINNAKER_ERR_IO', -1010),
    ('SPINNAKER_ERR_TIMEOUT', -1011),
    ('SPINNAKER_ERR_ABORT', -1012),
    ('SPINNAKER_ERR_INVALID_BUFFER', -1013),
    ('SPINNAKER_ERR_NOT_AVAILABLE', -1014),
    ('SPINNAKER_ERR_INVALID_ADDRESS', -1015),
    ('SPINNAKER_ERR_BUFFER_TOO_SMALL', -1016),
    ('SPINNAKER_ERR_INVALID_INDEX', -1017),
    ('SPINNAKER_ERR_PARSING_CHUNK_DATA', -1018),
    ('SPINNAKER_ERR_INVALID_VALUE', -1019),
    ('SPINNAKER_ERR_RESOURCE_EXHAUSTED', -1020),
    ('SPINNAKER_ERR_OUT_OF_MEMORY', -1021),
    ('SPINNAKER_ERR_BUSY', -1022),
    ('GENICAM_ERR_INVALID_ARGUMENT', -2001),
    ('GENICAM_ERR_OUT_OF_RANGE', -2002),
    ('GENICAM_ERR_PROPERTY', -2003),
    ('GENICAM_ERR_RUN_TIME', -2004),
    ('GENICAM_ERR_LOGICAL', -2005),
    ('GENICAM_ERR_ACCESS', -2006),
    ('GENICAM_ERR_TIMEOUT', -2007),
    ('GENICAM_ERR_DYNAMIC_CAST', -2008),
    ('GENICAM_ERR_GENERIC', -2009),
    ('GENICAM_ERR_BAD_ALLOCATION', -2010),
    ('SPINNAKER_ERR_IM_CONVERT', -3001),
    ('SPINNAKER_ERR_IM_COPY', -3002),
    ('SPINNAKER_ERR_IM_MALLOC', -3003),
    ('SPINNAKER_ERR_IM_NOT_SUPPORTED', -3004),
    ('SPINNAKER_ERR_IM_HISTOGRAM_RANGE', -3005),
    ('SPINNAKER_ERR_IM_HISTOGRAM_MEAN', -3006),
    ('SPINNAKER_ERR_IM_MIN_MAX', -3007),
    ('SPINNAKER_ERR_IM_COLOR_CONVERSION', -3008),
    ])

FlirCamImageStatus = ( 'IMAGE_NO_ERROR',           # /**< Image is returned from GetNextImage() call without any errors. */
                'IMAGE_CRC_CHECK_FAILED',   # /**< Image failed CRC check. */
                'IMAGE_INSUFFICIENT_SIZE',  # /**< Image size is smaller than expected. */
                'IMAGE_MISSING_PACKETS',    # /**< Image has missing packets */
                'IMAGE_LEADER_BUFFER_SIZE_INCONSISTENT',   # /**< Image leader is incomplete. */
                'IMAGE_TRAILER_BUFFER_SIZE_INCONSISTENT',  # /**< Image trailer is incomplete. */
                'IMAGE_PACKETID_INCONSISTENT',             # /**< Image has an inconsistent packet id. */
                'IMAGE_DATA_INCOMPLETE',    # /**< Image data is incomplete. */
                'IMAGE_UNKNOWN_ERROR'       # /**< Image has an unknown error. */
                )

class SpinNodeTypeEnum(Enum):
    ValueNode = 0
    BaseNode = 1
    IntegerNode = 2
    BooleanNode = 3
    FloatNode = 4
    CommandNode = 5
    StringNode = 6
    RegisterNode = 7
    EnumerationNode = 8
    EnumEntryNode = 9
    CategoryNode = 10
    PortNode = 11
    UnknownNode = -1


class AccessModeEnum(Enum):
    """
    access mode of a node
    """
    NI              = 0     #: Not implemented
    NA              = 1     #: Not available
    WO              = 2     #: Write Only
    RO              = 3     #: Read Only
    RW                    = 4       #: Read and Write
    _UndefinedAccesMode   = 5 #: Object is not yet initialized
    _CycleDetectAccesMode = 6   #: used internally for AccessMode cycle detection

