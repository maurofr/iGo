# imports the Telegram's API
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from staticmap import StaticMap, CircleMarker, IconMarker, Line
import os
import random
import time
from class_igo import *

TOKEN_ALBERT = "1848938537:AAEImx4WFL91JFydr9FnfmUIHMuxw1YFJqY"
TOKEN_MAURO = "1609114464:AAHK86rLORDYaxcjKw9gEOy0sw_IQ04i_oY"

TOKEN = TOKEN_ALBERT  # explicar al readme lo del token, que a l'entregar la pràctica això s'ha de treure

PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'
TRAFFIC_COLORS = ['blue', 'green', 'yellow', 'orange', 'red', 'purple', 'black']

people = {}  # it is a dictionary with key the id of the user, and attributes the latitude and longitude of its position
positions = {}  # dictionary with id as keys, every id containing a dictionary with the name of a place as id and its coordinates as attributes


def is_number(s):
    """
    Indicates if a string is a float.

    PRE: - s: the string
    ----------------------------------------------------------------------------
    POST: Returns true if it could be a float, and false otherwise.
    """
    try:
        float(s)
        return True
    except ValueError:
        return False


def read_arguments(context, update):
    """
    It reads the arguments that are passed in the 'pos', 'go' and 'set' functions.
    If the attributes received are coordinates, it returns their value. Otherwise,
    it trasforms the name of a place to its coordinates. If the attribute received
    is not correct, or if there isn't an attribute, the function returns an error
    and it explains why it failed.
    """
    place = ""
    is_coordinates = True
    coordinates = []
    for symbol in context.args:
        is_coordinates = is_number(symbol)  # to check if the attributes are coordinates or the name of a place
        if(is_coordinates):
            coordinates.append(float(symbol))
        place = place + ' ' + symbol
    if is_coordinates and len(coordinates) == 2:
        return coordinates[0], coordinates[1]  # we have received coordinates
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


def start(update, context):
    """It starts the chat with the user."""
    id = update.effective_chat.id
    fullname = update.effective_chat.first_name + ' ' + update.effective_chat.last_name
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Hi %s! I am the GuiderBot. Try the /help command to know more about me and my functions!" % (fullname))


def help(update, context):
    """It explains all the available functions and what they do."""
    bot_info = ["You can execute the following commands:"]
    bot_info.append("/start - Say hi to the bot, he will reply back!")
    bot_info.append("/author - The name of the authors and a link to the GitHub repository will be displayed.")
    bot_info.append("/go destination - You will receive the optimal route, calculated with iGo, that goes from your position to the desired place.")
    bot_info.append("/where - You will receive a small map with your current location on it.")
    bot_info.append("/set name place - Save a place you usually go to with a name (only 1 word). This way you can /go name !")
    bot_info.append("/myplaces - Sends a list of your saved places.")

    msg = "\n".join(bot_info)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=msg)


def author(update, context):
    """
    It shows the name of the authors of this project and the GitHub link.
    (The GitHub repository will be private until the 1st of June of 2021)
    """
    keyboard = [[InlineKeyboardButton("GitHub", url="https://github.com/maurofr/iGo")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="The authors of this project are Mauro Filomeno and Albert Fugardo, you can see the full code in GitHub.",
                             reply_markup=reply_markup)


def go(update, context):
    """
    It calculates the shortest path from the current location to a destination given by
    the user, and it prints the path on a map. It also gives the expected time to
    go from the origin to the destination following the path.
    """
    id = update.effective_chat.id
    try:
        origin_lat = people[id][0]
        origin_lon = people[id][1]

        if id in positions and context.args[0] in positions[id]:  # if the place the user wants to go is a 'set' place
            destination_lat = positions[id][context.args[0]][0]
            destination_lon = positions[id][context.args[0]][1]
        else:
            destination_lat, destination_lon = read_arguments(context, update)

        path, total_time = bcn_graph.get_shortest_path_with_ispeed(origin_lat, origin_lon, destination_lat, destination_lon)

        file = "%d.png" % random.randint(1000000, 9999999)
        map = StaticMap(SIZE, SIZE)  # map
        path_size = len(path)  # size

        map.add_marker(IconMarker((path[0]['x'], path[0]['y']), 'marker.png', 16, 32))  # highlights the origin node
        map.add_marker(IconMarker((path[-1]['x'], path[-1]['y']), 'flag.png', 0, 22))  # highlights the destination node

        i = 0
        while i < path_size-1:  # it draws the path on the map
            congestion = bcn_graph.digraph.edges[path[i]['node_id'], path[i+1]['node_id']]['congestion']
            map.add_line(Line(((path[i]['x'], path[i]['y']), (path[i+1]['x'], path[i+1]['y'])), TRAFFIC_COLORS[congestion], 3))
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


def where(update, context):
    """Prints the current location of the user on a map."""
    id = update.effective_chat.id
    try:
        lat = people[id][0]
        lon = people[id][1]
        file = "%d.png" % random.randint(1000000, 9999999)
        mapa = StaticMap(SIZE, SIZE)  # adjusts the size of the map
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
            text='Share your current position to be able to show it on a map!')


def pos(update, context):
    """It sets the current location of the user to the position given by him."""
    try:
        id = update.effective_chat.id
        a = context.args[0]  # to make an error appear if no name has been given
        if id in positions and context.args[0] in positions[id]:  # if the place where the user is located is a 'set' placed
            lat = positions[id][context.args[0]][0]
            lon = positions[id][context.args[0]][1]
        else:
            lat, lon = read_arguments(context, update)
        people[id] = (lat, lon)

        place = ""
        for word in context.args:
            place += " "
            place += word
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='You are now in' + place)
    except:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Write the position where you want to be!')


def set(update, context):
    id = update.effective_chat.id
    key = context.args[0]
    context.args.remove(key)
    lat, lon = read_arguments(context, update)
    if id not in positions:
        positions[id] = {}  # we declare positions[id] as a dictionary if it is empty
    positions[id][key] = (lat, lon)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Successfully saved '" + key + "' as a location.")


def print_places(update, context):
    id = update.effective_chat.id
    if id in positions:
        for key in positions[id].items():
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=key[0] + ':')
            lat = key[1][0]
            lon = key[1][1]
            file = "%d.png" % random.randint(1000000, 9999999)
            mapa = StaticMap(SIZE, SIZE)  # adjusts the size of the map
            mapa.add_marker(IconMarker((lon, lat), 'house.png', 16, 32))
            image = mapa.render()
            image.save(file)
            context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=open(file, 'rb'))
            os.remove(file)
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="There are no saved locations. You can save one with /set. For more info see /help.")


def current_position(update, context):
    """This function is called every time we get a new location of a user."""
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
dispatcher.add_handler(CommandHandler('myplaces', print_places))
dispatcher.add_handler(MessageHandler(Filters.location, current_position))

print("Starting the bot, please wait a few seconds...")
bcn_graph = iGraph(PLACE, GRAPH_FILENAME, HIGHWAYS_URL, CONGESTIONS_URL)
try:
    bcn_graph.get_traffic()
except:
    print("Could not retrieve live traffic data")

# it starts the bot
updater.start_polling()
print("The bot is now operative")

while True:
    # every 5 minutes the congestions are updated, because they could have changed
    time.sleep(300)
    try:
        bcn_graph.get_traffic()
        print("Successfully updated live traffic data.")
    except:
        print("An error occurred while getting live traffic data.")
