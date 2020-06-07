# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import random
import time
from collections import namedtuple

import numpy as np
import bpy
from bpy.props import (
    BoolProperty, StringProperty, EnumProperty, IntProperty, FloatProperty
    )

from mathutils.noise import seed_set, random
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.core.update_system import make_tree_from_nodes, do_update
from sverchok.utils.listutils import (
    listinput_getI, 
    listinput_getF, 
    listinput_setI, 
    listinput_setF
    )

Gene = namedtuple('Gene', 'name, g_type, min_n, max_n, range, init_val')
GeneList = namedtuple('GeneList', 'name, g_type, num_length, init_val')

evolver_mem = {}

def is_valid_node(node, genotype_frame):
    if genotype_frame == 'All' and node.bl_idname in ["SvNumberNode", "SvListInputNode"]:
        return True
    if node.parent and node.parent.name == genotype_frame and node.bl_idname in ["SvNumberNode", "SvListInputNode"]:
        return True
    return False

def number_gene(node):
    num_type = node.selected_mode
    if node.selected_mode == "float":
        min_n = node.float_min
        max_n = node.float_max
        initial_value = node.float_
    else:
        min_n = node.int_min
        max_n = node.int_max
        initial_value = node.int_
    gene = Gene(name=node.name, g_type=num_type, min_n=min_n, max_n=max_n, range=max_n-min_n, init_val=initial_value)
    return gene

def list_gene(node):
    num_type = node.mode
    if num_type == 'int_list':
        num_length = node.int_
        init_val = listinput_getI(node,num_length)
    elif num_type == 'float_list':
        num_length = node.int_
        init_val = listinput_getF(node,num_length)
    else:
        num_length = node.v_int
        mem_list = node.vector_list
        init_val = [[mem_list[3*i], mem_list[3*i + 1], mem_list[3*i + 2]] for i in range(num_length)]
    gene = GeneList(name=node.name, g_type=num_type, num_length=num_length, init_val=init_val)
    return gene

def get_genes(target_tree, genotype_frame):
    genes = []
    for node in target_tree.nodes:
        if is_valid_node(node, genotype_frame):
            if node.bl_idname == "SvNumberNode":
                gene = number_gene(node)
            else:
                gene = list_gene(node)

            genes.append(gene)
    return genes

def list_cross(ancestor1_gene, ancestor2_gene, o_gene):
    mixing_factor = int(random()* o_gene.num_length)
    new_gene = [ancestor1_gene[i] for i in range(mixing_factor)]
    for g in ancestor2_gene:
        if not g in new_gene:
            new_gene.append(g)
    return new_gene

def set_list_node(gen_data, agent_gene, tree):
    if gen_data.g_type == 'int_list':
        node = tree.nodes[gen_data.name]
        listinput_setI(node, agent_gene, gen_data)
    elif gen_data.g_type == 'float_list':
        node = tree.nodes[gen_data.name]
        listinput_setF(node, agent_gene, gen_data)
    else:
        for i in range(gen_data.num_length):
            node.vector_list[3*i] = gen_data.init_val[agent_gene[i][0]]
            node.vector_list[3*i + 1] = gen_data.init_val[agent_gene[i][1]]
            node.vector_list[3*i + 2] = gen_data.init_val[agent_gene[i][2]]

def random_ancestor_mix(ancestor1_gene, ancestor2_gene):
    mixing_factor = random()
    new_gene = ancestor1_gene * mixing_factor + ancestor2_gene * (1 - mixing_factor)
    return new_gene

def random_element_swap(new_gene):

    item_a = int(random() * len(new_gene))
    item_b = int(random() * len(new_gene))
    temp_g = new_gene[item_a]
    new_gene[item_a] = new_gene[item_b]
    new_gene[item_b] = temp_g

class DNA:

    def __init__(self, genes_def, random_val=True, empty=False):
        self.genes_def = genes_def
        self.genes = []
        self.fitness = 0
        if empty:
            return
        self.fill_genes(random_val=random_val)

    def fill_genes(self, random_val=True):
        if random_val:
            for gene in self.genes_def:
                if isinstance(gene, GeneList):
                    agent_gene = list(range(gene.num_length))
                    np.random.shuffle(agent_gene)

                else:
                    agent_gene = gene.min_n + random() * gene.range
                    if gene.g_type == 'int':
                        agent_gene = int(agent_gene)
                self.genes.append(agent_gene)
        else:
            for gene in self.genes_def:
                if isinstance(gene, GeneList):
                    agent_gene = list(range(gene.num_length))
                else:
                    agent_gene = gene.init_val
                self.genes.append(agent_gene)

    def evaluate_fitness(self, tree, update_list, node):
        try:
            tree.sv_process = False
            for gen_data, agent_gene in zip(self.genes_def, self.genes):
                if isinstance(gen_data, GeneList):
                    set_list_node(gen_data, agent_gene, tree)

                else:
                    if gen_data.g_type == 'float':
                        tree.nodes[gen_data.name].float_ = agent_gene
                    else:
                        tree.nodes[gen_data.name].int_ = agent_gene

            tree.sv_process = True
            do_update(update_list, tree.nodes)
            agent_fitness = node.inputs[0].sv_get(deepcopy=False)[0]
            if isinstance(agent_fitness, list):
                agent_fitness = agent_fitness[0]
            self.fitness = agent_fitness
        finally:
            tree.sv_process = True

    def cross_over(self, other_ancestor, mutation_threshold):

        new_agent = DNA(self.genes_def, empty=True)
        for ancestor1_gene, ancestor2_gene, o_gene in zip(self.genes, other_ancestor.genes, self.genes_def):
            mutation_succes = random()
            if mutation_succes < mutation_threshold:
                total_reset_chance = random()
                total_reset_barrier = 0.5
                if total_reset_chance < total_reset_barrier:
                    #total gene reset
                    if isinstance(o_gene, GeneList):
                        new_gene = np.array(ancestor1_gene)
                        np.random.shuffle(new_gene)
                    else:
                        new_gene = o_gene.min_n + random() * o_gene.range
                else:
                    #small gene mutation
                    if isinstance(o_gene, GeneList):
                        new_gene = list_cross(ancestor1_gene, ancestor2_gene, o_gene)
                        random_element_swap(new_gene)

                    else:
                        new_gene = random_ancestor_mix(ancestor1_gene, ancestor2_gene)
                        small_mutation = (random() - 0.5) * o_gene.range * mutation_threshold
                        new_gene += small_mutation
                        new_gene = max(min(new_gene, o_gene.max_n), o_gene.min_n)

            else:
                if isinstance(o_gene, GeneList):
                    new_gene = list_cross(ancestor1_gene, ancestor2_gene, o_gene)
                else:
                    new_gene = random_ancestor_mix(ancestor1_gene, ancestor2_gene)


            if o_gene.g_type == 'int':
                new_gene = int(new_gene)
            new_agent.genes.append(new_gene)

        return new_agent

class Population:

    def __init__(self, genotype_frame, node, tree):
        self.node = node
        self.tree = tree
        self.time_start = time.time()
        self.genes = get_genes(tree, genotype_frame)
        self.update_list = make_tree_from_nodes([g.name for g in self.genes], tree)
        self.population_g = []
        self.init_population(node.population_n)


    def init_population(self, population_n):
        self.population_g.append(DNA(self.genes, random_val=False))
        for i in range(population_n-1):
            self.population_g.append(DNA(self.genes))



    def  evaluate_fitness_g(self):
        try:
            for agent in self.population_g:
                agent.evaluate_fitness(self.tree, self.update_list, self.node)
        finally:
            self.tree.sv_process = True
    def population_genes(self):
        return [agent.genes for agent in self.population_g]

    def population_fitness(self):
        return [agent.fitness for agent in self.population_g]

    def get_new_population(self, fitness, mode):
        '''Crossover and mutation of previous population to create the new population'''
        if mode == 'MAX':
            weights = np.power(np.array(fitness), self.node.fitness_booster)
        else:
            weights = 1/np.power(np.array(fitness), self.node.fitness_booster)
        weights = weights/np.sum(weights)

        parents_id = np.random.choice(len(self.population_g), [len(self.population_g)-1, 2], replace=True, p=weights)
        # we keep the fittest for the next generation
        new_population = [self.population_g[0]]
        mutation = self.node.mutation
        for ancestors in  parents_id:
            p0 = self.population_g[ancestors[0]]
            p1 = self.population_g[ancestors[1]]
            new_agent = p0.cross_over(p1, mutation)
            new_population.append(new_agent)

        return new_population

    def print_time_info(self, iteration):
        print(' '*80,end='\r')
        print("evolver on %s iteration" % (iteration + 1),"%s sec" % (time.time() - self.time_start), end='\r')

    def goal_achieved(self, fittest, mode, goal):
        if mode == "MAX":
            return fittest > goal
        if mode == "MIN":
            return fittest < goal

    def store_data(self, population_all, fitness_all):
        node_id = self.node.node_id
        evolver_mem[node_id]["population_all"] = population_all
        evolver_mem[node_id]["fitness_all"] = fitness_all
        evolver_mem[node_id]["genes"] = self.genes
        evolver_mem[node_id]["population"] = population_all[-1]
        evolver_mem[node_id]["fitness"] = fitness_all[-1]

    def evolve(self):
        population_all = []
        fitness_all = []
        info = "Evolver Runned"
        goal_achieved = False
        iterations = self.node.iterations
        mode = self.node.mode
        max_time = self.node.max_time
        use_fitness_goal = self.node.use_fitness_goal
        goal = self.node.fitness_goal

        for iteration in range(iterations - 1):
            self.evaluate_fitness_g()
            self.population_g.sort(key=lambda x: x.fitness, reverse=(mode == "MAX"))
            population_all.append(self.population_genes())
            actual_population_fitenss = self.population_fitness()
            fitness_all.append(actual_population_fitenss)

            if use_fitness_goal and self.goal_achieved(actual_population_fitenss[0], mode, goal):
                goal_achieved = True
                info = "goal achieved in %s iterations" % (iteration + 1)
                print(info)
                break

            self.print_time_info(iteration)
            if (time.time() - self.time_start) > max_time:
                info = "Max. time reached in %s iterations" % (iteration + 1)
                print(info)
                break

            self.population_g = self.get_new_population(actual_population_fitenss, mode)


        if not goal_achieved:
            self.evaluate_fitness_g()
            self.population_g.sort(key=lambda x: x.fitness, reverse=(mode == "MAX"))
            population_all.append(self.population_genes())
            fitness_all.append(self.population_fitness())

        self.store_data(population_all, fitness_all)
        self.node.info_label = info


class SvEvolverRun(bpy.types.Operator):

    bl_idname = "node.evolver_run"
    bl_label = "Evolver Run"

    idtree: bpy.props.StringProperty(default='')
    idname: bpy.props.StringProperty(default='')

    def execute(self, context):
        tree = bpy.data.node_groups[self.idtree]
        node = bpy.data.node_groups[self.idtree].nodes[self.idname]

        if not node.inputs[0].is_linked:
            node.info_label = "Stopped - Fitness not linked"
            return {'FINISHED'}

        genotype_frame = node.genotype
        evolver_mem[node.node_id] = {}

        seed_set(node.r_seed)
        np.random.seed(node.r_seed)

        population = Population(genotype_frame, node, tree)
        population.evolve()
        update_list = make_tree_from_nodes([node.name], tree)
        do_update(update_list, tree.nodes)
        return {'FINISHED'}

def set_fittest(tree, genes, agent, update_list):
    '''sets the nodetree with the best value'''
    try:
        tree.sv_process = False
        for gene_o, gene_agent in zip(genes, agent):
            if isinstance(gene_o, GeneList):
                set_list_node(gene_o, gene_agent, tree)
            else:
                if gene_o.g_type == 'int':
                    tree.nodes[gene_o.name].int_ = gene_agent
                else:
                    tree.nodes[gene_o.name].float_ = gene_agent
        tree.sv_process = True
        do_update(update_list, tree.nodes)
    finally:
        tree.sv_process = True

class SvEvolverSetFittest(bpy.types.Operator):

    bl_idname = "node.evolver_set_fittest"
    bl_label = "Evolver Run"

    idtree: bpy.props.StringProperty(default='')
    idname: bpy.props.StringProperty(default='')

    def execute(self, context):
        tree = bpy.data.node_groups[self.idtree]
        node = bpy.data.node_groups[self.idtree].nodes[self.idname]
        data = evolver_mem[node.node_id]
        genes = data["genes"]
        population = data["population"]
        update_list = make_tree_from_nodes([g.name for g in genes], tree)
        set_fittest(tree, genes, population[0], update_list)
        return {'FINISHED'}

def get_framenodes(base_node, _):

    items = [
        ('All', "All", "Use all 'A number' nodes. Create Frame around 'A Number' nodes the restrict genotype", 0),

    ]

    tree = base_node.id_data

    for node in tree.nodes:
        if node.bl_idname == 'NodeFrame':
            items.append((node.name, node.name, "Use Number nodes inside %s as genotype" % node.name, len(items)))
    return items

class SvEvolverNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Genetics algorithm
    Tooltip: Advanced node to find the best solution to a defined problem using a genetics algorithm technic
    """
    bl_idname = 'SvEvolverNode'
    bl_label = 'Evolver'
    bl_icon = 'RNA'

    def props_changed(self, context):
        if self.node_id in evolver_mem:
            self.info_label = "Props changed since execution"
    def props_changed_and_update(self, context):
        if self.node_id in evolver_mem:
            self.info_label = "Props changed since execution"
        updateNode(self, context)

    output_all: BoolProperty(
        name="Output all iterations",
        description="Output all iterations data or just last generation",
        default=False,
        update=updateNode
        )
    genotype: EnumProperty(
        name="Genotype",
        description="Define frame containing genotype or use all number nodes",
        items=get_framenodes,
        update=props_changed
        )
    mode_items = [
        ('MAX', 'Maximum', '', 0),
        ('MIN', 'Minimum', '', 1),
        ]
    mode: EnumProperty(
        name="Mode",
        description="Set Fitness as maximun or as minimum",
        items=mode_items,
        update=props_changed
        )
    population_n: IntProperty(
        default=20,
        name='Population amount', description='Number of agents',
        update=props_changed)
    iterations: IntProperty(
        default=1,
        min=1,
        name='Iterations', description='Iterations',
        update=props_changed)

    r_seed: IntProperty(
        default=1,
        min=1,
        name='Random Seed', description='Random Seed',
        update=props_changed)

    mutation: FloatProperty(
        name="Mutation",
        description="Mutation Factor",
        default=0.01,
        min=0,
        update=props_changed
    )
    fitness_goal: FloatProperty(
        name="Goal",
        description="Stop if fitness achieves or improves this value",
        default=0.01,
        update=props_changed
    )
    use_fitness_goal: BoolProperty(
        name="Stop on Goal",
        description="Stop evolving if defined value is achieved or improved",
        default=False,
        update=props_changed_and_update
        )
    fitness_booster: IntProperty(
        name="Fitness boost",
        description="Fittest population will be more probable to be choosen (power)",
        default=3,
        min=1,
        update=props_changed
    )

    max_time: IntProperty(
        default=10,
        min=1,
        name='Max Seconds', description='Maximum execution Time',
        update=props_changed)

    info_label: StringProperty(default="Not Executed")

    def sv_init(self, context):
        self.width = 200
        self.inputs.new('SvStringsSocket', 'Fitness')
        self.outputs.new('SvStringsSocket', 'Genes')
        self.outputs.new('SvStringsSocket', 'Population')
        self.outputs.new('SvStringsSocket', 'Fitness')


    def draw_buttons(self, context, layout):
        layout.label(text=self.info_label)
        genotype_row = layout.split(factor=0.4, align=False)
        genotype_row.label(text="Genotype:")
        genotype_row.prop(self, "genotype", text="")
        mode_row = layout.split(factor=0.4, align=False)
        mode_row.label(text="Mode:")
        mode_row.prop(self, "mode", text="")
        layout.prop(self, "population_n")
        layout.prop(self, "iterations")
        layout.prop(self, "r_seed")
        layout.prop(self, "fitness_booster")
        layout.prop(self, "mutation")
        layout.prop(self, "max_time")
        if self.use_fitness_goal:
            goal_row = layout.row(align=True)
            goal_row.prop(self, "use_fitness_goal", text="")
            goal_row.prop(self, "fitness_goal")
        else:
            layout.prop(self, "use_fitness_goal")
        self.wrapper_tracked_ui_draw_op(layout, "node.evolver_run", icon='RNA', text="RUN")
        if self.node_id in evolver_mem:
            self.wrapper_tracked_ui_draw_op(layout, "node.evolver_set_fittest", icon='RNA_ADD', text="Set Fittest")
            layout.prop(self, "output_all")

    def process(self):



        if self.node_id in evolver_mem and 'genes' in evolver_mem[self.node_id]:
            outputs = self.outputs
            outputs['Genes'].sv_set(evolver_mem[self.node_id]['genes'])
            if self.output_all:
                outputs['Population'].sv_set(evolver_mem[self.node_id]['population_all'])
                outputs['Fitness'].sv_set(evolver_mem[self.node_id]['fitness_all'])
            else:
                outputs['Population'].sv_set([evolver_mem[self.node_id]['population']])
                outputs['Fitness'].sv_set([evolver_mem[self.node_id]['fitness']])
        else:
            self.info_label = "Not Executed"
            for s in self.outputs:
                s.sv_set([])






classes = [SvEvolverRun, SvEvolverSetFittest, SvEvolverNode]
register, unregister = bpy.utils.register_classes_factory(classes)
