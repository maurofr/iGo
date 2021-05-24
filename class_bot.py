# importa l'API de Telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from staticmap import StaticMap, CircleMarker, IconMarker, Line
import os
import random
import time
from class_igo import *

TOKEN_ALBERT = "1848938537:AAEImx4WFL91JFydr9FnfmUIHMuxw1YFJqY"
TOKEN_MAURO = "1609114464:AAHK86rLORDYaxcjKw9gEOy0sw_IQ04i_oY"

# declara una constant amb el access token que llegeix de token.txt
TOKEN = TOKEN_MAURO

"""
It recieves a string and it returns true if it is a float, or false otherwise.
"""
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

"""
It reads the arguments that are passed in the 'pos' and 'go' functions. If the
attributes received are coordinates, i returns their value. Otherwise, it
trasforms the name of a place to its coordinates. If the attribute received is
not correct, or if there isn't an attribute, the function returns an error and
it explains why it failed.
"""
def read_arguments(context, update):
    #llegeix el lloc on es vol anar
    place = ""
    is_coordinates = True
    coordinates = []
    for symbol in context.args:
        is_coordinates = is_number(symbol)
        if(is_coordinates):
            coordinates.append(float(symbol))
        place = place + ' ' + symbol
    if is_coordinates and len(coordinates) == 2:
        return coordinates[0], coordinates[1] #hem rebut els atributs en forma de coordenades
    else:
        try:
            place = place + ' Barcelona'
            location = osmnx.geocoder.geocode(place)
            return location[0], location[1]
        except Exception as e: #crec que només hi ha excecpció quan no s'escriu res al costat de go, no, si posem campus nordBarcelona tampoc funciona
            print(e)
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='💣')
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='El lloc indicat  no és correcte. Siusplau, torna a escriure el lloc i comprova que el nom és correcte.') #canviar aquesta frase
            return 0,0


"""It starts the chat with the user."""
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hola! Soc un bot bàsic. Envia la teva ubicació en directe per fer funcionar el bot.")

"""It explains all the available functions and what they do."""
def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Explicar comandes disponibles.")

"""It shows the name of the authors of this project."""
def author(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Els autors d'aquest projecte són el Mauro Filomeno i l'Albert Fugardo.") #posar-ho amb markdown, negreta etc

"""
Calculates the shortest path from the current location to a destination given by
the user, and it prints the path on a map. It also gives the expected time to
go from the origin to the destination following the path.
"""
def go(update, context):
    try:
        origin_lat = dispatcher.user_data["lat"] #ara user_data és de type defaultdict i encara que "lat" i "lon" no existeixin, els hi assigna el valor de llista buida, pel que el codi no falla, però en teoria hauria de fallar a la funció get_shortest... i per tant el try except estaria ben fet suposo
        origin_lon = dispatcher.user_data["lon"]

        destination_lat, destination_lon = read_arguments(context, update) #estan en l'ordre que toca lat i lon??

        path, total_time = bcn_graph.get_shortest_path_with_ispeed(origin_lat, origin_lon, destination_lat, destination_lon)

        fitxer = "%d.png" % random.randint(1000000, 9999999)
        mapa = StaticMap(750, 750) #ajustar la mida del mapa
        mida = len(path)

        mapa.add_marker(IconMarker((path[0]['x'], path[0]['y']), 'marker.png', 16, 32)) #marca el node inicial
        mapa.add_marker(IconMarker((path[-1]['x'], path[-1]['y']), 'flag.png', 0, 22)) #marca el node final

        i = 0
        while i < mida-1:
            mapa.add_line(Line(((path[i]['x'], path[i]['y']), (path[i+1]['x'], path[i+1]['y'])), 'blue', 3))
            i = i + 1
        imatge = mapa.render()
        imatge.save(fitxer)
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(fitxer, 'rb'))
        os.remove(fitxer)

        minutes = total_time//60
        seconds = total_time%60
        message = "El temps esperat és de " + str(minutes) + " minut(s), " + str(seconds) + " segon(s)."
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    except:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='💣')
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Comparteix la teva ubicació o declara una amb /pos per poder mostrar la teva posició actual.')



"Prints the current location of the user on a map."
def where(update, context):
    try:
        lat = dispatcher.user_data["lat"]
        lon = dispatcher.user_data["lon"]
        print(lat, lon)
        fitxer = "%d.png" % random.randint(1000000, 9999999)
        mapa = StaticMap(750, 750) #ajustar la mida del mapa
        mapa.add_marker(IconMarker((lon, lat), 'marker.png', 16, 32))
        #mapa.add_marker(CircleMarker((lon, lat), 'blue', 10))
        imatge = mapa.render()
        imatge.save(fitxer)
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(fitxer, 'rb'))
        os.remove(fitxer)
    except:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='💣')
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Comparteix la teva ubicació per poder mostrar la teva posició actual.')

"It sets the current location of the user to the position given by him."
def pos(update, context): #si la ubicació en directe està engegada /pos no funciona bé correctament crec, perquè les dades en directe substitueixen a les de pos
    lat, lon = read_arguments(context, update)
    dispatcher.user_data["lat"] = lat
    dispatcher.user_data["lon"] = lon


def current_position(update, context):
    '''aquesta funció es crida cada cop que arriba una nova localització d'un usuari'''

    # aquí, els missatges són rars: el primer és de debò, els següents són edicions
    message = update.edited_message if update.edited_message else update.message
    # extreu la localització del missatge
    lat, lon = message.location.latitude, message.location.longitude
    # escriu la localització al servidor
    dispatcher.user_data["lat"] = lat
    dispatcher.user_data["lon"] = lon
    print("actualització = ",lat, lon)
    # envia la localització al xat del client
    context.bot.send_message(chat_id=message.chat_id, text=str((lat, lon)))


# crea objectes per treballar amb Telegram
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher



# indica que quan el bot rebi la comanda /start s'executi la funció start
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('author', author))
dispatcher.add_handler(CommandHandler('go', go))
dispatcher.add_handler(CommandHandler('where', where))
dispatcher.add_handler(CommandHandler('pos', pos))
dispatcher.add_handler(MessageHandler(Filters.location, current_position))

#carregar dades abans de començar
# Data
PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'

bcn_graph = iGraph(PLACE, GRAPH_FILENAME, HIGHWAYS_URL, CONGESTIONS_URL) #posar-ho abans de les funcions
#bcn_graph.get_traffic() #per les congestions

# engega el bot
updater.start_polling()

while True:
    # Cada 15 min actualitzem les congestions perque hauran variat
    try:
        bcn_graph.get_traffic()
        print("Succesfully updated live traffic data")
    except:
        print("An error ocurred while getting live traffic data")
    time.sleep(900)
