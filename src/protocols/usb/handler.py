from src.__version__ import __version__
from src.__version__ import micropython_version
from src.core import DEVICE_UID

from .frame import Frame
from .frame import FrameType
from .parser import FrameParser


class FrameHandler:

    def handle_master_command(self, frame: Frame) -> None:
        if not frame.from_master:
            raise ValueError("Frame is not from master. Cannot execute.")

        # Verify checksum
        if not frame.verify_checksum():
            raise ValueError(
                f"Checksum verification failed for device {frame.device_uid}. " "Possible command jailbreak detected !"
            )

        if frame.is_ping_order():
            self._handle_ping_order()
        elif frame.is_command_order():
            self._handle_command_order()
        else:
            return

    def _handle_ping_order(self) -> None:
        """Construct the ping order response with versions and device uid.
        Send the response to master.
        """
        frame_obj = Frame(
            frame_type=FrameType.ACK,
            device_uid=DEVICE_UID,
            command_id=0,
            gd_fw_version=__version__,
            mp_fw_version=micropython_version,
        )
        frame_response = FrameParser.parse_from_frame_klass(frame_obj)  # noqa: F841
        # TODO: Send frame_response to master service.
        #       Create function to this !

    def _handle_command_order(self) -> None:
        """Fetch the command in command store.
        Execute command.
        Construct the command order response.
        Send the response to master.
        """
        # TODO: Finish this method when the command store are available.
