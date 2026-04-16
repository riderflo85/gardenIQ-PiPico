from src.core.models import ModelType
from src.protocols.errors import FrameParsingError
from src.protocols.settings import ETX
from src.protocols.settings import STX
from src.protocols.usb.frame import CommandState
from src.protocols.usb.frame import Frame
from src.protocols.usb.frame import FrameType


class FrameParser:
    """
    Parser for communication frames between the device and master service.

    This class provides static methods to parse frame strings received from master service
    into structured Frame objects. It validates frame format, extracts components, and handles
    different command states and response types.
    This class is responsible for parsing and validation only.
    It does NOT access the database or perform any business logic.
    """

    @staticmethod
    def parse_from_master(recv_str: str) -> Frame:
        """
        Parse a frame string received from a master service into a Frame object.

        This method parses a newline-terminated string from a master service and extracts all frame components
        including frame type, device UID, command ID, command state, and optional data fields such as
        firmware versions or error messages.

        Args:
            recv_str (str): The raw string received from the master service. Must end with a newline character.
                        Expected format: "STX frame_type device_uid command_id command_state [data...] ETX checksum\n"

        Returns:
            Frame: A Frame object containing all parsed components from the received string.

        Raises:
            ValueError: If the received string does not end with a newline character.
            ValueError: If the received string has fewer than 7 parts (minimum valid frame).
            ValueError: If STX or ETX markers are invalid.
            ValueError: If the frame type cannot be parsed.

        Notes:
            - When command_id is 0 (ping), no additional args are expected.
        """
        if not recv_str.endswith("\n"):
            raise FrameParsingError("The received string does not end with a newline character. It's invalid frame !")

        recv_str = recv_str.removesuffix("\n")
        # Remove the checksum part for storing in Frame.source_frame_from_master
        recv_str_without_cs = recv_str.rsplit(" ", 1)[0]

        parts = recv_str.split(" ")

        # Minimum valid frame has 6 parts: STX, frame_type, device_uid, command_id, command_state, ETX, checksum
        # E.G: parts = "< PING device123 0 > 3C"
        # OR: parts = "< PING UKW_DEV_UID 0 > 3C" UKW is UNKNOWN
        if len(parts) < 6:
            raise FrameParsingError(
                f"The received string is too short. Warning: the system may be infected. recv: {recv_str}"
            )

        # Extract and validate basic components
        stx = parts[0]
        etx = parts[-2]
        checksum = parts[-1]

        if stx != STX:
            raise FrameParsingError(f"Invalid STX in received frame. Received: {stx}")
        if etx != ETX:
            raise FrameParsingError(f"Invalid ETX in received frame. Received: {etx}")

        # Parse frame type
        frame_type = FrameType.from_string(parts[1])
        if not frame_type:
            raise FrameParsingError(f"Invalid frame type in received frame. Received: {parts[1]}")

        # Extract device UID and command ID
        device_uid = parts[2]
        command_id = int(parts[3])
        command_slug = None
        args_values = ()
        model = None
        model_fields_values = ()

        # Parse args values
        if command_id == -1:
            # Is a initial command to received all Order language.
            model = ModelType.from_string(parts[4])
            model_fields_values = tuple(parts[5].split(";"))
        elif command_id > 0:
            command_slug = parts[4]
            args = parts[5]
            if len(parts) > 6 and ("," in args or args != ">"):
                args_values = tuple(args.split(","))
        # command_id == 0 is a ping command, so no args

        return Frame(
            frame_type=frame_type,
            device_uid=device_uid,
            command_id=command_id,
            from_master=True,
            model=model,
            model_attrs_values=model_fields_values,
            command_slug=command_slug,
            args_values=args_values,
            checksum=checksum,
            source_frame_from_master=recv_str_without_cs,
        )

    @staticmethod
    def parse_from_frame_klass(frame_obj: Frame) -> str:
        """
        Serialize a Frame object into a string representation for transmission.

        This method converts a Frame object into a properly formatted string that can be
        sent to a master service, including STX/ETX markers and a checksum for data integrity.

        Args:
            frame_obj (Frame): The Frame object to serialize. Must not be a master-originated frame.

        Returns:
            str: A formatted frame string with the following structure:
                "<STX> <frame_type> <device_uid> <command_id> [conditional_part] <ETX> <checksum>\n"
                where:
                - STX/ETX are start/end transmission markers
                - conditional_part depends on command_id and command_state
                - checksum is a 2-digit uppercase hexadecimal value

        Raises:
            FrameParsingError: If frame_obj.from_master is True, as master frames
                              cannot be serialized using this method.

        Note:
            The conditional frame part varies based on command_id and command_state:
            - If command_state is ERROR, the conditional part is the error message (err_msg).
            - If command_id is 0 (ping response), the conditional part includes firmware versions.
            - If command_id > 0, the conditional part is the ok_data. e.g. Back order `get_temp` -> ok_data == 21.
            - If command_id == -1, there is no conditional part.
        """
        if frame_obj.from_master:
            raise FrameParsingError("Cannot build frame from master frame.")

        # Build conditional frame part based on command_id and command_state
        # local variables = fewer attribute lookups (performance gain in MicroPython)
        command_id = frame_obj.command_id
        state = frame_obj.command_state

        if state == CommandState.ERROR:
            conditionnal_part = frame_obj.err_msg
        elif command_id == 0:  # is a ping response
            conditionnal_part = f"GDFW={frame_obj.gd_fw_version} MPFW={frame_obj.mp_fw_version}"
        elif command_id > 0:
            conditionnal_part = frame_obj.ok_data
        else:
            # command_id == -1 is a initial order language response. Have not data to send
            conditionnal_part = None

        parts = [
            STX,
            frame_obj.frame_type,
            frame_obj.device_uid,
            str(command_id),
            str(state),
        ]
        if conditionnal_part:
            parts += [str(conditionnal_part), ETX]
        else:
            parts.append(ETX)

        # Build complete frame
        frame_str = " ".join(parts)
        checksum = Frame.build_checksum(frame_str.encode())

        # explain f"{checksum:02X} formatting:
        # - f"..." indicates an f-string, allowing inline expressions
        # - {checksum:02X} formats 'checksum' as a hexadecimal string
        #   - 0: pad with leading zeros if necessary
        #   - 2: ensure at least 2 characters wide
        #   - X: use uppercase hexadecimal digits (A-F)
        return f"{frame_str} {checksum:02X}\n"
