# taken from https://github.com/nortikin/simple-ga
# making comparement between vertices and choose best match

import random
from functools import reduce
from statistics import mean, variance


"""
in  pattern v   d=[] n=0
in  data    v   d=[] n=0
in  population s d=20 n=2
in  generations s d=10000 n=2
in  threshold s d=0.9 n=2
in  mutator s d=0.1 n=2
in  selector s d=0.2 n=2
in  all_apart s d=0 n=2
out combination  v
"""


class Agent:

    def __init__(self, length):

        self.string = [random.choice(data[0]) for _ in range(length)]
        # self.string = ''.join(random.choice(data[0]) for _ in xrange(length))
        self.fitness = -1

    def __str__(self):

        return 'String: ' + str(self.string) + ' Fitness: ' + str(self.fitness)



def compare_two_lists(agent_list,pattern):
    """ fitness descision module """
    lenpat = len(pattern)
    Ratio = []
    for i in range(len(agent_list)):
        j = i%lenpat
        subpat = pattern[j]           
        subagl = agent_list[i]
        # main descision part here, so we assign 
        # coef to all or to separate and summ
        if all_apart == 0:
            # full match
            coef = [1 if x in subpat else 0 for x in subagl]
        elif all_apart == 1:
            # closest
            mainfunc = lambda y, x: (all_dif-abs(y-x))/all_dif
            coef = list(map(mainfunc, subagl, subpat))
        else:
            coef = [1 if x in subpat else 0 for x in subagl]
        Ratio.append(mean(coef))
    Ratio = mean(Ratio)
    #print (Ratio)
    return Ratio


def ga():

    agents = init_agents(population, in_str_len)

    for generation in range(generations):

        #print ('Generation: ' + str(generation))

        agents = fitness(agents)
        agents = selection(agents)
        agents = crossover(agents)
        agents = mutation(agents)

        if any(agent.fitness >= threshold for agent in agents):

            print (f'Last generation #{str(generation)}')
            agent = sorted(agents, key=lambda agent: agent.fitness, reverse=True)[0]
            print (f'GA ended with {type(agent.string)} {len(agent.string)}, \
                     \n{agent.string[:3]}... \
                     \nFitness: {agent.fitness}')
            return agent.string
    return [None]
    


def init_agents(population, length):

    return [Agent(length) for _ in range(population)]


def fitness(agents):

    for agent in agents:
        agent.fitness = compare_two_lists(agent.string, in_str)

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
        child1 = Agent(in_str_len)
        child2 = Agent(in_str_len)
        split = random.randint(0, in_str_len)
        child1.string = parent1.string[0:split] + parent2.string[split:in_str_len]
        child2.string = parent2.string[0:split] + parent1.string[split:in_str_len]

        offspring.append(child1)
        offspring.append(child2)

    agents.extend(offspring)

    return agents


def mutation(agents):

    for agent in agents:
        for idx, param in enumerate(agent.string):
            if random.uniform(0.0, 1.0) <= mutator:
                if all_apart == 0:
                    agent.string = agent.string[0:idx] + \
                                [(random.choice(data[0]))] + \
                                agent.string[idx+1:in_str_len]
                elif all_apart == 1:
                    agent.string = agent.string[0:idx] + \
                                [[random.uniform(-mutator,mutator)+d for d in param]] + \
                                agent.string[idx+1:in_str_len]
                else:
                    agent.string = agent.string[0:idx] + \
                                [(random.choice(data[0]))] + \
                                agent.string[idx+1:in_str_len]

    return agents

if data and pattern:
    in_str = pattern[0]
    emax = lambda a,b: a if (a > b) else b
    emin = lambda a,b: a if (a < b) else b
    all_max = reduce(emax,[reduce(emax, x) for x in in_str])
    all_min = reduce(emin,[reduce(emin, x) for x in in_str])
    all_dif = all_max-all_min
    print(f'GA initialised with {type(in_str)} {len(in_str)} \
            \n{in_str[:3]}...')
    in_str_len = len(in_str)
    combination = [ga()]
