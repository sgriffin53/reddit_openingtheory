import chess
import praw
import json
import random
import os
import sys
import requests as req
import time
import lichess
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
        self.opening_name = ''
        self.eco = ''

class Opening_Count():
    def __init__(self):
        self.count = 0
        self.opening = ""

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
        if "Theory_table" in headline or "Theory_Table" in headline or "theory table" in headline.lower() or "Statistics" in headline or "References" in headline: break
        if "</div></div></div>" in line or "<h1><span id=" in line:
            started = True
            started_idx = i
        if "span class=\"mw-headline\"" in line:
            headline = line.split("id=\"")[1].split("\"")[0].replace("_"," ")
            if "Theory_table" in headline or "Theory_Table" in headline or "Statistics" in headline or "References" in headline: break
            fulltext += "\n\n**" + headline.replace("\n","").replace("\r","") + "**" + "\n\n"
            started_idx = i
            if firstheadline == "":
                firstheadline = headline
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

def get_historical_games(fen):
    info = get_opening_info_lichess(fen)
    top_games = info['topGames']
    current_game = Historical_Game()
    games_list = []
    count = 0
    for game in top_games:
        current_game.url = "https://lichess.org/" + game['id']
        winner = game['winner']
        if winner == 'white':
            result = "1-0"
        elif winner == 'black':
            result = "0-1"
        else:
            result = "1/2-1/2"
        current_game.result = result
        current_game.players = game['white']['name'] + " (" + str(game['white']['rating']) + ") vs " + game['black']['name'] + " (" + str(game['black']['rating']) + ")"
        current_game.year = str(game['year'])
        if 'opening' in game:
            current_game.opening_name = str(game['opening']['name'])
            current_game.eco = str(game['opening']['eco'])
        games_list.append(current_game)
        current_game = Historical_Game()
        count += 1
        if count == 10: break
    return games_list

#def get_historical_games(eco_code):
#    if eco_code == '': return None
    '''
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
    '''
def get_opening_info_lichess(fen):
    # master games
    try:
        url = "https://explorer.lichess.ovh/masters?fen=" + fen
        resp = req.get(url)
        json_data = json.loads(resp.text)
        top_games = json_data['topGames']
        return json_data
    except Exception as e:
        print(e, resp.status_code)
        return None
    pass

def get_opening_info_lichess_all(fen):
    try:
        url = "https://explorer.lichess.ovh/lichess?variant=standard&fen=" + fen
        resp = req.get(url)
        json_data = json.loads(resp.text)
        top_games = json_data['topGames']
        return json_data
    except:
        return None
    pass


def get_weekly_openings(valid_openings):
    sublines = {}
    for opening in valid_openings:
        filename = opening.filename.replace("\index.html","")
        opening_line = filename.replace("chessopeningtheory\\", "")
        opening_line_split = opening_line.split("\\")
        index = len(opening_line_split)
        lastline = opening_line
        while index > 1:
            index -= 1
            move = opening_line_split[index]
            new_opening_line = ''
            for item in opening_line.split("\\"):
                if item == move: continue
                new_opening_line += item + "\\"
            opening_line = new_opening_line[:len(new_opening_line) - 1]
            if opening_line not in sublines:
                sublines[opening_line] = []
            #opening_line = opening_line.replace("\\\\","\\")
            #lastline = lastline.replace("\\\\","\\")
            sublines[opening_line].append(lastline)
            lastline = opening_line
    for key in sublines.keys():
        length = len(sublines[key])
       # if "2._f4" in key: print(":::", key, length)
        if length > 14:
            #print("yes!!")
            board = chess.Board()
            for move in key.replace("_", "\\").split("\\"):
                if "..." in move: move = move.split("...")[1]
                if "." in move: continue
                if move == "": continue
                board.push_san(move)
            fen = board.fen()
            info = get_opening_info_lichess_all(fen)
            if info is None: continue
            total_games = int(info['white']) + int(info['draws']) + int(info['black'])
            if total_games < 10000: continue
            #if length > 150: continue
            if key.count("\\") > 4: continue
            #print(key, length, total_games)

def new_weekly_opening(reddit, valid_openings):
    ff = open('weekly_candidates.txt','r')
    lines = ff.readlines()
    ff.close()
    chosen_index = random.randint(0,len(lines) - 1)
    chosen_opening = lines[chosen_index]
    chosen_opening = chosen_opening.split(" ")[0]
    dir = 'chessopeningtheory\\' + chosen_opening
    # get 21 most played openings
    result = [os.path.join(dp, f) for dp, dn, filenames in os.walk(dir) for f in filenames]
    new_result = []
    for item in result:
        if "index.html" in item:
            new_result.append(item)
    entries = []
    for filename in new_result:
        opening_line = filename.replace('chessopeningtheory','').replace('\\index.html','')
        board = chess.Board()
        for move in opening_line.replace("_", "\\").split("\\"):
            if "..." in move: move = move.split("...")[1]
            if "." in move: continue
            if move == "": continue
            board.push_san(move)
        fen = board.fen()
        #print(fen)
        info = get_opening_info_lichess_all(fen)
        if info is None: continue
        total_moves = int(info['white']) + int(info['draws']) + int(info['black'])
        #print(total_moves)
        entry = Opening_Count()
        entry.count = total_moves
        entry.opening = opening_line
        entries.append(entry)
        time.sleep(0.25)
    entries.sort(key=lambda entry: entry.count, reverse=True)
    new_entries = []
    i = 0
    top_opening = ''
    for entry in entries:
        #print("entry.opening", ":", chosen_opening)
        if entry.opening == "\\" + chosen_opening:
            i += 1
            continue
        print(entry.opening, entry.count)
        new_entries.append(entry)
        i += 1
        if len(new_entries) >= 21: continue
    ff = open('weekly_to_post.txt','w')
    i = 0
    for entry in new_entries:
        ff.write(entry.opening + "\n")
        i += 1
        if i > 21: break

    ff.close()
    ff = open('current_weekly.txt','w')
    ff.write(chosen_opening + "\n")
    ff.close()
    # post main weekly thread
    result = post_thread(reddit, chosen_opening, valid_openings, "weekly_main")
    if result is None: print("Unable to post weekly main thread")
    ff = open('weekly_candidates.txt', 'w')
    i = 0
    for line in lines:
        line = line.replace("\n","")
        if i == chosen_index:
            i += 1
            continue
        ff.write(line + "\n")
        i += 1
    ff.close()
    # post first weekly thread
    post_weekly_thread(reddit, valid_openings)
    #todo remove chosen opening from txt file

def post_weekly_thread(reddit, valid_openings):
    ff = open('weekly_to_post.txt','r')
    lines = ff.readlines()
    ff.close()
    if len(lines) <= 0 or len(lines[0]) < 2:
        print("Weekly theme finished. Posting new weekly opening.")
        new_weekly_opening(reddit, valid_openings)
        return None
    opening = lines[0].replace("\n","")
    post_thread(reddit, opening, valid_openings, "weekly")
    i = 0
    ff = open('weekly_to_post.txt','w')
    for line in lines:
        line = line.replace("\n","")
        if i == 0:
            i += 1
            continue
        ff.write(line + "\n")
        i += 1
    ff.close()
    if len(lines) <= 1:
        print("Weekly theme finished. Posting new weekly opening.")
        new_weekly_opening(reddit, valid_openings)
    pass

def post_thread(reddit, opening_line, valid_openings, weekly):
    if weekly != "weekly_main" and weekly != "weekly" and weekly != "random": return None
    new_opening_line = ""
    opening_line = opening_line.replace("_", " ")
    for move in opening_line.split("\\"):
        if "..." in move:
            move = move.split("...")[1]
        new_opening_line += move + " "
    opening_line = new_opening_line.strip()
    current_opening = None
    found = False
    for opening in valid_openings:
        opening.line = opening.line.strip()
        #if "1. c4" in opening.line: print(opening.line, opening_line)
        if opening.line == opening_line:
            found = True
            current_opening = opening
            break
            #print("Found", opening.wiki)
    if found == False:
        print("Unable to find opening")
        return None
    info = get_opening_info(opening_line)
    # post the thread
    opening = current_opening
    name = opening.name
    if name == "" or name == None: name = "Unknown"
    name = name.replace(".27","'").replace(".2C",":")
    board = chess.Board()
    for move in opening.line.split(" "):
        if "." in move: continue
        if move == "": continue
        board.push_san(move)
    print(opening.line)
    fen = board.fen()
    historical_games = get_historical_games(fen)
    #print(historical_games)
    hist_display_name = ''
    hist_display_eco = ''
    if len(historical_games) > 0:
        hist_display_name = historical_games[0].opening_name
        hist_display_eco = ' (' + historical_games[0].eco + ')'
        if historical_games[0].eco == '': hist_display_eco = ''
    if hist_display_name == '':
        hist_display_name = name
    historical_game_text = ''
    historical_game_text += '**Historical games for ' + hist_display_name + hist_display_eco + '**\n\n'
   # if not exact_match: historical_game_text += '(Unable to find exact match; using parent opening: ' + eco_line + ')\n\n'
    historical_game_text += "Game | Result | Year \n"
    historical_game_text += ":--|:--|:--\n"
    for game in historical_games:
        historical_game_text += "[" + game.players + "](" + game.url + ")" + " | " + game.result + " | " + game.year + "\n"
    if len(historical_games) == 0:
        historical_game_text = 'No historical games could be found for this line.'
    subr = 'chessopeningtheory'  # Choose your subreddit

    subreddit = reddit.subreddit(subr)  # Initialize the subreddit to a variable

    title = opening.line
    if opening.name != "" and opening.name != None: title += " (" + name + ")"
    opening.text = opening.text.replace(".27","'").replace(".2C",":")
    opening.name = opening.name.replace(".27","'").replace(".2C",":")
    selftext = ''
    if weekly == "weekly_main":
        selftext += "**This week's opening is " + opening.line + " (" + name + ")**\n\n"
        selftext += "The bot will post the most popular lines for this opening throughout the week.\n\n"
        selftext += "---\n\n"
        title = "This week's opening: " + opening.line + " (" + name + ")"
    if weekly == "weekly":
        ff = open('current_weekly.txt','r')
        lines = ff.readlines()
        ff.close()
        new_root_line = ''
        root_line = lines[0]
        root_line = root_line.replace("_", " ")
        for move in root_line.split("\\"):
            print(move)
            if "..." in move:
                move = move.split("...")[1]
            new_root_line += move + " "
        root_line = new_root_line.strip()
        current_opening = None
        found = False
        root_opening = None
        for loop_opening in valid_openings:
            loop_opening.line = loop_opening.line.strip()
            # print(opening_line, opening.line)
            if loop_opening.line == root_line:
                found = True
                root_opening = loop_opening
                break
                # print("Found", opening.wiki)
        if found == None:
            print("Unable to find root ", root_line)
        selftext += "***This is part of this week's series on " + root_opening.name + " (" + root_opening.line + ")***\n\n---\n\n"
        opening.name = opening.name.replace(".27","'").replace(".2C",":")
        root_opening.name = root_opening.name.replace(".27","'").replace(".2C",":")
        title = "[Weekly: " + root_opening.line + " (" + root_opening.name + ")] " + opening.line + " (" + opening.name + ")"
    if weekly == "random":
        title = "[Random] " + opening.line + " (" + name + ")"
    selftext += "Opening line: " + opening.line + "\n\n"
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
        return None
    #is_valid = True
    #for line in propertext.split("\n"):
        #if "**" in line: is_valid = False
    #if not is_valid:
     #   selftext = ""
      #  continue
    if len(propertext) < 5: return None
    selftext += propertext
    selftext += "\n\n---\n\n"
    selftext += historical_game_text
    print(title)
    #print(selftext)
    #sys.exit()
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
    return valid_openings
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
all_openings = []
# get valid files to choose from
for file in filenames:
    i += 1
    if i == 1: continue
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
        if "parent:" in line.lower(): continue
        if "eco code:" in line.lower(): continue
        if "notation" in line.lower(): continue
        if "moves:" in line.lower(): continue
        if "**" in line.lower(): continue
        if "wikipedia" in line.lower(): continue
        is_valid = True
    if len(fulltext) < 200: is_valid = False
    print("---")
    if file in already_posted: is_valid = False
    if is_valid or True:
        if is_valid: valid_files.append(file)
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
        if is_valid: valid_openings.append(opening)
        all_openings.append(opening)
    if i > 100000: break

#weekly_openings = get_weekly_openings(valid_openings)
#print(weekly_openings)
#new_weekly_opening(reddit, valid_openings)
#result = post_thread(reddit, random.choice(valid_openings).line, valid_openings, "random")
#print(result)
#result = post_weekly_thread(reddit, valid_openings)

while True:
    print("Posting weekly thread")
    post_weekly_thread(reddit, all_openings)
    print("Posting random thread")
    valid_openings = post_thread(reddit, random.choice(valid_openings).line, valid_openings, "random")
    time.sleep(60*60*8)