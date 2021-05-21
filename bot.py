# importa l'API de Telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from staticmap import StaticMap, CircleMarker
import os
import random
from class_igo import *

TOKEN_ALBERT = "1848938537:AAEImx4WFL91JFydr9FnfmUIHMuxw1YFJqY"
TOKEN_MAURO = ""

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hola! Soc un bot bàsic. Envia la teva ubicació en directe per fer funcionar el bot.")

def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Explicar comandes disponibles.")

def author(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Els autors d'aquest projecte són el Mauro Filomeno i l'Albert Fugardo.") #posar-ho amb markdown, negreta etc

def go(update, context):
    try:
        s = ""
        for symbol in context.args:
            s = s + ' ' + symbol
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=s)
    except Exception as e:
        print(e)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='💣')

def where(update, context):
    try:
        lat, lon = 41.631735, 2.164324 #fer que agafi la localització de la funció current position
        print(lat, lon)
        fitxer = "%d.png" % random.randint(1000000, 9999999)
        mapa = StaticMap(500, 500)
        mapa.add_marker(CircleMarker((lon, lat), 'blue', 10))
        imatge = mapa.render()
        imatge.save(fitxer)
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(fitxer, 'rb'))
        os.remove(fitxer)
    except Exception as e:
        print(e)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='💣')

def current_position(update, context):
    '''aquesta funció es crida cada cop que arriba una nova localització d'un usuari'''

    # aquí, els missatges són rars: el primer és de debò, els següents són edicions
    message = update.edited_message if update.edited_message else update.message
    # extreu la localització del missatge
    lat, lon = message.location.latitude, message.location.longitude
    # escriu la localització al servidor
    print(lat, lon)
    # envia la localització al xat del client
    context.bot.send_message(chat_id=message.chat_id, text=str((lat, lon)))

# declara una constant amb el access token que llegeix de token.txt
TOKEN = TOKEN_ALBERT

# crea objectes per treballar amb Telegram
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# indica que quan el bot rebi la comanda /start s'executi la funció start
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('author', author))
dispatcher.add_handler(CommandHandler('go', go))
dispatcher.add_handler(CommandHandler('where', where))
dispatcher.add_handler(MessageHandler(Filters.location, current_position))

# engega el bot
updater.start_polling()
