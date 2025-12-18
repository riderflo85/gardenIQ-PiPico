from src.core.enum import PseudoEnum
from src.protocols.errors import CommandError
from src.protocols.settings import pattern_strict_version


class FrameType(PseudoEnum):
    """Enumeration of frame types used by the communication protocol.

    Frame types:
    - CMD: Command frame — carries instructions or actions to be executed
    - PING: Keep-alive / heartbeat frame used to verify connectivity
    - ACK: Acknowledgement frame indicating successful receipt or processing
    """

    CMD = "CMD"
    PING = "PING"
    ACK = "ACK"


class CommandState(PseudoEnum):
    OK = "OK"
    ERROR = "ERR"


class Frame:

    # __slots__ is used to declare data members (like properties) and prevent the creation of
    #   __dict__ for each instance.
    # This can save memory and potentially improve performance when creating many instances of the class.
    __slots__ = (
        "frame_type",
        "device_uid",
        "command_id",
        "command_slug",
        "args_values",
        "from_master",
        "command_state",
        "ok_data",
        "err_msg",
        "gd_fw_version",
        "mp_fw_version",
        "checksum",
        "source_frame_from_master"
    )

    def __init__(
        self,
        frame_type: FrameType | str,
        device_uid: str,
        command_id: int,
        from_master: bool = False,  # master is the backend service
        command_slug: str | None = None,
        command_state: CommandState | str | None = None,  # State of the command on this device
        args_values: list[str] | None = None,  # Arguments values for the command when from master
        ok_data: str | None = None,  # Data send to master service when command sended is OK state
        err_msg: CommandError | str | None = None,  # Error message if cmd_state is ERROR
        gd_fw_version: str | None = None,  # GardenIQ Firmware Version
        mp_fw_version: str | None = None,  # MicroPython Firmware Version
        checksum: str | None = None,  # Checksum from master frame
        source_frame_from_master: str | None = None,  # Original frame string from master without \n
    ) -> None:
        # ...assignations...
        self.frame_type = frame_type
        self.device_uid = device_uid
        self.command_id = command_id
        self.command_slug = command_slug
        self.args_values = args_values
        self.from_master = from_master
        self.command_state = command_state
        self.ok_data = ok_data
        self.err_msg = err_msg
        self.gd_fw_version = gd_fw_version
        self.mp_fw_version = mp_fw_version
        self.checksum = checksum
        self.source_frame_from_master = source_frame_from_master
        # ......................

        self._validate()

    def _validate(self):
        """
        Validate the frame data after initialization.

        This method is automatically called in the class __init__ method.
        It ensures that if the frame is from a master, both the checksum and
        source_frame_from_master attributes are provided.

        Raises:
            ValueError: If from_master is True and checksum is None.
            ValueError: If from_master is True and source_frame_from_master is None.
            ValueError: If command_id is 0 and not from_master and firmware versions are missing or invalid.
        """
        if self.from_master:
            if self.checksum is None:
                raise ValueError("checksum required")
            if self.source_frame_from_master is None:
                raise ValueError("source_frame required")

        if self.command_id == 0 and not self.from_master:
            if self.gd_fw_version is None or self.mp_fw_version is None:
                raise ValueError("Firmware versions required for ping command")
            if not pattern_strict_version.match(self.gd_fw_version):
                raise ValueError("Invalid GardenIQ firmware version format")
            if not pattern_strict_version.match(self.mp_fw_version):
                raise ValueError("Invalid MicroPython firmware version format")

    @staticmethod
    def build_checksum(data: bytes) -> int:
        """
        Calculate a Fletcher8 checksum for the given data.

        This function implements the Fletcher8 checksum algorithm, which computes
        a checksum value by maintaining two running sums of the input bytes.
        The two sums are then combined using bitwise operations to produce a
        single byte checksum value.

        Args:
            data (bytes): The input data for which to calculate the checksum.

        Returns:
            int: An 8-bit checksum value (0-255) computed using the Fletcher8 algorithm.

        Example:
            >>> checksum = build_checksum(b'hello')
            >>> isinstance(checksum, int)
            True
        """
        sum1 = 0
        sum2 = 0
        for b in data:
            sum1 = (sum1 + b) % 255
            sum2 = (sum2 + sum2) % 255
        return ((sum2 << 4) ^ sum1) & 0xFF

    def verify_checksum(self) -> bool:
        """
        Verify the Fletcher8 checksum for the frame.
        This method compares the checksum stored in the frame (self.cs) with a
        calculated checksum based on the source master frame data. The stored
        checksum is expected to be in hexadecimal format.

        Returns:
            bool: True if the calculated checksum matches the expected checksum,
                  False otherwise.
        """
        if (
            not self.from_master
            or not self.source_frame_from_master
            or not self.checksum
        ):
            return False

        # explain int(checksum_part, 16):
        # - Converts the hexadecimal string 'checksum_part' to an integer
        # - '16' indicates that the input string is in base 16 (hexadecimal)
        expected_checksum = int(self.checksum, 16)

        # Calculate the checksum for the data part
        calculated_checksum = self.build_checksum(self.source_frame_from_master.encode())
        return calculated_checksum == expected_checksum

    def is_ping_order(self) -> bool:
        return (
            self.from_master
            and self.frame_type == FrameType.PING
            and self.command_id == 0
        )

    def is_command_order(self) -> bool:
        return (
            self.from_master
            and self.frame_type == FrameType.CMD
            and self.command_id > 0
        )
