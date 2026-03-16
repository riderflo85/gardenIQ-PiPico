from src.core import DEVICE_UID
from src.core import FrozenDataclass
from src.core import event_emitter
from src.protocols.errors import CommandError

from .dataqueue import data_received
from .dataqueue import data_to_response
from .frame import CommandState
from .frame import Frame
from .frame import FrameType
from .handler import frame_handler
from .parser import FrameParser


class FrozRegisterCB(FrozenDataclass):
    __slots__ = ("name", "func")


async def on_order_received(raw_data: bytes) -> None:
    """
    Callback function to handle received data from USB communication.

    Args:
        raw_data (bytes): The raw data received from the USB communication.

    Returns:
        None
    """
    await data_received.put(raw_data.decode("utf-8").strip())


async def on_order_process(order: Frame) -> None:
    frame_to_response = frame_handler.handle_master_command(order)
    if not frame_to_response:
        err_msg = "Cannot handle and process the command. No response generated."
        err_type = CommandError.UNKNOW_ERR
        await event_emitter.emit("error:occured", err_msg, err_type, order)
        return

    await event_emitter.emit("response:ready", frame_to_response)


async def on_error_occurred(error_message: str, error_type: str, trigger_order: str | Frame) -> None:
    # Replace the spaces string in the error message with underscores `_`,
    # because the frame parsing function splits the frame string using space to seperate blocks.
    formated_err_msg = f"{error_type}::{error_message.replace(" ", "_")}"

    if isinstance(trigger_order, Frame):
        error_frame_obj = Frame(
            FrameType.ACK,
            trigger_order.device_uid,
            trigger_order.command_id,
            command_state=CommandState.ERROR,
            err_msg=formated_err_msg,
        )
    else:
        error_frame_obj = Frame(
            FrameType.ACK,
            DEVICE_UID,
            command_id=-502,
            command_state=CommandState.ERROR,
            err_msg=formated_err_msg + f":order:{trigger_order}",
        )
    error_frame_str = FrameParser.parse_from_frame_klass(error_frame_obj)
    await event_emitter.emit("response:ready", error_frame_str)


async def on_response_ready(frame_response_data: str) -> None:
    await data_to_response.put(frame_response_data)


# Initially, I wanted to use a dictionary instead of a tuple of classes.
# However, dictionaries are mutable, and I wanted the list of callbacks
#   to be immutable to avoid accidental modification errors.
# So, I created the FrozenDataclass class to achieve this.
cb_register = (
    FrozRegisterCB(name="order:received", func=on_order_received),
    FrozRegisterCB(name="order:process", func=on_order_process),
    FrozRegisterCB(name="response:ready", func=on_response_ready),
    FrozRegisterCB(name="error:occurred", func=on_error_occurred),
)
