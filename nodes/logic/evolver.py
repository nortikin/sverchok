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

Gene = namedtuple('Gene', 'name g_type, min_n, max_n, range, init_val')

evolver_mem = {}

def is_valid_node(node, genotype_frame):
    if genotype_frame == 'All' and node.bl_idname == "SvNumberNode":
        return True
    if node.parent and node.parent.name == genotype_frame and node.bl_idname == "SvNumberNode":
        return True
    return False

def get_genes(target_tree, genotype_frame):
    genes = []
    for node in target_tree.nodes:
        if is_valid_node(node, genotype_frame):
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
            genes.append(gene)
    return genes

class DNA:
    genes_def = []
    genes = []
    fitness = 0
    def __init__(self, genes_def, random_val=True, empty=False):
        self.genes_def = genes_def
        self.genes = []
        self.fitness = 0
        if empty:
            return
        if random_val:
            for gene in genes_def:
                agent_gene = gene.min_n + random() * gene.range
                if gene.g_type == 'int':
                    agent_gene = int(agent_gene)
                self.genes.append(agent_gene)
        else:
            for gene in genes_def:
                agent_gene = gene.init_val
                self.genes.append(agent_gene)

    def evaluate_fitness(self, tree, update_list, node):
        tree.sv_process = False
        for gen_data, agent_gene in zip(self.genes_def, self.genes):
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
        # return agent_fitness
    def cross_over(self, other_ancestor, mutation):
        # new_agent = []
        new_agent = DNA(self.genes_def, empty=True)
        for g, g1, o_gene in zip(self.genes, other_ancestor.genes, self.genes_def):
            if random() < mutation:
                if random() < 0.5:
                    #total gene reset
                    new_gene = o_gene.min_n + random() * o_gene.range
                else:
                    #small gene mutation
                    fp1 = random()
                    mut = (random() - 0.5) * o_gene.range * mutation
                    new_gene = max(min((g*fp1 + g1*(1-fp1)) + mut, o_gene.max_n), o_gene.min_n)

            else:
                fp1 = random()
                new_gene = (g * fp1 + g1 * (1 - fp1))

            if o_gene.g_type == 'int':
                new_gene = int(new_gene)
            new_agent.genes.append(new_gene)

        return new_agent

class Population:
    population_g = []

    def __init__(self, genes_def, node, tree):
        self.node = node
        self.node_id = node.node_id
        self.tree = tree
        self.iterations = node.iterations
        self.mode = node.mode
        self.mutation = node.mutation
        self.fitness_booster = node.fitness_booster
        self.time_start = time.time()
        self.max_time = node.max_time
        self.genes = genes_def
        self.use_fitness_goal = node.use_fitness_goal
        self.fitness_goal = node.fitness_goal
        self.fitness_v = []
        self.population_g = []
        self.population_g.append(DNA(genes_def, random_val=False))
        for i in range(node.population_n-1):
            self.population_g.append(DNA(genes_def))

    def  evaluate_fitness_g(self, update_list):
        try:
            for agent in self.population_g:
                agent.evaluate_fitness(self.tree, update_list, self.node)
        finally:
            self.tree.sv_process = True
    def population_genes(self):
        return [agent.genes for agent in self.population_g]

    def population_fitness(self):
        return [agent.fitness for agent in self.population_g]

    def get_new_population(self, fitness):
        '''Crossover and mutation of previous population to create the new population'''
        if self.mode == 'MAX':
            weights = np.power(np.array(fitness), self.fitness_booster)
        else:
            weights = 1/np.power(np.array(fitness), self.fitness_booster)
        weights = weights/np.sum(weights)

        parents_id = np.random.choice(len(self.population_g), [len(self.population_g)-1, 2], replace=True, p=weights)
        # we keep the fittest for the next generation
        new_population = [self.population_g[0]]
        for ancestors in  parents_id:
            p0 = self.population_g[ancestors[0]]
            p1 = self.population_g[ancestors[1]]
            new_agent = p0.cross_over(p1, self.mutation)
            new_population.append(new_agent)

        return new_population

    def print_time_info(self, iteration):
        print("evolver in %s iteration" % (iteration + 1))
        print("evolver was %s seconds processing" % (time.time() - self.time_start))

    def goal_achieved(self, fittest):
        if self.mode == "MAX":
            return fittest > self.fitness_goal
        if self.mode == "MIN":
            return fittest < self.fitness_goal

    def store_data(self, population_all, fitness_all):
        evolver_mem[self.node_id]["population_all"] = population_all
        evolver_mem[self.node_id]["fitness_all"] = fitness_all
        evolver_mem[self.node_id]["genes"] = self.genes
        evolver_mem[self.node_id]["population"] = population_all[-1]
        evolver_mem[self.node_id]["fitness"] = fitness_all[-1]

    def evolve(self, update_list):
        population_all = []
        fitness_all = []
        info = "Evolver Runned"
        goal_achieved = False
        for i in range(self.iterations - 1):
            self.evaluate_fitness_g(update_list)
            self.population_g.sort(key=lambda x: x.fitness, reverse=(self.mode == "MAX"))
            population_all.append(self.population_genes())
            actual_population_fitenss = self.population_fitness()
            fitness_all.append(actual_population_fitenss)

            if self.use_fitness_goal and self.goal_achieved(actual_population_fitenss[0]):
                goal_achieved = True
                info = "goal achieved in %s iterations" % (i + 1)
                print(info)
                break

            self.print_time_info(i)
            if (time.time() - self.time_start) > self.max_time:
                info = "Max. time reached in %s iterations" % (i + 1)
                print(info)
                break

            self.population_g = self.get_new_population(actual_population_fitenss)


        if not goal_achieved:
            self.evaluate_fitness_g(update_list)
            self.population_g.sort(key=lambda x: x.fitness, reverse=(self.mode == "MAX"))
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

        genes = get_genes(tree, genotype_frame)
        update_list = make_tree_from_nodes([g.name for g in genes], tree)
        population = Population(genes, node, tree)
        population.evolve(update_list)
        update_list = make_tree_from_nodes([node.name], tree)
        do_update(update_list, tree.nodes)
        return {'FINISHED'}

def set_fittest(tree, genes, agent, update_list):
    '''sets the nodetree with the best value'''
    try:
        tree.sv_process = False
        for gene_o, gene_agent in zip(genes, agent):
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
