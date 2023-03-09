import chess
import chess.svg
import chess.engine
import praw
import json
import random
import os
import sys
import requests as req
import time
import lichess
import base64
import re
from bs4 import BeautifulSoup
from wand.api import library
import wand.color
import wand.image

class Puzzle:
    def __init__(self):
        self.id = ''
        self.url = ''
        self.opening = ''

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
    started_idx = 0
    ff = open(file, 'r', encoding='utf-8')
    lines = ff.readlines()
    ff.close()
    fulltext = ""
    lastline = ""
    i = 0
    for line in lines:
        i += 1
        textline = ''
        try:
            soup = BeautifulSoup(line)
            textline = soup.get_text()
        except:
            textline = line
        if textline == '':
            textline = re.sub('<[^<]+?>', '', line)
        if "When contributing to this" in line: continue
        if "Theory_table" in headline or "Theory_Table" in headline or "theory table" in headline.lower() or "Statistics" in headline or "References" in headline: break
        if "</div></div></div>" in line or "<h1><span id=" in line or "<a class=\"mw-jump-link\" href=\"#searchInput\">Jump to search</a>" in line:
            started = True
            started_idx = i
        if "<div id=\"mw-content-text\" lang=\"en\" dir=\"ltr\"" in line and "<b>" in line:
            headline = line.split("<b>")[1].split("</b>")[0].replace("_"," ")
            if "Theory_table" in headline or "Theory_Table" in headline or "Statistics" in headline or "References" in headline: break
            if "Theory_table" in headline or "Theory_Table" in headline or "theory table" in headline.lower() or "Statistics" in headline or "References" in headline: break
            fulltext += "\n\n**" + headline.replace("\n","").replace("\r","") + "**" + "\n\n"
            started_idx = i
            if firstheadline == "":
                firstheadline = headline
        if "span class=\"mw-headline\"" in line:
            headline = line.split("id=\"")[1].split("\"")[0].replace("_"," ")
            if "Theory_table" in headline or "Theory_Table" in headline or "Statistics" in headline or "References" in headline: break
            if "Theory_table" in headline or "Theory_Table" in headline or "theory table" in headline.lower() or "Statistics" in headline or "References" in headline: break
            fulltext += "\n\n**" + headline.replace("\n","").replace("\r","") + "**" + "\n\n"
            started_idx = i
            if firstheadline == "":
                firstheadline = headline
        if not started: continue
        else:
            #if ("<p><br />" in lastline and headline == "First") or headline != "":
            if "<p>" in line or "</li>" in line or "<dd>" in line:
                if i - started_idx < 100:
                    if "Category:" in line:
                        break
                    if "Contents" not in textline:
                        #if textline.split(" ")[0].replace(".","").isnumeric(): continue
                        fulltext += textline.replace("\n\n","") + "\n"

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

def update_past_weekly_threads(reddit):
    subreddit_name = "chessopeningtheory"
    subreddit = reddit.subreddit(subreddit_name)
    opening_title = ''
    out_text = ''
    opening_id = 0
    weekly_main_submission = None
    for submission in subreddit.new(limit=100):
        title = submission.title
        id = submission.id
        pinned = submission.pinned
        if "This week's opening" in title and submission.stickied:
            age = time.time() - submission.created
            if age < 7 * 24 * 60 * 60:
                started = False
                for word in title.split(" "):
                    if word == "1.":
                        started = True
                    if started:
                        opening_title += word + " "
                opening_title = opening_title.strip()
                opening_id = id
                weekly_main_submission = submission
                break
    for submission in subreddit.new(limit=100):
        title = submission.title
        #id = submission.id
        #pinned = submission.pinned
        url = submission.url
        if opening_title in title and "This week" not in title:
            out_text += "[" + title + "](" + url + ")\n\n"
    if weekly_main_submission is not None:
        text = weekly_main_submission.selftext
        new_text = ''
        broken = False
        for line in text.split("\n\n"):
            if "This week's posts" in line:
                broken = True
                break
            new_text += line + "\n\n"
        if not broken: new_text += "---\n\n"
        new_text += "**This week's posts for " + opening_title + ":**\n\n"
        for line in out_text.split("\n\n"):
            new_text += line + "\n\n"
        result = weekly_main_submission.edit(body=new_text)
        print(result)

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

def get_analysis_info_lichess(fen):
    try:
        url = "https://lichess.org/api/cloud-eval?fen=" + fen
        #print(url)
        resp = req.get(url)
        #print(resp.text)
        json_data = json.loads(resp.text)
        #print(json_data)
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
    opening_counts = {}
    subline_counts = {}
    for key in sublines.keys():
        length = len(sublines[key])
        if length > 14:
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
            if key.count("\\") > 15: continue
            opening_name = ''
            ff = open('eco_codes.txt','r')
            lines = ff.readlines()
            ff.close()
            if 'opening' in info and info is not None and info['opening'] is not None:
                if 'name' in info['opening']:
                    opening_name = str(info['opening']['name'])
            opening_counts[key] = total_games
            subline_counts[key] = length
    sorted_openings = sorted(opening_counts.items(), key=lambda x: x[1], reverse=True)
    for opening in sorted_openings:
        line = opening[0]
        count = opening[1]
        opening_name = ''
        board = chess.Board()
        for move in line.replace("_", "\\").split("\\"):
            if "..." in move: move = move.split("...")[1]
            if "." in move: continue
            if move == "": continue
            board.push_san(move)
        fen = board.fen()
        info = get_opening_info_lichess_all(fen)
        time.sleep(.250)
        if info is not None:
            if 'opening' in info:
                if info['opening'] is not None:
                    if 'name' in info['opening']:
                        opening_name = str(info['opening']['name'])
        print(line, "(" + opening_name + ")", subline_counts[line], count)

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
    filename = "chessopeningtheory" + lines[0].replace("\n","") + "\\index.html"
    text = get_text(filename)
    count = 0
    is_valid = False
    for line in text.split("\n"):
        if "Moves:" in line: continue
        if len(line) < 1: continue
        if "parent:" in line.lower(): continue
        if "eco code:" in line.lower(): continue
        if "notation" in line.lower(): continue
        if "moves:" in line.lower(): continue
        if "**" in line.lower(): continue
        if "wikipedia" in line.lower(): continue
        count += len(line)
        is_valid = True
    if count < 120: is_valid = False
    if not is_valid:
        # remove 1st opening
        i = 0
        ff = open('weekly_to_post.txt', 'w')
        for line in lines:
            line = line.replace("\n", "")
            if i == 0:
                i += 1
                continue
            ff.write(line + "\n")
            i += 1
        ff.close()
        # try again
        post_weekly_thread(reddit, valid_openings)
        return
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

def opening_line_to_filename(opening_line):
    filename = ''
    i = 0
    for move in opening_line.split(" "):
        if move == '': continue
        if move[0].isnumeric():
            movenum = int(move.replace(".",""))
        else:
            i += 1
            if i % 2 == 0:
                filename += str(movenum) + "..." + move + "\\"
            elif i % 2 == 1:
                filename += str(movenum) + "._" + move + "\\"
    filename += "\\index.html"
    print(filename)
    return filename

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
    if name == "" or name == None or "mw-" in name or "<" in name: name = "Unknown"
    name = name.replace(".27","'").replace(".2C",":")
    board = chess.Board()
    for move in opening.line.split(" "):
        if "." in move: continue
        if move == "": continue
        board.push_san(move)
    print(opening.line)
    fen = board.fen()
    historical_games = get_historical_games(fen)
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
    if opening.name == None: opening.name = ""
    if opening.name != "" and opening.name != None: title += " (" + name + ")"
    opening.text = opening.text.replace(".27","'").replace(".2C",":")
    if opening.name != None: opening.name = opening.name.replace(".27","'").replace(".2C",":")
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
            if "..." in move:
                move = move.split("...")[1]
            new_root_line += move + " "
        root_line = new_root_line.strip()
        current_opening = None
        found = False
        root_opening = None
        for loop_opening in valid_openings:
            loop_opening.line = loop_opening.line.strip()
            if loop_opening.line == root_line:
                found = True
                root_opening = loop_opening
                break
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
    selftext += "Board image: " + get_imgur_link(opening.line) + "\n\n"
    selftext += "Lichess board: " + opening.lichess + "\n\n"
    selftext += "Wikibooks page: " + opening.wiki + "\n\n"
    selftext += "---\n\n"

    # winning chances #

    board = chess.Board()
    for move in opening.line.split(" "):
        if "." in move: continue
        if move == "": continue
        board.push_san(move)
    #print(opening.line)
    fen = board.fen()

    info = get_opening_info_lichess(fen)
    white_wins = str(info['white'])
    black_wins = str(info['black'])
    draws = str(info['draws'])
    tot_games = int(white_wins) + int(black_wins) + int(draws)
    white_percent = 0
    black_percent = 0
    draws_percent = 0
    if tot_games > 0:
        white_percent = round(int(white_wins) * 100 / int(tot_games),2)
        black_percent = round(int(black_wins) * 100 / int(tot_games), 2)
        draws_percent = round(int(draws) * 100 / int(tot_games), 2)
    selftext += "Winning percenatages:\n\n"
    selftext += "White: " + str(white_wins) + " (" + str(white_percent) + "%)\n\n"
    selftext += "Black: " + str(black_wins) + " (" + str(black_percent) + "%)\n\n"
    selftext += "Draws: " + str(draws) + " (" + str(draws_percent) + "%)\n\n"
    selftext += "---\n\n"
    print(opening.text)
    propertext = ''
    for line in opening.text.split("\n"):
        if line.lower().split(" ")[0].replace(".","").isnumeric(): continue
        if "theory table" in line.lower(): break
        if "footnotes" in line.lower(): break
        if "newpp" in line.lower(): break
        if len(line.replace("\n","")) == 1 and ((line.replace("\n","") >= 'a' and line.replace('\n','') <= 'z') or line.replace("\n","").isnumeric): break
        propertext += line + "\n"
    propertext = propertext.replace("[edit]","")
  #  print(propertext)
    is_empty = True
    actual_len = 0
    for line in propertext.split("\n"):
        if "parent:" in line.lower(): continue
        if "eco code:" in line.lower(): continue
        if "notation" in line.lower(): continue
        if "moves:" in line.lower(): continue
        if "**" in line.lower(): continue
        if "wikipedia" in line.lower(): continue
    #    print(line, actual_len)
        actual_len += len(line)
        is_empty = False
    print("Len", actual_len, is_empty, len(propertext))
    if actual_len < 100: is_empty = True
    if is_empty:
        selftext = ""
        return None
    if len(propertext) < 5: return None
    selftext += propertext
    selftext += "\n\n---\n\n"
    filename = opening_line_to_filename(opening.line)
    print(filename)
    responses = get_responses(filename)
    if responses is None:
        selftext += "No known responses found"
    else:
        selftext += responses
    selftext += "\n\n---\n\n"
    engine_info = lichess_engine_eval(filename)
    if engine_info is not None:
        depth = engine_info[0]
        score = engine_info[1]
        score /= 100
        sign = ''
        if score > 0: sign = '+'
        best_move = engine_info[2]
        pvline = engine_info[3]
        selftext += "**Engine Evaluation**\n\n"
        selftext += "Depth: " + str(depth) + "\n\n"
        selftext += "Score: " + sign + str(score) + "\n\n"
        selftext += "Best Move: " + str(best_move) + "\n\n"
        selftext += "PV Line: " + str(pvline) + "\n\n"
        selftext += "\n\n---\n\n"
    training_link = get_full_parent_lichess('chessopeningtheory\\' + filename)
    if training_link is not None:
        lichess_name = training_link[0]
        lichess_url = training_link[1]
        selftext += '**Puzzles based around ' + lichess_name + '**\n\n' + lichess_url
        selftext += "\n\n---\n\n"
    selftext += historical_game_text
    print(title)
    print(selftext)
    print("Posting thread:", title)
    result = subreddit.submit(title, selftext=selftext)
    print(result)
    ff = open('posted.txt', 'a', encoding='utf-8')
    ff.write(opening.filename + "\n")
    ff.close()
    if weekly == "weekly":
        update_past_weekly_threads(reddit)
    new_valid_openings = []
    for valid_opening in valid_openings:
        if valid_opening.line == opening.line:
            continue
        new_valid_openings.append(valid_opening)
    valid_openings = new_valid_openings
    return valid_openings
    pass

def get_imgur_link(opening):
    board = chess.Board()
    for move in opening.replace(" ", "\\").split("\\"):
        if "..." in move: move = move.split("...")[1]
        if "." in move: move = move.split(".")[1]
        if move == "": continue
        board.push_san(move)
    svg = chess.svg.board(board)
    with wand.image.Image() as image:
        with wand.color.Color('transparent') as background_color:
            library.MagickSetBackgroundColor(image.wand,
                                             background_color.resource)
        image.read(blob=svg.encode('utf-8'), format="svg")
        png_image = image.make_blob("png32")
    with open('image.png', "wb") as out:
        out.write(png_image)
    client_id = 'c8f4505d33d1b56'

    headers = {"Authorization": "Client-ID c8f4505d33d1b56"}

    api_key = 'eaaac6fe9b0830eb305093acc66ffa646c7711f3'

    url = "https://api.imgur.com/3/upload.json"

    j1 = req.post(
        url,
        headers=headers,
        data={
            'key': api_key,
            'image': base64.b64encode(open('image.png', 'rb').read()),
            'type': 'base64',
            'name': 'chess_opening.jpg',
            'title': '' + opening
        }
    )
    data = json.loads(j1.text)['data']
    return data['link']

def get_opening_name(filename):
    ff = open(filename, 'r', encoding='utf-8')
    lines = ff.readlines()
    ff.close()
    name = None
    for line in lines:
        #print(line)
        if "<div id=\"mw-content-text\" lang=\"en\" dir=\"ltr\"" in line and "<b>" in line:
            name = line.split("<b>")[1].split("</b>")[0].replace("_", " ")
        if "span class=\"mw-headline\"" in line:
            name = line.split("id=\"")[1].split("\"")[0].replace("_", " ")
        if name is not None:
            name = name.replace(".27", "'").replace(".2C", ":")
            return name
    return None

def get_first_two_sentences(filename):
    name = get_opening_name(filename)
    text = get_text(filename)
    realtext = ''
    for line in text.split("\n"):
        if line == '': continue
        if line[0].isnumeric() and line.split(".")[0].isnumeric(): continue
        if "**" in line: continue
        realtext += line + "\n"
    #print(realtext)
    realtext = realtext.replace("\n"," ")
    sentences = []
    sentence = ''
    #print(realtext)
    for word in realtext.split(" "):
        if sentence != '':
            sentence += ' '
        sentence += word
       # print(sentence)
        if len(word) >= 1 and word[-1] == ".":
            if word.replace(".","").isnumeric(): continue
            sentence += ""
            sentences.append(sentence)
            sentence = ""
            if len(sentences) == 2:
                fulltext = sentences[0] + " " + sentences[1]
                fulltext = fulltext.replace("\n","")
                #print(sentences)
                return fulltext
    if len(sentences) == 1:
        fulltext = sentences[0]
        fulltext = fulltext.replace("\n", "")
        # print(sentences)
        return fulltext
    return ''

def get_responses(filename):
    directory = filename.replace('\\index.html','')
    directory = directory.replace("", "\\")
    fulldir = "chessopeningtheory/" + directory
   # print(fulldir)
    current_slashes = directory.count("\\")
    result = [os.path.join(dp, f) for dp, dn, filenames in os.walk(fulldir) for f in filenames]
  #  print(result)
    new_result = []
    for item in result:
        #print(item)
        if "index.html" in item:
            slashes = item.replace("\\index.html","").count("\\")
            if slashes == current_slashes - 0: new_result.append(item)
    filenames = new_result
    if len(filenames) == 0: return None
    counts = {}
    for filename in filenames:
        opening_line = filename.replace("chessopeningtheory\\","").replace("\\index.html","")
        board = chess.Board()
        for move in opening_line.replace("_", "\\").split("\\"):
            if "..." in move: move = move.split("...")[1]
            if "." in move: continue
            if move == "": continue
            board.push_san(move)
        fen = board.fen()
        info = get_opening_info_lichess_all(fen)
        count = int(info['white']) + int(info['draws']) + int(info['black'])
        counts[filename] = count
        pass
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    responses = []
    outtext = "**Most popular responses**\n\n"
    i = 0
    for response in sorted_counts:
        filename = response[0]
        count = response[1]
        first_sentences = get_first_two_sentences(filename)
        name = get_opening_name(filename)
        namestring = ""
        if name is not None: namestring = "(" + name + ")"
        if name is None: namestring = ""
        opening_line = filename.replace("chessopeningtheory\\", "").replace("\\index.html", "")
        opening_line = opening_line.replace("_", " ")
        new_opening_line = ''
        for move in opening_line.split("\\"):
            if "..." in move:
                move = move.split("...")[1]
            new_opening_line += move + " "
        opening_line = new_opening_line.strip()
        last_word = opening_line.split(" ")[-1]
        last_last_word = opening_line.split(" ")[-2]
        last_last_last_word = opening_line.split(" ")[-3]
        response_move = last_word
        if "." in last_last_word:
            response_move = last_last_word + " " + response_move
        else:
            response_move = last_last_last_word + ".." + response_move
        response_move = response_move.replace("chessopeningtheory/","")
        addstring = "* " + response_move + " " + namestring + " " + first_sentences
        opening_lichess = "https://lichess.org/analysis/pgn/" + opening_line.replace(" ", "+")
        wiki_link = filename.replace("\\", "/").replace("chessopeningtheory/","").replace("/index.html", "")
        if wiki_link[len(wiki_link) - 1] == "/":
            wiki_link = wiki_link[:len(wiki_link) - 1]
        wiki_link = "wiki/Chess_Opening_Theory/" + wiki_link
        #print(wiki_link)
        addstring += " ([Lichess analysis](" + opening_lichess + ")) ([Wikibooks](https://en.wikibooks.org/" + wiki_link + ")) (" + str(count) + " games)"
        outtext += addstring + "\n\n"
        addstring = ''
        i += 1
        if i >= 5: break
    return outtext
    #print(filenames)

def engine_eval(engine, filename, timelimit):
    key = filename.replace("chessopeningtheory\\", "").replace("\\index.html", "")
    board = chess.Board()
    full_move = 0
    half_move = 0
    i = 0
    opening_line = ''
    for move in key.replace("_", "\\").split("\\"):
        if "..." in move: move = move.split("...")[1]
        if "." in move: continue
        if move == "": continue
        board.push_san(move)
        if i % 2 == 0:
            full_move += 1
            opening_line += str(full_move) + ". "
        else:
            opening_line += ""
        opening_line += move + " "
        half_move += 1
        i += 1
    half_move += 1
    if i % 2 == 0: full_move += 1
    fen = board.fen()
    orig_board = chess.Board(fen)
    with engine.analysis(board, chess.engine.Limit(time=timelimit)) as analysis:
        for info in analysis:
            #print(info.get('score'))
            pass
    pv = analysis.info['pv'][0]
    #print("pv", pv)
    #print(opening_line, orig_board)
    pvline = analysis.info['pv']
    full_pv = opening_line
    full_pv += "**"
    #half_move += 1
    for move in pvline:
        if half_move % 2: # odd
            full_pv += str(full_move) + ". "
        else:
            opening_line += ""

        half_move += 1
        if half_move % 2: full_move += 1
        full_pv += str(orig_board.san(move)) + " "
     #   print(opening_line, move)
        orig_board.push(move)
    full_pv = full_pv.strip()
    full_pv += "**"
    #print(full_pv)

  #  for
    score = analysis.info['score'].relative.score()
    turn = analysis.info['score'].turn
    depth = analysis.info['depth']
    if turn == False: # black
        score *= -1
    return score, board.san(pv), full_pv, depth

def lichess_engine_eval(filename):
    key = filename.replace("chessopeningtheory\\", "").replace("\\index.html", "")
    board = chess.Board()
    full_move = 0
    half_move = 0
    i = 0
    opening_line = ''
    for move in key.replace("_", "\\").split("\\"):
        if "..." in move: move = move.split("...")[1]
        if "." in move: continue
        if move == "": continue
        board.push_san(move)
        if i % 2 == 0:
            full_move += 1
            opening_line += str(full_move) + ". "
        else:
            opening_line += ""
        opening_line += move + " "
        half_move += 1
        i += 1
    half_move += 1
    if i % 2 == 0: full_move += 1
    fen = board.fen()
    print(fen)
    orig_board = chess.Board(fen)
    info = get_analysis_info_lichess(fen)
    if info is None: return None
    depth = info['depth']
    score = info['pvs'][0]['cp']
    best_move = None
    #print("depth", depth)
    pv = info['pvs'][0]['moves']
    pvline = pv.split(' ')
    print(pvline)
    full_pv = opening_line
    full_pv += "**"
    #half_move += 1
    i = 0
    for move in pvline:
        if half_move % 2: # odd
            full_pv += str(full_move) + ". "
        else:
            opening_line += ""
        half_move += 1
        if half_move % 2: full_move += 1
        print(move)
        if i == 0: best_move = str(orig_board.san(chess.Move.from_uci(move)))
        full_pv += str(orig_board.san(chess.Move.from_uci(move))) + " "
     #   print(opening_line, move)
        orig_board.push(chess.Move.from_uci(move))
        i += 1
    full_pv = full_pv.strip()
    full_pv += "**"
    return depth, score, best_move, full_pv
    #print(opening_line)
    #print(pvline)
    #print(full_pv)
    #print(best_move)

def post_daily_puzzle(reddit, puzzle):
    subr = 'chessopeningtheory'  # Choose your subreddit

    subreddit = reddit.subreddit(subr)  # Initialize the subreddit to a variable

    title = "[Daily Puzzle] " + puzzle.opening
    print("Posting thread:", title, puzzle.url)
    result = subreddit.submit(title, url=puzzle.url)
    comment_result = result.reply(body='More puzzles based around ' + puzzle.opening + ': https://lichess.org/training/' + puzzle.opening.replace(' ', '_') + '.')
    print(result)
    print('comment', comment_result)
    pass

def get_puzzles():
    print("Getting puzzles")
    ff = open('lichess_db_puzzle.csv')
    lines = ff.readlines()
    ff.close()
    puzzles = []
    i = 0
    for line in lines:
        line = line.replace("\n","")
        #print(line)
        line_split = line.split(",")
        #print(len(line_split))
        opening_name = ''
        if 'lichess.org' in line_split[-2]:
            continue
        opening_name = line_split[-2]
        opening_name = opening_name.replace("_", " ")
        id = line_split[0]
        url = "https://lichess.org/training/" + str(id)
        cur_puzzle = Puzzle()
        cur_puzzle.opening = opening_name
        cur_puzzle.id = id
        cur_puzzle.url = url
        puzzles.append(cur_puzzle)
        i += 1
        if i >= 1000000000: break
    return puzzles

def is_opening_valid_lichess(opening_name):
    opening_name = opening_name.replace(' ', '_')
    opening_name = opening_name.replace(':', '')
    opening_name = opening_name.replace(',', '')
    opening_name = opening_name.replace('\'', '')
    opening_name = opening_name.strip()
    #opening_name = opening_name.replace(' ', '_')

    resp = req.get('https://lichess.org/training/' + opening_name)
    print('https://lichess.org/training/' + opening_name)
    if opening_name in resp.text or opening_name in resp.text.replace("Defense", "Defence") or opening_name in resp.text.replace("Defence", "Defense"):
        return 'https://lichess.org/training/' + opening_name
    else:
        return False
    pass

def get_valid_lichess(opening_name):
    split = opening_name.split(' ')
    while len(split) > 1:
        new_opening_name = ''
        for item in split:
            new_opening_name += item + ' '
        new_opening_name = new_opening_name.strip()
        print(new_opening_name)
        new_opening_name = new_opening_name.replace(",", "")
        new_opening_name = new_opening_name.replace(":", "")

        result = is_opening_valid_lichess(new_opening_name)
        if result:
            return new_opening_name, result
        split.pop()
    return None

def get_parent(filename):
    directory = filename.replace("\\index.html", "")
    split = directory.split("\\")
    split.pop()
    parent_directory = ''
    for item in split:
        parent_directory += item + '\\'
    parent_file = parent_directory + "index.html"
    return get_opening_name(parent_file), parent_file

def get_full_parent_lichess(filename):
    filename = filename.replace("\\\\", "\\")
    opening_name = get_opening_name(filename).strip()
    finished = False
    while not finished:
        valid = get_valid_lichess(opening_name)
        if valid is None:
            opening_name = get_lichess_name(filename)
            if opening_name is not None:
                valid = get_valid_lichess(opening_name)
        print(opening_name, valid)
        if valid is None:
            parent = get_parent(filename)
            opening_name = parent[0].strip()
            filename = parent[1]
        else:
            return valid

def get_lichess_name(filename):
    filename = filename.replace('\\index.html','').replace('chessopeningtheory\\','')
    key = filename
    board = chess.Board()
    for move in key.replace("_", "\\").split("\\"):
        if "..." in move: move = move.split("...")[1]
        if "." in move: continue
        if move == "": continue
        board.push_san(move)
    fen = board.fen()
    info = get_opening_info_lichess_all(fen)
    time.sleep(.250)
    if info is not None:
        if 'opening' in info:
            if info['opening'] is not None:
                if 'name' in info['opening']:
                    opening_name = str(info['opening']['name'])
                    return opening_name

#print(get_full_parent_lichess("chessopeningtheory\\1._e4\\1...e5\\2._f4\\2...exf4\\3._Nf3\\3...g5\\4._h4\\4...g4\\5._Ne5\\5...Nf6\\index.html"))
#print(get_responses("chessopeningtheory\\1._e4\\1...c5\\index.html"))
#print(get_first_two_sentences("chessopeningtheory\\1._e4\\1...c5\\2._Nf3\\2...e6\\index.html"))
#sys.exit()

#responses = get_responses("1._e4\\1...c5\\2._Nf3\\2...Nc6\\index.html")
#responses = get_responses("1._e4\\1...e5\\2._f4\\2...exf4\\3._Nf3\\3...g5\\4._h4\\4...g4\\5._Ne5\\5...Nf6\\")
#print(opening_line_to_filename(random.choice(valid_openings).line))
#score = engine_eval(engine, "chessopeningtheory\\1._e4\\index.html", 10)
#print(score)
#sys.exit()
#print(get_valid_lichess('Sicilian Defense with 2...Nc6'))
#lichess_engine_eval('chessopeningtheory\\1._e4\\1...c5\\2._Nf3\\2...e6\\index.html')
#sys.exit()
if __name__ == "__main__":
    #authenticate
    credentials = 'client_secrets.json'
    with open(credentials) as f:
        creds = json.load(f)

    reddit = praw.Reddit(client_id=creds['client_id'],
                         client_secret=creds['client_secret'],
                         user_agent=creds['user_agent'],
                         redirect_uri=creds['redirect_uri'],
                         refresh_token=creds['refresh_token'])
    puzzles = get_puzzles()
    # print(puzzles)
   # sys.exit()
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
        actual_len = 0
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
            actual_len += len(line)
            is_valid = True
        if actual_len < 100: is_valid = False
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
            #print(filename)
            #sys.exit()
            #if "1. e4\\1...Nf6\\2. Bc4" in filename:
                #print(fulltext)
             #   sys.exit()
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


   # weekly_openings = get_weekly_openings(valid_openings)
    #new_weekly_opening(reddit, valid_openings)
    #result = post_thread(reddit, random.choice(valid_openings).line, valid_openings, "random")
    #result = post_weekly_thread(reddit, valid_openings)
    skip_first = True
    i = 0
   # responses = get_responses("1._e4\\1...c5\\2._Nf3\\2...Nc6\\index.html")
    #sys.exit()
    time_daily_posted = time.time() - 100000000
    if skip_first:
        time_daily_posted = time.time()
    while True:
        print(len(valid_openings), "valid openings")
        time_since_daily = time.time() - time_daily_posted
        if time_since_daily > 24 * 60 * 60:
            print("Posting daily puzzle")
            post_daily_puzzle(reddit, random.choice(puzzles))
        i += 1
        if i > 1 or not skip_first:
            print("Posting weekly thread")
            post_weekly_thread(reddit, all_openings)
            time.sleep(2)
            print("Posting random thread")
            valid_openings = post_thread(reddit, random.choice(valid_openings).line, valid_openings, "random")
        else:
            print("Skipping first run")
        time.sleep(60*60*8+20)