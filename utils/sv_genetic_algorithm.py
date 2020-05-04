# taken from https://github.com/nortikin/simple-ga
# making comparement between vertices and choose best match

import random
from functools import reduce
from statistics import mean, variance


"""
Agent
SvGAmain
compare_two_lists
init_agents
fitness
selection
crossover
mutation
"""


class Agent:

    def __init__(self, length):

        self.genes = [random.choice(values) for _ in range(length)]
        self.fitness = -1


def SvGAmain(pattern,values,populations=20,generations=1000,\
            threshold=0.9,mutator=0.1,mutofactor=0.1,selector=0.2,seed=0):
    """
    Main function GA
    """
    if not pattern or not values:
        return
    random.seed(seed)
    emax = lambda a,b: a if (a > b) else b
    emin = lambda a,b: a if (a < b) else b
    all_max = reduce(emax,[reduce(emax, x) for x in pattern])
    all_min = reduce(emin,[reduce(emin, x) for x in pattern])
    all_dif = all_max-all_min
    """
    print(f'------------------------------------ \
          \nGA started \
          \nGA pattern: {[[round(i,2) for i in x] for x in pattern[:2]]} ...')
    """
    pattern_len = len(pattern)
    agents = init_agents(population, pattern_len)
    stepper = 0.76
    condition = False

    # for generation in range(generations):

    #print ('Generation: ' + str(generation))
    agents = fitness(agents)
    agents = selection(agents)
    agents = crossover(agents)
    agents = mutation(agents)

    if any(agent.fitness >= stepper for agent in agents):
        combo.append(sorted(agents, key=lambda agent: agent.fitness, reverse=True)[0].genes)
        print(f"GA fitness >= {round(stepper,2)}, in #{generation} generation")
        stepper += 0.02
    if any(agent.fitness >= threshold for agent in agents):

        agent = sorted(agents, key=lambda agent: agent.fitness, reverse=True)[0]
        print (f'GA ended \
                 \nGA fitness: {round(agent.fitness,4)}, in #{str(generation)} generation \
                 \nGA pattern: {[[round(i,2) for i in x] for x in agent.genes[:2]]} ... ')
        condition = True
    return agent.genes, condition


def compare_two_lists(agent_list, pattern):
    """ fitness descision module """
    lenpat = len(pattern)
    Ratio = []
    for i in range(len(agent_list)):
        j = i%lenpat
        subpat = pattern[j]           
        subagl = agent_list[i]
        mainfunc = lambda y, x: (all_dif-abs(y-x))/all_dif
        coef = list(map(mainfunc, subagl, subpat))
        Ratio.append(mean(coef))
    Ratio = mean(Ratio)
    #print (Ratio)
    return Ratio


def init_agents(population, length):

    return [Agent(length) for _ in range(population)]


def fitness(agents):

    for agent in agents:
        agent.fitness = compare_two_lists(agent.genes, pattern)

    return agents


def selection(agents):

    agents = sorted(agents, key=lambda agent: agent.fitness, reverse=True)
    #print ('\n'.join(map(str, agents)))
    agents = agents[:int(selector * len(agents))]

    return agents


def crossover(agents):

    offspring = []

    for _ in range((population - len(agents)) // 2):

        parent1 = random.choice(agents)
        parent2 = random.choice(agents)
        child1 = Agent(pattern_len)
        child2 = Agent(pattern_len)
        split = random.randint(0, pattern_len)
        child1.genes = parent1.genes[0:split] + parent2.genes[split:pattern_len]
        child2.genes = parent2.genes[0:split] + parent1.genes[split:pattern_len]

        offspring.append(child1)
        offspring.append(child2)

    agents.extend(offspring)

    return agents


def mutation(agents):

    for agent in agents:
        for idx, param in enumerate(agent.genes):
            if random.uniform(0.0, 1.0) <= mutofactor:
                agent.genes = agent.genes[0:idx] + \
                    [[random.uniform(-mutator,mutator)+d for d in param]] + \
                    agent.genes[idx+1:pattern_len]
    return agents

