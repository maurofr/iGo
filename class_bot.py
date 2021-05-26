# imports the Telegram's API
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from staticmap import StaticMap, CircleMarker, IconMarker, Line
import os
import random
import time
from class_igo import *

TOKEN_ALBERT = "1848938537:AAEImx4WFL91JFydr9FnfmUIHMuxw1YFJqY"
TOKEN_MAURO = "1609114464:AAHK86rLORDYaxcjKw9gEOy0sw_IQ04i_oY"

TOKEN = TOKEN_ALBERT #explicar al readme lo del token, que a l'entregar la pràctica això s'ha de treure

PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'

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
It reads the arguments that are passed in the 'pos', 'go' and 'set' functions.
If the attributes received are coordinates, it returns their value. Otherwise,
it trasforms the name of a place to its coordinates. If the attribute received
is not correct, or if there isn't an attribute, the function returns an error
and it explains why it failed.
"""
def read_arguments(context, update):
    place = ""
    is_coordinates = True
    coordinates = []
    for symbol in context.args:
        is_coordinates = is_number(symbol) #to check if the attributes are coordinates or the name of a place
        if(is_coordinates):
            coordinates.append(float(symbol))
        place = place + ' ' + symbol
    if is_coordinates and len(coordinates) == 2:
        return coordinates[0], coordinates[1] #we have received coordinates
    else:
        try:
            place = place + ' Barcelona'
            location = osmnx.geocoder.geocode(place)
            return location[0], location[1]
        except Exception as e:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='💣')
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='The place indicated is not correct. Please, write it again and check that the address is correct.')



"""It starts the chat with the user."""
def start(update, context):
    id = update.effective_chat.id
    fullname = update.effective_chat.first_name + ' ' + update.effective_chat.last_name
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi %s! I am the GuiderBot. Try the /help command to know more about me and my functions!" %(fullname))

"""It explains all the available functions and what they do."""
def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Explicar comandes disponibles.")

"""It shows the name of the authors of this project."""
def author(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="The authors of this project are Mauro Filomeno and Albert Fugardo.")

"""
It calculates the shortest path from the current location to a destination given by
the user, and it prints the path on a map. It also gives the expected time to
go from the origin to the destination following the path.
"""
def go(update, context):
    id = update.effective_chat.id
    try:
        origin_lat = people[id][0]
        origin_lon = people[id][1]

        if [context.args[0] in positions[id]]: #the place the user wants to go is a 'set' placed
            destination_lat = positions[id][context.args[0]][0]
            destination_lon = positions[id][context.args[0]][1]
        else:
            destination_lat, destination_lon = read_arguments(context, update)

        path, total_time = bcn_graph.get_shortest_path_with_ispeed(origin_lat, origin_lon, destination_lat, destination_lon)

        file = "%d.png" % random.randint(1000000, 9999999)
        map = StaticMap(SIZE, SIZE) #map
        path_size = len(path) #size

        map.add_marker(IconMarker((path[0]['x'], path[0]['y']), 'marker.png', 16, 32)) #highlights the origin node
        map.add_marker(IconMarker((path[-1]['x'], path[-1]['y']), 'flag.png', 0, 22)) #highlights the destination node

        i = 0
        while i < path_size-1: #it draws the path on the map
            map.add_line(Line(((path[i]['x'], path[i]['y']), (path[i+1]['x'], path[i+1]['y'])), 'blue', 3))
            i = i + 1
        image = map.render()
        image.save(file)
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(file, 'rb'))
        os.remove(file)

        minutes = total_time//60
        message = "The expected time is of " + str(minutes) + " minute(s)."
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    except Exception as e:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='You are not in a position!')




"Prints the current location of the user on a map."
def where(update, context):
    id = update.effective_chat.id
    try:
        lat = people[id][0]
        lon = people[id][1]
        file = "%d.png" % random.randint(1000000, 9999999)
        mapa = StaticMap(SIZE, SIZE) #adjusts the size of the map
        mapa.add_marker(IconMarker((lon, lat), 'marker.png', 16, 32))
        image = mapa.render()
        image.save(file)
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(file, 'rb'))
        os.remove(file)
    except:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='💣')
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Share your current position or use /pos to be able to show the position on a map!.')

"It sets the current location of the user to the position given by him."
def pos(update, context):
    id = update.effective_chat.id
    if [context.args[0] in positions[id]]: #if the place where the user is located is a 'set' placed
        lat = positions[id][context.args[0]][0]
        lon = positions[id][context.args[0]][1]
    else:
        lat, lon = read_arguments(context, update)
    people[id] = (lat, lon)


def set(update, context):
    id = update.effective_chat.id
    key = context.args[0]
    context.args.remove(key)
    lat, lon = read_arguments(context, update)
    try:
        a = positions[id]
    except: #positions[id] is empty
        positions[id] = {} #we declare positions[id] as a dictionary if it is empty
    positions[id][key] = (lat,lon)

def print_places(update, context):
    id = update.effective_chat.id
    for key in positions[id].items():
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=key[0] + '(' + str(key[1][0]) + ',' + str(key[1][1]) + ')')


def current_position(update, context):
    '''this function is called every time we get a new location of a user'''
    id = update.effective_chat.id
    message = update.edited_message if update.edited_message else update.message
    lat, lon = message.location.latitude, message.location.longitude
    people[id] = (lat, lon)


# it creates objects to be able to work with telegram
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher


dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('author', author))
dispatcher.add_handler(CommandHandler('go', go))
dispatcher.add_handler(CommandHandler('where', where))
dispatcher.add_handler(CommandHandler('pos', pos))
dispatcher.add_handler(CommandHandler('set', set))
dispatcher.add_handler(CommandHandler('print_places', print_places))
dispatcher.add_handler(MessageHandler(Filters.location, current_position))


bcn_graph = iGraph(PLACE, GRAPH_FILENAME, HIGHWAYS_URL, CONGESTIONS_URL) #posar-ho abans de les funcions
# it starts the bot
updater.start_polling()
people = {} #it is a dictionary with key the id of the user, and attributes the latitude and longitude of its position
positions = {} #dictionary with id as keys, every id containing a dictionary with the name of a place as id and its coordinates as attributes

while True:
    # every 5 minutes the congestions are updated, because they could have changed
    try:
        bcn_graph.get_traffic()
        print("Succesfully updated live traffic data") #hauríem de fer que també s'actualitzés el mapa, no?, o fer-ho cada minut lo del mapa
    except:
        print("An error ocurred while getting live traffic data")
    time.sleep(300)
