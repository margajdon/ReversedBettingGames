from scipy.stats import dirichlet

# Define strategies are available per round
availableStrategies = {
    1: ["allIn", "prop10", "prop9", "prop8", "prop7", "prop6", "prop5", "prop4", "prop3", "prop2"],
    2: ["allIn", "prop9", "prop8", "prop7", "prop6", "prop5", "prop4", "prop3", "prop2"],
    3: ["allIn", "prop8", "prop7", "prop6", "prop5", "prop4", "prop3", "prop2"],
    4: ["allIn", "prop7", "prop6", "prop5", "prop4", "prop3", "prop2"],
    5: ["allIn", "prop6", "prop5", "prop4", "prop3", "prop2"],
    6: ["allIn", "prop5", "prop4", "prop3", "prop2"],
    7: ["allIn", "prop4", "prop3", "prop2"],
    8: ["allIn", "prop3", "prop2"],
    9: ["allIn", "prop2"]
}

class Player:
    id = 0                  
    suspicion = []          # List of 10 numbers, representing probabilities of being the Mole per contestant
    allSuspicion = {}       # Pre-set suspicion per round
    strategy = []           # Indicates player strategy
    bets = {}               # Keep track of bets throughout game for calculating Molbonus
    score = 0               # Player's current score
    mole = 0                # Set Mole to player with index 0 
    
    def __init__(self, _allsus, _strategy, _id=0):
        # Basic game setup
        self.id = _id
        self.score, self.strategy = 100, _strategy
        self.averageScore, self.fitness = 0, 0
        self.allSuspicion = _allsus

        # Initialize empty bet
        self.bets = {1 : [], 2 : [], 3 : [],  4 : [], 5 : [],
        6 : [], 7 : [], 8 : [], 9 : []}

        # Initialize suspicion
        self.suspicion = self.allSuspicion[1]

    def play(self, allsus):
        """
        A full playthrough of game. Returns the final score.
        """
        # First make sure player is reset
        self.reset(allsus)

        # Play games
        # Losers are [9, 8, 7, 6, 5, 4, 3, 2, 1], 0 is Mole
        for round in range(1, 10):
            self.processRound(round, 10-round)
        return self.score
    
    def processRound(self, currentRound, loser):
        """
        Sets a bet for current round, calculates new score after loser leaves
        and updates suspicion. 
        """
        # First, set bet for current round
        # If player has no points, set 0 bet
        if self.score == 0:
            self.bets[currentRound] = [0] * 10

        # Else, set bet according to strategy
        else:
            currentStrategy = self.strategy[currentRound - 1]

            # If strategy is allIn, find main suspect and bet all points on them
            # Note: if player has same amount of prob on both,
            # they bet on contestant with lowest index
            if currentStrategy == "allIn":
                mainMole = self.suspicion.index(max(self.suspicion))
                bet, bet[mainMole] = [0] * 10, self.score
                self.bets[currentRound] = bet
            else:
                # If strategy is proportional, bet proportional to suspicion                                   
                self.bets[currentRound] = self.proportionalBet(currentStrategy)

        # Calculate new score based on loser in that round
        betOnLoser = self.bets[currentRound][loser]
        self.score = (self.score - betOnLoser) * 2

        if (currentRound < 9):
            # Update suspicion for next round
            self.suspicion = self.allSuspicion[currentRound + 1]
        else:
            # Game is over, calculate molbonus and set final score
            self.score += self.molBonus()

    def proportionalBet(self, strategy):
        # Find the number of people to bet on
        peopleToBet = int(strategy[4:])

        # Add index to each probability and sort these
        enumerated = enumerate(self.suspicion)
        probSorted = list(reversed(sorted(enumerated, key=lambda x: x[1])))

        # Split the sorted list in indexes and probabilities
        maxIndices = [x[0] for x in probSorted[:peopleToBet]]
        probabilities = [x[1] for x in probSorted[:peopleToBet]]

        # Normalize probabilities and set bet accordingly
        probabilities = [x/sum(probabilities) for x in probabilities]
        betValues = [round(x * self.score) for x in probabilities]

        # Combine indices with normalized probabilities
        normalizedIndex = zip(maxIndices, betValues)

        # Start with empty bet and fill in normalized values
        result = [0] * 10
        for (index, value) in normalizedIndex:
            result[index] = value  
        return result
    
    def molBonus(self):
        # Calculate molbonus
        molbonus = 0
        for n in range(1, 10):
            molbonus += self.bets[n][self.mole]
        return molbonus

    def reset(self, allsus):
        self.allSuspicion, self.bets = allsus, {}
        self.suspicion, self.score = self.allSuspicion[1], 100

def collectSuspicions():
    # Initialize
    losers = [9,8,7,6,5,4,3,2,1]
    activeContestants = [1] * 10
    result = {}

    # Set first suspicion
    current = getSuspicion(1, [], activeContestants)
    result[1] = current.copy()
    activeContestants[losers[0]] = 0
    current[losers[0]] = 0

    # Collect suspicions per round
    for r in range(2, 10):
        current = getSuspicion(r, current, activeContestants)
        result[r] = current.copy()
        activeContestants[losers[r-1]] = 0
        current[losers[r-1]] = 0

    return result

def getSuspicion(currentRound, suspicion, activeContestants, debug=False):
    """
    Set suspicion according to sample from Dirichlet distribution.
    """     
    if currentRound == 1:
        # Set bet with no knowledge, so symmetric Dirichlet
        # Variance 0.00089109, mean 0.1, diff entropy -19.759096838337683
        alpha = [10] * 10    

    else:
        # Set multiplier
        multiplier = 30

        # Multiply each value with the multiplier
        alpha = [x * multiplier for x in suspicion]  

        # If a player has disregarded a certain contestant, give them a little chance to come back.
        # If this is not done, player has a chance of ending up with no suspicion because of
        # disregarding the players who continue in the game.
        for index, param in enumerate(alpha):
            if activeContestants[index] and alpha[index] == 0:
                alpha[index] = multiplier / 20

    # Ensure no alpha is exactly zero
    for index, param in enumerate(alpha):
        alpha[index] = param + 0.0001
    
    sample = dirichlet.rvs(alpha).tolist()[0]
    return [round(x, 3) for x in sample]

if __name__ == "__main__":
    # Debug
    sus = collectSuspicions()
    test1 = Player(sus.copy(), ["prop3", "prop4", "prop3", "prop3", "prop3", "prop3", "prop3", "allIn", "allIn"])
    test2 = Player(sus.copy(), ["prop10", "prop4", "prop3", "prop3", "prop3", "prop3", "prop3", "allIn", "allIn"])
    for n in range(1, 10):
        test1.processRound(n, 10-n)        
        test2.processRound(n, 10-n)   
    print(test1.bets)   