import logging
from geopy.geocoders import Yandex  # For location
from telegram import Bot
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, Filters
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler
from telegram.utils.request import Request

DEFAULT_PHOTO = ['AgADAgADWqwxG2mlAAFIDtF_p9eVWNcS2bkPAAQBAAMCAAN4AAMKFQcAARYE']  # Add your photo instead of this one
# Conversation_registration_handler states, every func there ambiguous: process previous message and send new
(USER_GENDER, USER_AGE, USER_COUNTRY, USER_CITY,
 USER_PHOTOS, ADD_PHOTO, USER_COMMENT, USER_CONFIRM, END_REG) = range(1, 10)
STEPS_COUNT = END_REG - len([USER_CITY, ADD_PHOTO, USER_CONFIRM, END_REG])  # No every step is shown to the user


def get_scrolling_profile_keyboard(shower_id):  # Inline keyboard for list user photos
    return InlineKeyboardMarkup([[
        InlineKeyboardButton('Back', callback_data=f'back_photo {shower_id}'),
        InlineKeyboardButton('Next', callback_data=f'next_photo {shower_id}')]])


# # # HELP FUNCS # # #
def send_misunderstand_text(update, end_string):
    update.message.reply_text(f'I do not understand you, type {end_string}')


def get_location_from_coordinates(location, context): # maybe it would be better to combine this into one?
    location = locator.reverse(f'{location.latitude}, {location.longitude}', exactly_one=True)
    context.chat_data['user']['country'] = [place.strip() for place in location.address.split(',')][-1]  # country
    context.chat_data['user']['city'] = [place.strip() for place in location.address.split(',')][-2]  # city


# # # CONVERSATIONS # # # #
# noinspection PyUnusedLocal
def start_reg(update, context):
    keyboard = [['Start'], ['/Cancel'], ]
    update.message.reply_text('Great! During the registration I will ask you for\
    gender, age, country, city, photos and comment.', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return USER_GENDER


# noinspection PyUnusedLocal
def ask_user_gender(update, context):
    keyboard = [['Male'], ['Female'], ['Back', 'Skip'], ['/Cancel'], ]
    update.message.reply_text(f'step {USER_GENDER} out of  {STEPS_COUNT}.\n\nChoose your gender.',
                              reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

    return USER_AGE


def ask_user_age(update, context):
    context.chat_data['user'] = {}  # Create dict for profile_data

    # # # PROCESS OLD MESSAGE # # #
    message_text = update.message.text.lower().strip()
    if 'male' in message_text:
        context.chat_data['user']['gender'] = 'male'
    elif 'female' in message_text:
        context.chat_data['user']['gender'] = 'female'
    elif 'skip' not in message_text and 'back' not in message_text:
        send_misunderstand_text(update, '"male" or "female."')
        return USER_GENDER  # Return previous step
    # # # SEND NEW MESSAGE # # #
    keyboard = [['Back', 'Skip'], ['/Cancel'], ]
    update.message.reply_text(f'Step {USER_AGE} out of  {STEPS_COUNT}.\n\nHow old are you?',
                              reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return USER_COUNTRY


def ask_user_country(update, context):
    # # # PROCESS OLD MESSAGE # # #
    message_text = update.message.text.lower().strip()
    age = ''.join([letter for letter in update.message.text if letter.isdigit()])  # Get digits from the message
    if 0 < len(age) < 3:
        context.chat_data['user']['age'] = message_text
    elif 'skip' not in message_text and 'back' not in message_text:
        send_misunderstand_text(update, 'How old are you. For example, type: "25 years."')
        return USER_COUNTRY
    # # # SEND NEW MESSAGE # # #
    if update.message.chat.type == 'group':  # No location for public chat
        context.chat_data['location_button'] = ''  # Empty button = remove button from keyboard
    else:
        context.chat_data['location_button'] = [KeyboardButton(text="Send country location", request_location=True)]
        #  Getting whole location, but choosing only country from it
    # # # SEND NEW MESSAGE # # #
    keyboard = [context.chat_data['location_button'], ['Back', 'Skip'], ['Cancel']]
    update.message.reply_text(f'Step {USER_COUNTRY} out of  {STEPS_COUNT}.\n\nType your country.',
                              reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return USER_CITY


def ask_user_city(update, context):  # USER_COUNTRY don't have validation
    # Do not create var message_text because it can not exist
    # # # PROCESS OLD MESSAGE # # #
    if update.message.location:  # If user sent location by button
        return ask_user_photos(update, context)  # Jump to next state and continue from there. ask_user_photos handlers
        #  location. It will get country and city from a location (as argument, we passing update from a previous state.
    elif 'skip' not in update.message.text.lower().strip() and 'back' not in update.message.text.lower().strip():
        context.chat_data['user']['country'] = update.message.text.strip()  # Without .lower()
    else:
        return ask_user_photos(update, context)  # Will skipped twice. Go ask photos immediately:
    # # # SEND NEW MESSAGE # # #
    keyboard = [context.chat_data['location_button'], ['Back', 'Skip'], ['Cancel']]
    update.message.reply_text(f'Step {USER_COUNTRY}.5 out of  {STEPS_COUNT}.\n\nType your city.',
                              reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return USER_PHOTOS


def ask_user_photos(update, context):  # user_city don't have validation
    # Do not create var message_text because it can not exist
    #  Maybe no need to get the city from the location, as the user may want to specify only a country ?
    # # # PROCESS OLD MESSAGE # # #
    if update.message.location:  # If location was not send before
        get_location_from_coordinates(update.message.location, context)  # user_city exist only if location was send
    elif 'skip' not in update.message.text.lower().strip() and 'back' not in update.message.text.lower().strip():
        context.chat_data['user']['city'] = update.message.text.strip()  # Without .lower()
    # # # SEND NEW MESSAGE # # #
    photo_keyboard = ['', ['Use account photos'], '', ['Back', 'Skip'], ['Cancel']]  # '' - placeholders
    context.chat_data['photo_keyboard'] = context.chat_data.get('photo_keyboard', photo_keyboard)  # If user go back
    update.message.reply_text(f'Step {USER_CITY} out of  {STEPS_COUNT}.\n\n\
attach photos to the message when finished - type finish',
                              reply_markup=ReplyKeyboardMarkup(context.chat_data['photo_keyboard'],
                                                               resize_keyboard=True))
    return USER_COMMENT


def few_photos_handler(update, context):  # Activates if user send a photo
    photo = update.message.photo[-1].file_id  # [-1] = Choose photo with best quality
    new_id = update.message.media_group_id
    old_id = context.chat_data.setdefault('old_media_group_id', int())  # For case if user chose profile_photos option
    context.chat_data['photo_keyboard'][0] = ['Finish']
    context.chat_data['photo_keyboard'][2] = ['Remove selected photos']
    context.chat_data['photo_keyboard'][3][1] = ''  # Remove skip option from the keyboard.
    # No put empty '' inside the list, TG will do not understand it. Remember: this is a list (placed on one line)

    if photo not in context.chat_data.setdefault('photos', list()):  # If not exist:
        context.chat_data['photos'].append(photo)
    if old_id != new_id:  # don't send message "add else photo" for every photo in message/album
        update.message.reply_text('Add more photos?', reply_markup=ReplyKeyboardMarkup(
            context.chat_data['photo_keyboard'], resize_keyboard=True))
    context.chat_data['old_media_group_id'] = new_id  # Already old :)
    return USER_COMMENT


def ask_user_comment(update, context):
    # # # PROCESS OLD MESSAGE # # #
    message_text = update.message.text.lower().strip()
    if 'use account photos' in message_text:
        #  profile_photos - photos of account, photos - selected photos.
        photos = context.chat_data.get('photos', list())
        profile_photos = [photo[-1].file_id for photo in bot.get_user_profile_photos(update.effective_user.id).photos]
        if profile_photos:
            context.chat_data['photos'] = [photo for photo in profile_photos if photo not in photos]  # Unique
            context.chat_data['photo_keyboard'][0] = ['Finish']
            context.chat_data['photo_keyboard'][1] = ''  # Remove get_photos_profile option from keyboard
            context.chat_data['photo_keyboard'][2] = ['Remove selected photos']
            context.chat_data['photo_keyboard'][3][1] = ''  # Remove skip option from keyboard.
            update.message.reply_text('Add more photos?', reply_markup=ReplyKeyboardMarkup(
                context.chat_data['photo_keyboard'], resize_keyboard=True))
        else:
            update.message.reply_text('Your profile has no photos.')
        return USER_COMMENT  # User may wish to add else photos after inserting photos from the account.
    elif 'remove selected photos' in message_text:
        del context.chat_data['photos']  # del because checking for exists, not for empties.
        # Return keyboard for originated form
        context.chat_data['photo_keyboard'] = ['', ['Use account photos'], '', ['Back', 'Skip'], ['Cancel']]
        update.message.reply_text('Removed.\n\nAdd more photos?', reply_markup=ReplyKeyboardMarkup(
            context.chat_data['photo_keyboard'], resize_keyboard=True))
        return USER_COMMENT
    # # # SEND NEW MESSAGE # # #
    keyboard = [['Back', 'Skip'], ['Cancel']]
    update.message.reply_text(f'Step {USER_PHOTOS} out of  {STEPS_COUNT}.\n\nAny additional info.',
                              reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return USER_CONFIRM


def ask_user_confirm(update, context):
    # No validation for comment. Last step can't get back_r in update
    # # # PROCESS OLD MESSAGE # # #
    message_text = update.message.text.lower().strip()
    if 'skip' not in message_text:
        context.chat_data['user']['comment'] = update.message.text.strip()
    # # # SEND NEW MESSAGE # # #
    keyboard = [['Back', 'Finish'], ['Cancel']]
    context.chat_data['message'] = update.message.reply_text('Your profile will look like this:',
                                                             reply_markup=ReplyKeyboardMarkup(keyboard,
                                                                                              resize_keyboard=True))
    show_profile(update.effective_user.id, context.chat_data['user'],
                 context.chat_data.get('photos', DEFAULT_PHOTO)[0])
    return END_REG


def show_profile(user_id, profile_data, photo):  # For profile needs only one photo
    # # # PROCESS OLD MESSAGE # # #
    text = ''
    for key, value in profile_data.items():
        text += f'{key} - {value}.\n'
    bot.send_photo(user_id, photo, caption=text, reply_markup=get_scrolling_profile_keyboard(user_id))


def user_confirm_handler(update, context):
    message_text = update.message.text.lower().strip()
    message = update.message.reply_text(''''Do you like secrets? The only way to remove "reply_keyboard" in telegram API
is to send a new message and immediately delete one''', reply_markup=ReplyKeyboardRemove())  # So we deleting a keyboard
    message.delete()
    if 'finish' in message_text:
        return ConversationHandler.END
    elif 'back' not in message_text:
        send_misunderstand_text(update, '"Finish", "back", or "/Cancel"')


def scrolling_profile_handler(update, context):
    """
    func gets in callback pressed button (next/back) and id of the owner of photos (shower_id)
    1. Checks if there photo to leaf,
    2.Create dict with user_id of owners of photos, that user scrolled
    3. Assign index as value. So it has looks like user_id: index.
    4. Check if current index not more of len(photos)
    5. Send (edit) message with a new photo.
    6. Reply to the TG server that the update has been received.
    """
    button, shower_id = update.callback_query.data.split()
    shower_id = int(shower_id)
    photos = context.chat_data.get('photos', list())
    if len(photos) > 1:
        context.chat_data.setdefault('photo_indexes', {}).setdefault(shower_id, 0)
        # Shower_id guarantees uniqueness of a key for each profile
        context.chat_data['photo_indexes'][shower_id] += 1 if button == 'next_photo' else -1

        if abs(context.chat_data['photo_indexes'][shower_id]) == len(photos):
            context.chat_data['photo_indexes'][shower_id] = 0

        bot.edit_message_media(chat_id=update.effective_user.id, message_id=update.callback_query.message.message_id,
                               media=InputMediaPhoto(photos[context.chat_data['photo_indexes'][shower_id]],
                                                     caption=update.callback_query.message.caption),
                               reply_markup=get_scrolling_profile_keyboard(shower_id))

    update.callback_query.answer()


# noinspection PyUnusedLocal
def cancel_handler(update, context):
    update.message.reply_text('CANCELED', reply_markup=ReplyKeyboardRemove())  # Remove any previous keyboard
    return ConversationHandler.END


conversation_registration_handler = ConversationHandler(

    entry_points=[CommandHandler('reg', start_reg)],

    states={
        USER_GENDER: [MessageHandler(Filters.text, ask_user_gender)],

        USER_AGE: [MessageHandler(Filters.regex(r'Back'), start_reg),
                   MessageHandler(Filters.text, ask_user_age)],

        USER_COUNTRY: [MessageHandler(Filters.regex(r'Back'), ask_user_gender),
                       MessageHandler(Filters.text, ask_user_country)],

        USER_CITY: [MessageHandler(Filters.regex(r'Back'), ask_user_age),
                    MessageHandler(Filters.location, ask_user_city),  # No use filters.all to give chance
                    MessageHandler(Filters.text, ask_user_city)],  # for fallback (currently empty)

        USER_PHOTOS: [MessageHandler(Filters.regex(r'Back'), ask_user_country),
                      MessageHandler(Filters.location, ask_user_photos),  # No use filters.all to give chance
                      MessageHandler(Filters.text, ask_user_photos)],  # for fallback (currently empty)

        USER_COMMENT: [MessageHandler(Filters.regex(r'Back'), ask_user_country),
                       MessageHandler(Filters.photo, few_photos_handler),
                       MessageHandler(Filters.text, ask_user_comment), ],

        USER_CONFIRM: [MessageHandler(Filters.regex(r'Back'), ask_user_city),
                       MessageHandler(Filters.text, ask_user_confirm), ],

        END_REG: [MessageHandler(Filters.regex(r'Back'), ask_user_comment),
                  MessageHandler(Filters.text, user_confirm_handler), ], },
    fallbacks=[CommandHandler('Cancel', cancel_handler)]
)

if __name__ == '__main__':
    token = 'YOUR TOKEN'
    yandex_api_key = "YOR TOKEN"

    logging.basicConfig()
    PROXY_URL = 'https://telegg.ru/orig/bot'  # Public TG proxy if TG blocked into your country
    request = Request(connect_timeout=1, read_timeout=1, con_pool_size=8)
    bot = Bot(token=token, request=request, base_url=PROXY_URL)
    updater = Updater(bot=bot, use_context=True)
    locator = Yandex(api_key=yandex_api_key, timeout=3)  # for location you also can use nominatim,
    # but you have to change parsing func (get_location_from_coordinates).

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(scrolling_profile_handler, pattern=r'^back_photo|^next_photo'))
    dispatcher.add_handler(conversation_registration_handler)
    updater.start_polling()
    updater.idle()
