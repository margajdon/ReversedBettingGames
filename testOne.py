from player import collectSuspicions, Player
import statistics as s
from tqdm import tqdm

def main(testStrategy):
    results = []

    # Generate suspicions
    iterations = 200000
    suspicions = {}
    print("Generating suspicions...")
    t = tqdm(total=iterations)
    for n in range(iterations):
        suspicions[n] = collectSuspicions()
        t.update()
    t.close()

    # Test each strategy
    resultsNonZero = []
    lower = 0
    losersOrder = [9,8,7,6,5,4,3,2,1]
    print("Testing strategy...")
    t = tqdm(total=iterations)
    for i in range(iterations):
        player = Player(suspicions[i], testStrategy)
        for n in range(1, 10):
            player.processRound(n, losersOrder[n-1])
        if player.score != 0:
            resultsNonZero.append(player.score)
        if player.score < 10230:
            lower += 1
        results.append(player.score)
        t.update()
    t.close()
    print('')

    zeros = 0
    for r in results:
        if r == 0:
            zeros += 1

    print("Mean: {m}\nSt.Dev: {sd}\nMax: {ma}\nZeros: {z}\n".
        format(m=s.mean(results), sd=s.stdev(results), ma=max(results), z=zeros))
    print("Lower score than baseline achieved in {} of scores.".format(lower/200000))

if __name__ == "__main__":
    """
    Test one (or multiple) strategies specifically and get statistics on them.
    """
    toTest = ['prop2','prop2','prop2','prop2','prop2','prop2','prop2','prop2','allIn']
    main(toTest)