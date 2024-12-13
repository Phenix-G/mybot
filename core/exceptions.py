import logging
import traceback
from typing import Callable, Optional


def handle_exception(
    e: Exception,
    message: str = "An error occurred",
    notify_func: Optional[Callable[[str], None]] = None,
    source: str = "app",
):
    """
    Handle exception with logging and optional notification
    Args:
        e: The exception
        message: Custom error message
        notify_func: Optional function to send notification
        source: Source of the error (bot/web)
    """
    # Get full traceback
    error_traceback = "".join(traceback.format_tb(e.__traceback__))

    # Get original error location (for brief display)
    tb = traceback.extract_tb(e.__traceback__)[-1]
    error_location = f'File "{tb.filename}", line {tb.lineno}, in {tb.name}'

    # Combine error message
    error_message = (
        f"{message}: {str(e)}\n"
        f"Location: {error_location}\n"
        f"Full traceback:\n{error_traceback}"
    )

    # Log the error directly using error logger with source
    extra = {"source": source}
    logging.error(error_message, extra=extra)

    # Send notification if function provided
    if notify_func:
        try:
            notify_func(error_message)
        except Exception as notify_error:
            logging.error(f"Failed to send notification: {notify_error}", source=source)
