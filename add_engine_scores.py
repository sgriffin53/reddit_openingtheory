import main
import chess
import chess.engine

engine = chess.engine.SimpleEngine.popen_uci("stockfish15.exe")
engine.configure({"Threads": 30})
engine.configure({"Hash": 8192})
filenames = main.get_filenames()
i = 0
for filename in filenames:
    if i == 0:
        i += 1
        continue
    i += 1
    directory = filename.replace("\\index.html", "")
    result = main.engine_eval(engine, filename, 300)
    score = result[0]
    depth = result[1]
    pv = result[2]
    writefile = directory + "\\engine_score.txt"
    ff = open(writefile, 'w', encoding='utf-8')
    ff.write(str(score) + ", " + str(pv) + ", " + str(depth) + "\n")
    ff.close()
    print(i, writefile, score, pv, depth)