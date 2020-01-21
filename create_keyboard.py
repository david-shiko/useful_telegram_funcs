def get_keyboard(*buttons):
    """
    Telegram keyboard it is list of lists.
    Inner list it is separate keyboard line.
    Outer list it is set of separate lines.
    Wrap multiple strings in one list if you want display them on the same line.
    :param buttons: list of string.
    :return: list of items.
    """
    keyboard = []
    for button in buttons:
        if not isinstance(button, list):
            button = [button]  # Newline = new list.
        keyboard.append(button)
    return keyboard  # List


def get_reply_markup(*buttons, resize_keyboard=True, one_time_keyboard=True):
    """
    Use ReplyKeyboardMarkup method to to append keyboard to the message.
    :param buttons: result from get_keyboard func.
    :param resize_keyboard: True - minimize keyboard size to size of the string. Default False.
    :param one_time_keyboard: Hide keyboard after using it. Default False.
    :return: ReplyKeyboardMarkup object.
    """
    keyboard = get_keyboard(*buttons)
    return ReplyKeyboardMarkup(keyboard, resize_keyboard, one_time_keyboard)

