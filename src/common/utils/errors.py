def format_error_message(error_message, replacements):
    for i, replacement in enumerate(replacements):
        placeholder = f"({i})"
        error_message = error_message.replace(placeholder, replacement)

    return error_message
