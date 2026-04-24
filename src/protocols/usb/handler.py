from src.__version__ import __version__
from src.__version__ import micropython_version
from src.core import DEVICE_UID
from src.models import ModelType
from src.stores import commands_store
from src.stores import init_pins_store

from .frame import CommandState
from .frame import Frame
from .frame import FrameType
from .parsers import FrameParser
from .parsers import parse_str_order_to_model
from .parsers import parse_str_pin_to_model


class FrameHandler:

    def handle_master_command(self, frame: Frame) -> None | str:
        if not frame.from_master:
            raise ValueError("Frame is not from master. Cannot execute.")

        if frame.device_uid not in (DEVICE_UID, "UKW_DEV_UID"):
            raise Exception(
                f"Received command for device UID {frame.device_uid},"
                " but this device UID does not match the current device UID."
            )

        # Verify checksum
        if not frame.verify_checksum():
            raise ValueError(
                f"Checksum verification failed for device {frame.device_uid}. " "Possible command jailbreak detected !"
            )

        if frame.is_ping_order():
            return self._handle_ping_order()
        elif frame.is_init_order():
            return self._handle_init_order(frame)
        elif frame.is_command_order():
            return self._handle_command_order()
        else:
            return

    def _handle_ping_order(self) -> str:
        """Construct the ping order response with versions and device uid.
        Send the response to master.
        """
        frame_obj = Frame(
            frame_type=FrameType.ACK,
            device_uid=DEVICE_UID,
            command_id=0,
            command_state=CommandState.OK,
            gd_fw_version=__version__,
            mp_fw_version=micropython_version,
        )
        frame_response = FrameParser.parse_from_frame_klass(frame_obj)
        return frame_response

    def _handle_command_order(self) -> None:
        """Fetch the command in command store.
        Execute command.
        Construct the command order response.
        Send the response to master.
        """
        # TODO: Finish this method when the command store are available.

    def _handle_init_order(self, frame: Frame) -> str:
        """Complete or update registry."""
        if frame.model == ModelType.ORDER:
            order_obj = parse_str_order_to_model(frame.model_attrs_values)
            commands_store.add_item(order_obj)
        elif frame.model == ModelType.PIN:
            pin_obj = parse_str_pin_to_model(frame.model_attrs_values)
            init_pins_store.add_item(pin_obj)
        else:
            raise ValueError(f"Model `{frame.model}` is not supported !")
        frame_obj = Frame(
            frame_type=FrameType.ACK,
            device_uid=DEVICE_UID,
            command_id=frame.command_id,
            command_state=CommandState.OK,
        )
        frame_response = FrameParser.parse_from_frame_klass(frame_obj)
        return frame_response


# Create a singleton of FrameHandler
frame_handler = FrameHandler()
