# This three func intended to store telegram message object in sqlite (built in database of python) or
# echo on any message with one method despite of the message content.
# There we are converts object to string ang back, because sqlite can't store objects. 
# There are also another ways to do it. We don't storing whole message object, only important elements (text + link)
# Storing message in DB: First we getting content of the message 
# (str link or list) to append it to the sending message.
# Next we getting caption (text) of the message. Finally we getting type of the message.
# After saving it, to send message we have to determine appropriate method to sends message
# by message content via get_str_message_send_method func with output of get_message_content func as a parameter


def get_message_send_method(message, check_func=helpers.effective_message_type):  # Get send method by message type
    """
    With it, you can echo for the most popular message type. The library doesn't have a built-in 'autodetect' method 
    to get the appropriate method for the answer. helpers.effective_message_type() returns str name of content.
    """
    if check_func(message) == 'photo':
        method = bot.send_photo  # method
    elif check_func(message) == 'video':
        method = bot.send_video  # method
    elif check_func(message) == 'audio':
        method = bot.send_audio  # method
    elif check_func(message) == 'text':
        method = bot.send_message  # method
    else:
        message.reply_text('I can detect mathod only for photo, video, audio or text')
        return
    return method


def get_message_content(message):
    """
    Content it is just a simple telegram link. helpers.effective_message_type() returns str name of content.
    To send back message by method also needs to specify appropriated content from current message.
    """
    if helpers.effective_message_type(message) == 'photo':
        content = message.photo[-1].file_id  # str
    elif helpers.effective_message_type(message) == 'video':
        content = message.video.file_id  # str
    elif helpers.effective_message_type(message) == 'audio':
        content = message.audio.file_id  # str
    elif helpers.effective_message_type(message) == 'text':
        content = message.text  # str
    else:
        return
    return content


def get_str_message_send_method(message):  # Get send method by string stored in DB
    """
    With it you can get send method by string (output of get_message_content). This func calls get_message_send_method. 
    """
    return get_message_send_method(message, check_func=lambda arg: arg)


#  Example:
 
 
#  Storing: (With context.chat_data (dict) you can pass data from func to func)

context.chat_data['message_content'] = get_message_content(update.message)  # str link
context.chat_data['message_caption'] = update.message.caption  # text of message
context.chat_data['post_content_type'] = helpers.effective_message_type(update.message) # str type of content


#   Sending:
    
message_send_method = get_str_message_send_method(context.chat_data['post_content_type'])  # Method
message_send_method(chat_id=update.effective_user.id, text=post_content, audio=post_content, video=post_content, 
                    photo=post_content, caption=post_caption)  # update.effective_user.id - sender id.
                    # Don't forget to past appropriate id
