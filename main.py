import chess
import praw
import json
import random
import os
import sys
import requests as req
import time
from bs4 import BeautifulSoup

class Opening:
    def __init__(self):
        self.name = ""
        self.line = ""
        self.wiki = ""
        self.lichess = ""
        self.text = ""
        self.filename = ""

class Historical_Game:
    def __init__(self):
        self.players = ''
        self.year = ''
        self.moves = ''
        self.result = ''
        self.opening = ''
        self.url = ''
        self.event = ''

def get_filenames():

    result = [os.path.join(dp, f) for dp, dn, filenames in os.walk("chessopeningtheory") for f in filenames]
    new_result = []
    for item in result:
        if "index.html" in item:
            new_result.append(item)
   # return ["chessopeningtheory\\1._d4\\1...d5\\2._Bf4\\index.html"]
    return new_result

def get_text(file):
    firstheadline = ""
    headline = "First"
    started = False
    started_idx = i
    ff = open(file, 'r', encoding='utf-8')
    lines = ff.readlines()
    ff.close()
    fulltext = ""
    lastline = ""
    for line in lines:
        textline = ''
        try:
            soup = BeautifulSoup(line)
            textline = soup.get_text()
        except:
            textline = line
        if "When contributing to this" in line: continue
        if "Theory_table" in headline or "Theory_Table" in headline or "Statistics" in headline or "References" in headline: break
        if "</div></div></div>" in line:
            started = True
            started_idx = i
       ##print("::::::", line)
        if "span class=\"mw-headline\"" in line:
            print(":::", line)
            headline = line.split("id=\"")[1].split("\"")[0].replace("_"," ")
            if "Theory_table" in headline or "Theory_Table" in headline or "Statistics" in headline or "References" in headline: break
            fulltext += "\n\n**" + headline.replace("\n","").replace("\r","") + "**" + "\n\n"
            started_idx = i
            if firstheadline == "":
                firstheadline = headline
                print(headline)
        if not started: continue
        else:
            if ("<p><br />" in lastline and headline == "First") or headline != "":
                if i - started_idx < 100:
                    if "Contents" not in textline:
                        if textline.split(" ")[0].replace(".","").isnumeric(): continue
                        fulltext += textline.replace("\n\n","")
        lastline = line
    return fulltext

def get_opening_info(opening_line):
    ff = open('eco_codes.txt', 'r')
    lines = ff.readlines()
    ff.close()
    search_line = opening_line.replace(".","").strip()
    for line in lines:
        line = line.replace("\n","").strip()
        eco_code = line.split("|")[0]
        opening_name = line.split("|")[1]
        found_line = line.split("|")[2].strip()
        if found_line == search_line:
            return line

def get_historical_games(eco_code):
    if eco_code == '': return None
    resp = req.get("https://chessgames.com/perl/chessopening?eco=" + eco_code, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    #print(resp.text)
    lines = resp.text.split("\n")
    current_game = Historical_Game()
    count = 0
    games_list = []
    for line in lines:
        if "<td><font face='verdana,arial,helvetica' size=-1>" in line:
            if "<td valign=TOP NOWRAP>" not in line:
                #print(line)
                players = line.split("<a href=\"/perl/chessgame?gid=")[1].split(">")[1].split("<")[0]
                url = line.split("<a href=\"")[1].split("\"")[0]
                #.split(">")[1].split("<")[0]
                current_game.players = players
                #print(players)
                current_game.players = players
                current_game.url = url
                #print(line, url)
            else:
                result = line.split("<td align=RIGHT NOWRAP><font face='verdana,arial,helvetica' size=-1>")[1].split("<")[0]
                moves = line.split("<td align=RIGHT><font face='verdana,arial,helvetica' size=-1>")[1].split("<")[0]
                year = line.split("<td align=RIGHT><font face='verdana,arial,helvetica' size=-1>")[2].split("<")[0]
                #event = line.split("<td align=RIGHT><font face='verdana,arial,helvetica' size=-1>")[3].split("<")[0]
                #moves = 0
      #          print(line)
                event = ''
                if "/perl/chess.pl?" in line:
                    event = line.split("<font size=-2><a href=\"/perl/chess.pl?")[1].split(">")[1].split("<")[0]
                else:
                    event = line.split("<font size=-2>")[1].split("<")[0]
                count += 1
                result = result.replace("&#189;", "1/2")
                current_game.result = result
                current_game.moves = moves
                current_game.year = year
                current_game.event = event
                games_list.append(current_game)
                current_game = Historical_Game()
                #print(current_game.url, result, moves, year, event)
        if count >= 10:
            break
    return games_list
    pass

#authenticate
credentials = 'client_secrets.json'
with open(credentials) as f:
    creds = json.load(f)

reddit = praw.Reddit(client_id=creds['client_id'],
                     client_secret=creds['client_secret'],
                     user_agent=creds['user_agent'],
                     redirect_uri=creds['redirect_uri'],
                     refresh_token=creds['refresh_token'])
board = chess.Board()
already_posted = []
ff = open('posted.txt','r')
lines = ff.readlines()
ff.close()
for line in lines:
    already_posted.append(line.replace("\n",""))

i = 0
valid_files = []
valid_openings = []
filenames = get_filenames()
# get valid files to choose from
for file in filenames:
    i += 1
    if i == 1: continue
    if file in already_posted: continue
    print(i)
    fulltext = get_text(file)
    filename = file.replace("index.html", "").replace("chessopeningtheory\\", "")
    wiki_link = filename.replace("\\", "/")
    if wiki_link[len(wiki_link) - 1] == "/":
        wiki_link = wiki_link[:len(wiki_link) - 1]
        wiki_link = "wiki/Chess_Opening_Theory/" + wiki_link
    filename = filename.replace("_", " ")
    opening_line = ""
    for move in filename.split("\\"):
        print(move)
        if "..." in move:
            move = move.split("...")[1]
        opening_line += move + " "
    is_valid = False
    opening_name = None
    for line in fulltext.split("\n"):
        if "**" in line and "theory" not in line.lower():
            if opening_name is None:
                opening_name = line.replace("**","")
                opening_name = opening_name.replace("_"," ")
                if "- " in opening_name and opening_name[0].isnumeric():
                    opening_name = opening_name.split("- ")[1]
            continue
        if "Moves:" in line: continue
        if len(line) < 1: continue
        is_valid = True
    print(is_valid)
    print("wiki link", wiki_link)
    print("move list", opening_line)
    print("opening name", opening_name)
    print("---")
    print(fulltext)
    if fulltext == "" or not is_valid:
        print(file)
        #break
    print("---")
    if is_valid:
        valid_files.append(file)
        opening = Opening()
        opening.wiki = "https://en.wikibooks.org/" + wiki_link
        opening.line = opening_line
        if opening.name != None: opening.name = opening.name.replace("'", "")
        opening.name = opening_name
        opening.text = fulltext
        opening.filename = file
        #opening_line = "1. b4 e5 2. Bb2 Bxb4"
        board = chess.Board()
        for move in opening_line.split(" "):
            if "." in move: continue
            if move == "": continue
            board.push_san(move)
        fen = board.fen()
        #opening.lichess = "https://lichess.org/analysis/" + fen.replace(" ", "_")
        opening.lichess = "https://lichess.org/analysis/pgn/" + opening_line.replace(" ","+")
        valid_openings.append(opening)
    if i > 60000: break

while True:
    opening = random.choice(valid_openings)
    #opening = valid_openings[35]
    opening_line = opening.line
    print(opening.line)
    opening_info = get_opening_info(opening.line)
    length = len(opening.line.split(" "))
    exact_match = True
    while opening_info == None and length > 0:
        print("Failed to find ECO code")
        exact_match = False
        opening_line_split = opening_line.split(" ")
        opening_line_split.pop()
        new_opening_line = ''
        i = 0
        for item in opening_line_split:
            new_opening_line += item
            if i == len(opening_line_split) - 1:
                break
            new_opening_line += " "
            i+=1
        opening_line = new_opening_line
        print(opening_line)
        opening_info = get_opening_info(opening_line)
        length = len(opening_line.split(" "))
    eco_code = '0'
    eco_name = ''
    eco_line = ''
    historical_game_text = 'No historical games could be found for this line.'
    if opening_info == None:
        print("Unable to find parent opening")
    else:
        eco_code = opening_info.split("|")[0]
        eco_name = opening_info.split("|")[1]
        eco_line = opening_info.split("|")[2]
        historical_games = get_historical_games(eco_code)
        #print(historical_games)
        historical_game_text = ''
        historical_game_text += '**Historical games for ' + eco_name + ' (' + eco_code + ')**\n\n'
        if not exact_match: historical_game_text += '(Unable to find exact match; using parent opening: ' + eco_line + ')\n\n'
        historical_game_text += "Game | Result | Moves | Year | Event\n"
        historical_game_text += ":--|:--|:--|:--|:--\n"
        for game in historical_games:
            historical_game_text += "[" + game.players + "](https://www.chessgames.com" + game.url + ")" + " | " + game.result + " | " + game.moves + " | " + game.year + " | " + game.event + "\n"

    subr = 'chessopeningtheory'  # Choose your subreddit

    subreddit = reddit.subreddit(subr)  # Initialize the subreddit to a variable

    title = opening.line
    name = opening.name
    if name == "" or name == None: name = "Unknown"
    name = name.replace(".27","'").replace(".2C",":")
    if opening.name != "" and opening.name != None: title += " (" + name+ ")"
    opening.text = opening.text.replace(".27","'").replace(".2C",":")
    selftext = "Opening line: " + opening.line + "\n\n"
    selftext += "Opening name: " + name + "\n\n"
    selftext += "Lichess board: " + opening.lichess + "\n\n"
    selftext += "Wikibooks page: " + opening.wiki + "\n\n"
    selftext += "---\n\n"
    propertext = ''
    for line in opening.text.split("\n"):
        if "theory table" in line.lower(): break
        if "footnotes" in line.lower(): break
        if "newpp" in line.lower(): break
        if len(line.replace("\n","")) == 1: break
        propertext += line + "\n"
    propertext = propertext.replace("[edit]","")
    is_empty = True
    actual_len = 0
    for line in propertext.split("\n"):
        if "parent:" in line.lower(): continue
        if "eco code:" in line.lower(): continue
        if "notation" in line.lower(): continue
        if "moves:" in line.lower(): continue
        if "**" in line.lower(): continue
        if "wikipedia" in line.lower(): continue
        actual_len += len(line)
        is_empty = False
    if actual_len < 100: is_empty = True
    if is_empty:
        selftext = ""
        continue
    #is_valid = True
    #for line in propertext.split("\n"):
        #if "**" in line: is_valid = False
    #if not is_valid:
     #   selftext = ""
      #  continue
    if len(propertext) < 5: continue
    selftext += propertext
    selftext += "\n\n---\n\n"
    selftext += historical_game_text
    result = subreddit.submit(title, selftext=selftext)
    print(result)
    ff = open('posted.txt', 'a', encoding='utf-8')
    ff.write(opening.filename + "\n")
    ff.close()
    new_valid_openings = []
    for valid_opening in valid_openings:
        if valid_opening.line == opening.line:
            continue
        new_valid_openings.append(valid_opening)
    valid_openings = new_valid_openings
    time.sleep(60*60*8)