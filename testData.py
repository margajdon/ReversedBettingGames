import json
from player import Player, collectSuspicions
import multiprocessing
import json
import time
import os
from tqdm import tqdm

def testData():
    for folder in os.listdir('./evolveData'):  
        # Load strategies
        allStrategies = json.load(open('./evolveData/' + folder + '/hallOfFame.json'))
        allStrategies = list(allStrategies.values())
        
        # Generate suspicions
        print("Generating suspicions...")
        suspicions = {}
        iterations = 20000
        for n in range(iterations):
            suspicions[n] = collectSuspicions()
        print("Starting testing...")

        # Initialize
        global progressBar
        progressBar = tqdm(total=iterations, mininterval=0.5)
        manager = multiprocessing.Manager()
        data, lock = manager.dict(), manager.Lock()

        # Divide strategies into chunks of equal size
        pool = multiprocessing.Pool()
        for i in range(len(suspicions)):
            pool.apply_async(handleSus, (i, suspicions[i], allStrategies, data, lock),
                callback=updateProgressbar)

        pool.close()
        pool.join()

        # Save data in uniquely named file
        timestr = time.strftime("%Y-%m-%d_%H-%M")
        filename = './evolveData/' + folder + '/test' + timestr + '.json'
        with open(filename, 'w') as outfile:
            json.dump(data.copy(), outfile)

def analyzeData():
    for folder in os.listdir('./evolveData'):
        # Load file
        print(folder)
        for file in os.listdir('./evolveData/' + folder):
            if file != 'hallOfFame.json' or file != 'stats.json':
                data = json.load(open('./evolveData/' + folder + '/' + file))
        
        # Load empty dicts
        stratsTopTen = emptyDict(100)
        stratsFirst = emptyDict(100)

        # Iterate over data
        for sus in data:
            currentResults = data[sus]
            
            # Note top 10
            for id, _ in currentResults[:10]:
                stratsTopTen[id] += 1
            
            # Note first
            bestId, _ = currentResults[0]
            stratsFirst[bestId] += 1
        
        # Sort both by times of occurring
        sortedTopTen = list(reversed(sorted(
            [(_id, times) for _id, times in stratsTopTen.items()], key=lambda x: x[1])))
        sortedFirst = list(reversed(sorted(
            [(_id, times) for _id, times in stratsFirst.items()], key=lambda x: x[1])))

        # Get top ten of both
        sortedTopTen = sortedTopTen[:10]
        sortedFirst = sortedFirst[:10]

        # Get ids in both
        overlap = []
        sortedTopTenId = [x for x, _ in sortedTopTen[:10]]
        for id, _ in sortedFirst:
            if id in sortedTopTenId:
                overlap.append(id)

        # Calculate average score of scores doing best
        scores = {}
        for id in overlap:
            scores[id] = {}
            scores[id]['max'] = 0
            scores[id]['avg'] = 0
            for sus in data:
                currentResults = data[sus]
                for _id, score in currentResults:
                    if _id == id:
                        scores[id]['avg'] += score      # Build up total score
                        if score > scores[id]['max']:
                            scores[id]['max'] = score   # Keep track of highest score
        # Calculate average score
        totalSus = len(data)
        for key, val in scores.items():
            scores[key]['avg'] = round(val['avg'] / totalSus, 2)

        # Strategies file
        allStrategies = json.load(open('./evolveData/' + folder + '/hallOfFame.json'))
        for id in overlap:
            print("{_id}: {s}".format(_id=id, s=allStrategies[str(id)]))
        print('')
    
def emptyDict(len):
    result = {}
    for i in range(len):
        result[i] = 0
    return result

def handleSus(index, suspicions, strategies, data, lock):
    # Make players with each strategy
    players = []
    for n in range(len(strategies)):
        players.append(Player(_id=n, 
            _allsus=suspicions.copy(), _strategy=strategies[n]))
    
    # Let them play game
    for p in players:
        p.play(suspicions.copy())

    # Combine id of strategy with score gained
    idScores = [(p.id, p.score) for p in players]

    # Combine data
    with lock:
        data[str(index)] = list(reversed(sorted(idScores, key=lambda x: x[1])))

def updateProgressbar(_):
    progressBar.update()

if __name__ == "__main__":
    #testData()
    analyzeData()
