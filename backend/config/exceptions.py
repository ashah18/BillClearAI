from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled


def custom_exception_handler(exc, context):
    """Custom exception handler that returns friendly rate-limit messages on 429."""
    response = exception_handler(exc, context)

    if isinstance(exc, Throttled):
        wait = exc.wait
        if wait is not None:
            if wait < 60:
                secs = int(wait) + 1
                time_str = f"{secs} second{'s' if secs != 1 else ''}"
            else:
                mins = int(wait // 60) + 1
                time_str = f"{mins} minute{'s' if mins != 1 else ''}"
        else:
            time_str = "some time"

        view = context.get("view")
        view_name = type(view).__name__ if view else ""

        if "Upload" in view_name:
            message = f"You've reached the limit for bill uploads. Please try again in {time_str}."
        elif "Chat" in view_name:
            message = f"You've reached the limit for chat messages. Please try again in {time_str}."
        elif "Dispute" in view_name:
            message = f"You've reached the limit for dispute letter generation. Please try again in {time_str}."
        elif "Analyze" in view_name:
            message = f"You've reached the limit for bill re-analysis. Please try again in {time_str}."
        elif "Register" in view_name:
            message = f"Too many registration attempts. Please try again in {time_str}."
        elif "PasswordReset" in view_name:
            message = f"Too many password reset requests. Please try again in {time_str}."
        else:
            message = f"Too many requests. Please try again in {time_str}."

        response.data = {"detail": message}

    return response
