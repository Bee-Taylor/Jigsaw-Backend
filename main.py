import io

import socket
import flickrapi
from multiprocessing import Process
from PIL import Image
import requests
import time
import json
import numpy as np
from matplotlib import pyplot as plt
import random
import os
import png
from flask import Flask, send_file, request


app = Flask(__name__)

API_KEY = "f372261b6d63c60e2a16b7cbf9c8a801"
SECRET = "864baaa1a9d40f03"

def inverse_nobble(np_array):
    for y in range(np_array.shape[0]):
        for x in range(np_array.shape[1]):
            if np_array[y,x] > 100:
                np_array[y,x] = 0
            else:
                np_array[y,x] = 255
    return np_array

def nobble_to_2d(np_array):
    to_return = np.zeros(np_array.shape[:2])
    for y in range(np_array.shape[0]):
        for x in range(np_array.shape[1]):
            if min(np_array[y,x]) > 100:
                to_return[y,x] = 255
            else:
                to_return[y,x] = 0
    if to_return[0,0] > 0:
        inverse_nobble(to_return)
    return to_return

def split_into_pieces(image, piece_height, pieces_wide, pieces_tall, directory):
    jigsaw_obj = {"pieces": [], "pieces_wide": pieces_wide, "pieces_tall": pieces_tall}
    nobble = Image.open("nobbles/nobble1.jpg")
    nobble = nobble.resize((int(piece_height/2), piece_height))
    nobble_np = np.array(nobble)
    nobble_np_vert = np.rot90(nobble_np)
    nobble_np_backwards = np.rot90(nobble_np_vert)
    nobble_np_vert_backwards = np.rot90(nobble_np_backwards)
    nobble_np = nobble_to_2d(nobble_np)
    nobble_np_vert = nobble_to_2d(nobble_np_vert)
    nobble_np_backwards = nobble_to_2d(nobble_np_backwards)
    nobble_np_vert_backwards = nobble_to_2d(nobble_np_vert_backwards)
    pieces_np = np.zeros((pieces_tall, pieces_wide, piece_height * 2, piece_height * 2, 4), dtype=np.uint8)
    image_np = np.array(image)
    direction_of_nobbles = [[random.random() <= 0.5 for x in range(pieces_wide + 1)] for y in range(pieces_tall)]
    for y in range(image_np.shape[0]):
        for x in range(image_np.shape[1]): # 100:150, 250:300, 400:450
            pos_in_piece_x = int((x % (piece_height * (3/2))) + piece_height/2)
            pos_in_piece_y = int((y % (piece_height * (3/2))) + piece_height/2)
            in_horizontal_neutral_zone = pos_in_piece_x - piece_height * (3/2) >= 0
            in_vertical_neutral_zone = pos_in_piece_y - piece_height * (3/2)>= 0
            piece_left = x // 150
            piece_up = y // 150

            if in_horizontal_neutral_zone and in_vertical_neutral_zone:
                if piece_left + 1 >= pieces_np.shape[1] or piece_up + 1 >= pieces_np.shape[0]:
                    continue
                left = ((x % (piece_height * (3/2))) - piece_height) + 1 <= piece_height / 4
                up = ((y % (piece_height * (3/2))) - piece_height) + 1 <= piece_height / 4
                pos_in_right_x = int((piece_height/2) - (2*piece_height - pos_in_piece_x))
                pos_in_down_y = int((piece_height/2) - (2*piece_height - pos_in_piece_y))
                pieces_np[piece_up, piece_left, pos_in_piece_y, pos_in_piece_x, :3] = image_np[y,x]
                pieces_np[piece_up, piece_left + 1, pos_in_piece_y, pos_in_right_x, :3] = image_np[y, x]
                pieces_np[piece_up + 1, piece_left, pos_in_down_y, pos_in_piece_x, :3] = image_np[y, x]
                pieces_np[piece_up + 1, piece_left + 1, pos_in_down_y, pos_in_right_x, :3] = image_np[y, x]
                if left and up:
                    #top left
                    pieces_np[piece_up, piece_left, pos_in_piece_y, pos_in_piece_x, 3] = 255
                    #top right
                    pieces_np[piece_up, piece_left + 1, pos_in_piece_y, pos_in_right_x, 3] = 0
                    #bottom left
                    pieces_np[piece_up + 1, piece_left, pos_in_down_y, pos_in_piece_x, 3] = 0
                    #bottom right
                    pieces_np[piece_up + 1, piece_left + 1, pos_in_down_y, pos_in_right_x, 3] = 0

                elif left:
                    #top left
                    pieces_np[piece_up, piece_left, pos_in_piece_y, pos_in_piece_x, 3] = 0
                    #top right
                    pieces_np[piece_up, piece_left + 1, pos_in_piece_y, pos_in_right_x, 3] = 0
                    #bottom left
                    pieces_np[piece_up + 1, piece_left, pos_in_down_y, pos_in_piece_x, 3] = 255
                    #bottom right
                    pieces_np[piece_up + 1, piece_left + 1, pos_in_down_y, pos_in_right_x, 3] = 0

                elif up:
                    #top left
                    pieces_np[piece_up, piece_left, pos_in_piece_y, pos_in_piece_x, 3] = 0
                    #top right
                    pieces_np[piece_up, piece_left + 1, pos_in_piece_y, pos_in_right_x, 3] = 255
                    #bottom left
                    pieces_np[piece_up + 1, piece_left, pos_in_down_y, pos_in_piece_x, 3] = 0
                    #bottom right
                    pieces_np[piece_up + 1, piece_left + 1, pos_in_down_y, pos_in_right_x, 3] = 0

                else:
                    #top left
                    pieces_np[piece_up, piece_left, pos_in_piece_y, pos_in_piece_x, 3] = 0
                    #top right
                    pieces_np[piece_up, piece_left + 1, pos_in_piece_y, pos_in_right_x, 3] = 0
                    #bottom left
                    pieces_np[piece_up + 1, piece_left, pos_in_down_y, pos_in_piece_x, 3] = 0
                    #bottom right
                    pieces_np[piece_up + 1, piece_left + 1, pos_in_down_y, pos_in_right_x, 3] = 255
            elif in_horizontal_neutral_zone:
                if piece_up >= pieces_np.shape[0] or piece_left >= pieces_np.shape[1] - 1:
                    continue
                if direction_of_nobbles[piece_up][piece_left]:
                    tmp = nobble_np
                else:
                    tmp = nobble_np_backwards
                pos_in_right_x = int((piece_height/2) - (2*piece_height - pos_in_piece_x))
                pieces_np[piece_up, piece_left, pos_in_piece_y, pos_in_piece_x, :3] = image_np[y,x]
                pieces_np[piece_up, piece_left + 1, pos_in_piece_y, pos_in_right_x, :3] = image_np[y, x]
                if tmp[pos_in_piece_y-50, pos_in_right_x] < 100:
                    pieces_np[piece_up, piece_left, pos_in_piece_y, pos_in_piece_x, 3] = 255
                    pieces_np[piece_up, piece_left + 1, pos_in_piece_y, pos_in_right_x, 3] = 0
                else:
                    pieces_np[piece_up, piece_left + 1, pos_in_piece_y, pos_in_right_x, 3] = 255
                    pieces_np[piece_up, piece_left, pos_in_piece_y, pos_in_piece_x, 3] = 0
            elif in_vertical_neutral_zone:
                if piece_up >= pieces_np.shape[0]-1 or piece_left >= pieces_np.shape[1]:
                    continue
                if direction_of_nobbles[piece_up][piece_left]:
                    tmp = nobble_np_vert
                else:
                    tmp = nobble_np_vert_backwards
                pos_in_down_y = int((piece_height/2) - (2*piece_height - pos_in_piece_y))
                pieces_np[piece_up, piece_left, pos_in_piece_y, pos_in_piece_x, :3] = image_np[y,x]
                pieces_np[piece_up+1, piece_left, pos_in_down_y, pos_in_piece_x, :3] = image_np[y, x]
                if tmp[pos_in_down_y, pos_in_piece_x - 50] < 100:
                    pieces_np[piece_up, piece_left, pos_in_piece_y, pos_in_piece_x, 3]= 255
                    pieces_np[piece_up+1, piece_left, pos_in_down_y, pos_in_piece_x, 3] = 0
                else:
                    pieces_np[piece_up+1, piece_left, pos_in_down_y, pos_in_piece_x, 3] = 255
                    pieces_np[piece_up, piece_left, pos_in_piece_y, pos_in_piece_x, 3] = 0
            else:
                pieces_np[piece_up, piece_left, pos_in_piece_y, pos_in_piece_x, :3] = image_np[y,x]
                pieces_np[piece_up, piece_left, pos_in_piece_y, pos_in_piece_x, 3] = 255
    #piece = Image.fromarray(pieces_np[-2, 2], "RGBA")
    #tmp_image.save("piece.png")

    print("reshaping")
    print(pieces_np.shape)
    pieces_to_return = []
    index = 0
    os.mkdir("premade/" + directory + "/" + str(pieces_wide) + "/")
    for y in range(pieces_np.shape[0]):
        for x in range(pieces_np.shape[1]):
            tmp = Image.fromarray(pieces_np[y,x], "RGBA")
            tmp.save("premade/" + directory + "/" + str(pieces_wide) + "/" + str(index) + ".png")
            index += 1


def check_url(url):
    saved_urls = open("premade/saved_urls.csv", "r")
    directory = None
    for line in saved_urls:
        line = line.split("\n")[0]
        tmp = line.split(" ")
        if tmp[0] == url:
            directory = tmp[1]
    saved_urls.close()
    return directory


def check_size(directory, pieces_wide):
    return str(pieces_wide) in os.listdir("premade/" + directory + "/")

def make_directory(url, image):
    saved_urls = open("premade/saved_urls.csv", "r")
    max_directory = -1
    for line in saved_urls:
        tmp = line.split(" ")
        if int(tmp[1]) > max_directory:
            max_directory = int(tmp[1])
    max_directory += 1
    saved_urls.close()
    saved_urls = open("premade/saved_urls.csv", "a")
    saved_urls.write("\n" + url + " " + str(max_directory))
    os.mkdir("premade/" + str(max_directory))
    image.save("premade/" + str(max_directory) + "/presaved_image.jpg")
    saved_urls.close()
    return str(max_directory)


def get_game(game_id, player_id, player_name):
    #gs_file = open("gamestates.json")
    #gs_string = ""
    #for line in gs_file:
    #    gs_string += line
    #gs_obj = json.loads(gs_string)
    #gs_file.close()
    global gs_obj
    for game in gs_obj["games"]:
        if game_id == game["game_id"]:
            tmp = None
            for player in game["players"]:
                if player_id == player["player_id"]:
                    tmp = player
            if tmp is None:
                game["players"].append({
                    "name": player_name,
                    "score": 0,
                    "player_id": player_id
                })
                gs_string = repr(gs_obj)
                gs_file = open("gamestates.json")
                gs_file.write(gs_string)
                gs_file.close()
            return game
    return False


def add_game(game_in):
    #gs_file = open("gamestates.json")
    #gs_string = ""
    #for line in gs_file:
    #    gs_string += line
    #gs_file.close()
    #gs_obj = json.loads(gs_string)
    global gs_obj
    existing_game_ids = []
    for game in gs_obj["games"]:
        existing_game_ids.append(game["game_id"])
    new_game_id = random.randint(0, 100000000)
    while new_game_id in existing_game_ids:
        new_game_id = random.randint(0, 10000000)
    game_in["game_id"] = new_game_id
    gs_obj["games"].append(game_in)
    return game_in


@app.route("/jigsaw_gamestate/", methods=["POST"])
def gamestate_changer():
    content = request.json
    #gs_file = open("gamestates.json")
    #gs_string = ""
    #for line in gs_file:
    #    gs_string += line
    #gs_file.close()
    #gs_obj = json.loads(gs_string)
    print(content)
    global gs_obj
    tmp = gs_obj["games"][0]
    for game in gs_obj["games"]:
        if content["game_id"] == game["game_id"]:
            for piece in game["pieces"]:
                if piece["focussed_by"] == content["player_id"]:
                    piece["focussed_by"] = -1
            if content["focussed"] != -1:
                if game["pieces"][content["focussed"]]["focussed_by"] == -1:
                    game["pieces"][content["focussed"]]["x"] = content["new_coords"]["x"]
                    game["pieces"][content["focussed"]]["y"] = content["new_coords"]["y"]
                    game["pieces"][content["focussed"]]["focussed_by"] = content["player_id"]
                    game["pieces"][content["focussed"]]["last_focus"] = time.time()
            tmp = game
            break
    return tmp



@app.route("/piece_retriever/<directory>/<pieces_wide>/<piece_id>/", methods=["GET"])
def piece_retriever(directory, pieces_wide, piece_id):
    image_id = os.listdir("premade/" + directory + "/" + pieces_wide + "/")[int(piece_id)]
    return send_file("premade/" + directory + "/" + pieces_wide + "/" + image_id, mimetype="image/png")




@app.route("/jigsaw/", methods=["POST", "GET"])
def jigsaw_maker():
    if request.method == "GET":
        return "test working"
    #flickr = flickrapi.FlickrAPI(API_KEY, SECRET, format="parsed-json")
    content = request.json
    print(content)
    url = content["url"]
    pieces_wide = content["pieces_wide"]
    directory = check_url(url)
    if directory is None:
        im = Image.open(requests.get(url, stream=True).raw)
        directory = make_directory(url, im)
    else:
        im = Image.open("premade/" + directory + "/presaved_image.jpg")
    width, height = im.size
    pieces_tall = int(pieces_wide * (height / width))
    if not check_size(directory, pieces_wide):
        im = Image.open("premade/" + directory + "/presaved_image.jpg")
        im1 = im.resize((pieces_wide * 150, pieces_tall * 150))
        split_into_pieces(im1, 100, pieces_wide, pieces_tall, directory)
    if content["new_game"]:
        game = {
            "url": content["url"],
            "directory": directory,
            "pieces_wide": content["pieces_wide"],
            "total_pieces": pieces_wide * pieces_tall,
            "pieces": [
                {
                    "x": random.randint(-100, 100),
                    "y": random.randint(-100, 100),
                    "key": i,
                    "focussed_by": -1,
                    "last_focus": -1
                } for i in range(pieces_wide * pieces_tall)
            ],
            "players": [
                {
                    "name": content["name"],
                    "score": 0,
                    "player_id": content["player_id"]
                }
            ]
        }
        game = add_game(game)
        print(game)
        return game
    else:
        return get_game(content["game_id"], content["player_id"], content["name"])




def test_maker(port, port_return):
    print("testing")
    UDP_IP_ADDRESS = "127.0.0.1"
    UDP_PORT_NO = port
    clientSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    UDP_IP_ADDRESS_return = "127.0.0.1"
    UDP_PORT_NO_return = port_return
    serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSock.bind((UDP_IP_ADDRESS_return, UDP_PORT_NO_return))
    for i in range(200):
        json_data = {"url": "https://live.staticflickr.com/5496/14375837173_1929d5bccb_o_d.jpg", "pieces_wide": 20,
                     "pieces_tall": 10, "port_return": port_return, "piece_id": i}
        Message = json.dumps(json_data)
        clientSock.sendto(Message.encode("utf-8"), (UDP_IP_ADDRESS, UDP_PORT_NO))
        data, addr = serverSock.recvfrom(40128)
        im = Image.frombytes("RGBA", (200,200), data)
        im.show()


def test_maker_post():
    print("in test")
    response = {}
    for i in range(200):
        json_data = {"url": "https://live.staticflickr.com/5496/14375837173_1929d5bccb_o_d.jpg", "pieces_wide": 20,
                     "piece_id": i, "new_game": True, "game_id": -1, "player_id": 6969, "name": "beenis"}
        print("sending")
        if i == 0:
            response = requests.post("http://127.0.0.1:5000/jigsaw/", json=json_data, stream=True).json()
            print(response)
        else:
            print("http://127.0.0.1:5000/piece_retriever/" + response["directory"] + "/" +
                        str(response["pieces_wide"]) + "/" + str(i) + "/")
            img = Image.open(requests.get("http://127.0.0.1:5000/piece_retriever/" + response["directory"] + "/" +
                        str(response["pieces_wide"]) + "/" + str(i) + "/").raw)


def obj_saver():
    global gs_obj
    while True:
        time.sleep(10)
        gs_string = json.dumps(gs_obj)
        gs_file = open("gamestates.json", "w")
        gs_file.write(gs_string)
        gs_file.truncate()
        gs_file.close()



if __name__ == "__main__":
    process_count = 3
    #cluster = LocalCluster(n_workers=process_count, threads_per_worker=1, memory_limit=20e9)
    #client = Client(cluster)
    gs_file = open("gamestates.json")
    gs_string = ""
    for line in gs_file:
        gs_string += line
    gs_file.close()
    gs_obj = json.loads(gs_string)
    p = Process(target = obj_saver)
    p.start()
#    client.run(jigsaw_out)
#    port_return = 45679
    app.run(host="0.0.0.0", port=5000, debug=False)
