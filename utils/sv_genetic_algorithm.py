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

    def __init__(self, length, values):

        self.genes = [random.choice(values) for _ in range(length)]
        self.fitness = -1


def SvGAmain(criteria,values,populations=20,generations=1000,\
            threshold=0.9,mutator=0.1,mutofactor=0.1,selector=0.2,seed=0):
    """
    Main function GA
    """
    if not criteria or not values:
        return None
    """
    random.seed(seed)
    emax = lambda a,b: a if (a > b) else b
    emin = lambda a,b: a if (a < b) else b
    all_max = reduce(emax,[reduce(emax, x) for x in criteria])
    all_min = reduce(emin,[reduce(emin, x) for x in criteria])
    all_dif = all_max-all_min
    """
    """
    print(f'------------------------------------ \
          \nGA started \
          \nGA criteria: {[[round(i,2) for i in x] for x in criteria[:2]]} ...')
    """
    criteria_len = len(criteria)
    agents = init_agents(populations, criteria_len, values)
    #stepper = 0.76
    condition = False

    # for generation in range(generations):

    #print ('Generation: ' + str(generation))
    agents = fitness(agents, criteria, criteria_len)
    agents = selection(agents, selector)
    agents = crossover(agents, values, populations, criteria_len)
    agents = mutation(agents, mutofactor, mutator, criteria_len)
    """
    if any(agent.fitness >= stepper for agent in agents):
        combo.append(sorted(agents, key=lambda agent: agent.fitness, reverse=True)[0].genes)
        print(f"GA fitness >= {round(stepper,2)}, in #{generation} generation")
        stepper += 0.02
    """
    if any(agent.fitness >= threshold for agent in agents):

        agent = sorted(agents, key=lambda agent: agent.fitness, reverse=True)[0]
        print (f'GA ended \
                 \nGA fitness: {round(agent.fitness,4)}, in #{str(generation)} generation \
                 \nGA criteria: {[[round(i,2) for i in x] for x in agent.genes[:2]]} ... ')
        condition = True
        genes = [[agent.genes]]
    genes = [agent.genes for agent in agents]
    return genes, condition


def compare_two_lists(genes, criteria, criteria_len):
    """ fitness descision module """
    Ratio = []
    for i in range(len(genes)):
        j = i%criteria_len
        subpat = criteria[j]           
        subagl = genes[i]
        mainfunc = lambda y, x: (all_dif-abs(y-x))/all_dif
        coef = list(map(mainfunc, subagl, subpat))
        Ratio.append(mean(coef))
    Ratio = mean(Ratio)
    #print (Ratio)
    return Ratio


def init_agents(population, length, values):

    return [Agent(length, values) for _ in range(population)]


def fitness(agents, criteria, criteria_len, all_dif):

    for agent in agents:
        agent.fitness = compare_two_lists(agent.genes, criteria, criteria_len)

    return agents


def selection(agents, selector):

    agents = sorted(agents, key=lambda agent: agent.fitness, reverse=True)
    #print ('\n'.join(map(str, agents)))
    agents = agents[:int(selector * len(agents))]

    return agents


def crossover(agents, values, populations, criteria_len):

    offspring = []

    for _ in range((population - len(agents)) // 2):

        parent1 = random.choice(agents)
        parent2 = random.choice(agents)
        child1 = Agent(criteria_len, values)
        child2 = Agent(criteria_len, values)
        split = random.randint(0, criteria_len)
        child1.genes = parent1.genes[0:split] + parent2.genes[split:criteria_len]
        child2.genes = parent2.genes[0:split] + parent1.genes[split:criteria_len]

        offspring.append(child1)
        offspring.append(child2)

    agents.extend(offspring)

    return agents


def mutation(agents, mutofactor, mutator, criteria_len):

    for agent in agents:
        for idx, param in enumerate(agent.genes):
            if random.uniform(0.0, 1.0) <= mutofactor:
                agent.genes = agent.genes[0:idx] + \
                    [[random.uniform(-mutator,mutator)+d for d in param]] + \
                    agent.genes[idx+1:criteria_len]
    return agents

