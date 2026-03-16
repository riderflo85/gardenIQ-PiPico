from src.core.enum import PseudoEnum


class FrameParsingError(Exception):
    """Raised when frame parsing fails."""

    pass


class FrameProcessingError(Exception):
    """Raised when frame processing fails."""

    pass


class CommandError(PseudoEnum):
    """
    Enumeration of possible command execution errors.

    This enum defines the various error states that can occur during command
    processing and communication with back service.

    Attributes:
        UNKNOW_CMD: Command identifier is not recognized or does not exist
        UNKNOW_ERR: An unknown error occurred during command execution
        INVALID_PARAM: Command parameters are malformed or invalid
        CHECKSUM_ERR: Data integrity check failed, indicating potential data corruption
    """

    UNKNOW_CMD = "UNKNOW_CMD"
    UNKNOW_ERR = "UNKNOW_ERR"
    INVALID_PARAM = "INVALID_PARAM"
    CHECKSUM_ERR = "CHECKSUM_ERR"
