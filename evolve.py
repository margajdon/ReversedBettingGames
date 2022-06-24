from deap import base, creator, tools
from dotenv import load_dotenv
from .player import Player, collectSuspicions
import multiprocessing
from tqdm import tqdm
from functools import partial
import random
import numpy
import json
import time
import os

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

# Get hyperparameters 
load_dotenv()
crossoverRate = float(os.getenv("CROSSOVER_RATE"))
populationSize = int(os.getenv("POPULATION_SIZE"))
generations = int(os.getenv("NGEN"))
mutationRates = os.getenv("MUTATION_RATES").split(", ")
mutationRates = [float(x) for x in mutationRates]

# Define evaluate and mutate methods for DEAP
def evaluate(individual, allSuspicions):
    """
    Player plays `rounds` amount of games, the sum of the score in all the
    games is returned.
    """
    load_dotenv()
    rounds = int(os.getenv('ROUNDS'))
    indivPlayer = Player(allSuspicions[0], individual)
    score = 0
    for i in range(rounds):
        score += indivPlayer.play(allsus=allSuspicions[i])
    return (score,)

def mutate(ind, toolbox, index):
    """
    Individual changes strategy for round `index`. 
    It is sure to have a new value after mutating.    
    """
    mutant = toolbox.individual(ind.copy())
    while ind[index] == mutant[index]:
        newGene = random.randrange(0, len(availableStrategies[index + 1]))
        mutant[index] = availableStrategies[index + 1][newGene]
    del mutant.fitness.values
    return mutant

# Initializes a player individual with a given or random strategy
def getStrategy(icls, strat=None):
    if strat is not None:
        return icls(strat)
    strategy = list()
    for n in range(1, 10):
        index = random.randrange(0, len(availableStrategies[n]))
        strategy.append(availableStrategies[n][index])
    return icls(strategy)

# Define fitness score and individual
creator.create("Fitness", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.Fitness)

# Define operators
toolbox = base.Toolbox()
toolbox.register("individual", getStrategy, creator.Individual)
toolbox.register("mate", tools.cxUniform)
toolbox.register("mutate", mutate, toolbox=toolbox)
toolbox.register("select", tools.selTournament, k=populationSize, tournsize=10)
toolbox.register("evaluate", evaluate)

if __name__ == "__main__": 
    # Make a pool and register concurrent map
    pool = multiprocessing.Pool()
    toolbox.register("map", pool.map)

    # Define statistics
    stats = tools.Statistics(key=lambda ind:ind.fitness.values)
    stats.register("avg", numpy.mean, axis=0)
    stats.register("std", numpy.std, axis=0)
    stats.register("min", numpy.min, axis=0)
    stats.register("max", numpy.max, axis=0)

    # Define control strategy
    controlStrat = ["prop10", "prop9", "prop8", "prop7", "prop6", "prop5", 
        "prop4", "prop3", "allIn"] 
    population = [controlStrat]

	# Create starting population based on control
    for currentRound in range(1, 10):
        for strategy in availableStrategies[currentRound]:
            if controlStrat[currentRound-1] == strategy:
                continue
            newPlayer = controlStrat.copy()
            newPlayer[currentRound-1] = strategy
            population.append(newPlayer)
    
    # Get amount of rounds and create first suspicions
    load_dotenv()
    rounds = int(os.getenv('ROUNDS'))
    manager = multiprocessing.Manager()
    allSuspicions = manager.dict()
    for i in range(rounds):
        allSuspicions[i] = collectSuspicions()

    # Make strategies into individuals and determine their fitness
    population = [toolbox.individual(strat=p) for p in population]  
    fitnesses = toolbox.map(partial(toolbox.evaluate, allSuspicions=allSuspicions), 
        population)
    for ind, fit in zip(population, fitnesses):
        ind.fitness.values = fit

    # Initialize hall of fame
    hallOfFame = tools.HallOfFame(100)
    hallOfFame.update(population)

    # Initialize statistics record
    newstats = stats.compile(population)
    newstats = [[round(x, 3) for x in newstats[s]] for s in newstats]
    statsRecord = {
        0 : newstats
    }

    # Initialize progress bar
    progressBar = tqdm(total=generations)

    # Perform evolution
    for gen in range(1, generations + 1):
        # Select next generation and clone them
        offspring = toolbox.select(population)
        offspring = [toolbox.individual(x.copy()) for x in offspring]
        
        # Apply crossover
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            toolbox.mate(child1, child2, indpb=crossoverRate)
            del child1.fitness.values
            del child2.fitness.values

        # Each round has a chance of mutating
        for mutant in offspring:
            for toMutate in range(0, 9):
                if random.random() < mutationRates[toMutate]:
                    toolbox.mutate(mutant, index=toMutate)
                    del mutant.fitness.values
            
        # Get new suspicions
        for i in range(rounds):
            allSuspicions[i] = collectSuspicions()

        # Evaluate the offspring with an invalid fitness
        invalidInds = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(partial(toolbox.evaluate, allSuspicions=allSuspicions), 
            invalidInds)
        for ind, fit in zip(invalidInds, fitnesses):
            ind.fitness.values = fit
        
        # Replace population with offspring
        population[:] = offspring

        # Update statistics and hall of fame
        newstats = stats.compile(population)
        statsRecord[gen] = [[round(x, 3) for x in newstats[s]] for s in newstats]
        hallOfFame.update(population)
        progressBar.update()
        
    # Create directory for results
    dirname = time.strftime("%m-%d_%H%M")
    os.mkdir("./evolveData/" + dirname) 

    # Write statistics to file
    filename = "./evolveData/" + dirname + "/stats.json"
    with open(filename, "w") as f:
        json.dump(statsRecord, f)

    # Write hall of fame to file
    filename = "./evolveData/" + dirname + "/hallOfFame.json"
    hallOfFame = [x for x in hallOfFame]
    hallOfFame = dict(zip(range(len(hallOfFame)), hallOfFame))
    with open(filename, "w") as f:
        json.dump(hallOfFame, f)