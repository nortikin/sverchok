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

import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix
from math import radians
from bpy.props import (
    BoolProperty, FloatVectorProperty, StringProperty, EnumProperty, IntProperty, FloatProperty
)
from sverchok.node_tree import SverchCustomTreeNode, SverchCustomTree
from sverchok.data_structure import dataCorrect, updateNode
from sverchok.nodes.object_nodes.getsetprop import assign_data, types
from mathutils.noise import seed_set, random
import numpy as np
import time
from sverchok.core.update_system import process_from_nodes, make_tree_from_nodes, do_update
from collections import namedtuple

Gene = namedtuple('Gene', 'name g_type, min_n, max_n, range')
# can't use a PointerProperty for type=bpy.data.node_group
# https://blender.stackexchange.com/questions/2075/assign-datablock-to-custom-property
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
            else:
                min_n = node.int_min
                max_n = node.int_max
            gene = Gene(name=node.name, g_type=num_type, min_n=min_n, max_n=max_n, range=max_n-min_n)
            genes.append(gene)
    return genes

def initial_population(genes, init_pop_num):
    population =[]
    for i in range(init_pop_num):
        agent = []
        for g in genes:
            a = g.min_n + random() * g.range
            if g.g_type == 'int':
                a = int(a)
            agent.append(a)
        population.append(agent)
    return population


def evaluate_fitness(population, genes, tree, update_list, node):
    fitness = []

    for agent in population:
        tree.sv_process = False
        for g, s in zip(genes, agent):
            tree.nodes[g[0]].float_= s
        tree.sv_process = True
        do_update(update_list, tree.nodes)
        a = node.inputs[0].sv_get(deepcopy=False)[0]
        if isinstance(a, list):
            a = a[0]
        fitness.append(a)
    return fitness


def get_new_population(population, fitness, genes, mutation, fitness_booster, mode):
    if mode == 'MAX':
        weights = np.power(np.array(fitness), fitness_booster)
    else:
        weights = 1/np.power(np.array(fitness), fitness_booster)
    weights = weights/np.sum(weights)
    parents = np.random.choice(len(population), [len(population),2], replace=True, p=weights)
    new_population = []
    for ancestors in  parents:
        p0 = population[ancestors[0]]
        p1 = population[ancestors[1]]

        new_agent = []
        for g, g1, o_gene in zip(p0, p1, genes):
            if random() < mutation:
                if random() < 0.5:
                    #total gene reset
                    new_gene = o_gene.min_n + random() * o_gene.range
                else:
                    #small gene mutation
                    fp1 = random()
                    mut = (random() - 0.5) * o_gene[4]*mutation
                    new_gene = (g*fp1 + g1*(1-fp1)) + mut

            else:
                fp1 = random()
                new_gene = (g * fp1 + g1 * (1 - fp1))
                # new_gene = (g* weight0 + g1 * weight1)

            if o_gene.g_type == 'int':
                new_gene = int(new_gene)
            new_agent.append(new_gene)

        new_population.append(new_agent)

    return new_population

class SvEvolverRun(bpy.types.Operator):

    bl_idname = "node.evolver_run"
    bl_label = "Evolver Run"

    idtree: bpy.props.StringProperty(default='')
    idname: bpy.props.StringProperty(default='')

    def execute(self, context):
        tree = bpy.data.node_groups[self.idtree]
        node = bpy.data.node_groups[self.idtree].nodes[self.idname]
        genotype_frame = node.genotype
        evolver_mem[node.node_id] = {}
        seed_set(node.r_seed)
        np.random.seed(node.r_seed)
        genes = get_genes(tree, genotype_frame)
        update_list = make_tree_from_nodes([g.name for g in genes], tree)
        time_start = time.time()
        population_s = initial_population(genes, node.population_n)
        info = "Evolver Runned"

        population_all = []
        fitness_all = []
        for i in range(node.iterations-1):
            fitness = evaluate_fitness(population_s, genes, tree, update_list, node)
            population_all.append(population_s)
            fitness_all.append(fitness)
            population_s = get_new_population(population_s, fitness, genes, node.mutation, node.fitness_booster, node.mode)
            node.info_label="evolver in %s iteration" % i
            print("evolver in %s iteration" % i)
            if (time.time() - time_start) > node.max_time:
                print("maximum time reached in %s iterations" % i)
                info = "Max. time reached in %s iterations" % i
                break
        fitness = evaluate_fitness(population_s, genes, tree, update_list, node)
        population_sorted = sorted(list(zip(fitness, population_s)), reverse=node.mode == "MAX")
        # set_fittest(target_tree, genes, population_sorted[0], update_list)
        fitness_s = [l for l, a in population_sorted]
        population_s = [a for l, a in population_sorted]
        population_all.append(population_s)
        fitness_all.append(fitness_s)
        evolver_mem[node.node_id]["population_all"] = population_all
        evolver_mem[node.node_id]["fitness_all"] = fitness_all
        evolver_mem[node.node_id]["genes"] = genes
        evolver_mem[node.node_id]["population"] = population_s
        evolver_mem[node.node_id]["fitness"] = fitness_s
        # node.outputs[0].sv_set([genes])
        # node.outputs[1].sv_set([population_s])
        # node.outputs[2].sv_set([fitness_s])
        node.info_label = info
        update_list = make_tree_from_nodes([node.name], tree)
        do_update(update_list, tree.nodes)
        return {'FINISHED'}

def set_fittest(tree, genes, agent, update_list):

    tree.sv_process = False
    for gene_o, gene_agent in zip(genes, agent):
        if gene_o.g_type == 'int':
            tree.nodes[gene_o.name].int_ = gene_agent
        else:
            tree.nodes[gene_o.name].float_ = gene_agent
    tree.sv_process = True
    do_update(update_list, tree.nodes)

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

def get_framenodes(base_node, b):

    items = [
        ('All', "All", "Use all 'A number' nodes. Create Frame around Number nodes the define genotype", 0),

    ]
    # items =[]
    tree = base_node.id_data

    for node in tree.nodes:
        if node.bl_idname == 'NodeFrame':
            items.append((node.name, node.name, "Use Number nodes inside %s as genotype" % node.name, len(items)))
    return items

class SvEvolverNode(bpy.types.Node, SverchCustomTreeNode):

    bl_idname = 'SvEvolverNode'
    bl_label = 'Evolver'
    bl_icon = 'RNA'
    # sv_icon = 'RNA'

    def props_changed(self,context):
        if self.node_id in evolver_mem:
            self.info_label = "Props changed since execution"
        # updateNode(self, context)
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
    mode_items=[
        ('MAX','Maximum', '', 0),
        ('MIN','Minimum', '', 1),
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
        self.inputs.new('SvVerticesSocket', 'fitness')
        self.outputs.new('SvStringsSocket', 'Genes')
        self.outputs.new('SvStringsSocket', 'Population')
        self.outputs.new('SvStringsSocket', 'Fitness')


    def draw_buttons(self, context, layout):
        layout.label(text=self.info_label)
        layout.prop(self, "genotype")
        layout.prop(self, "mode")
        layout.prop(self, "population_n")
        layout.prop(self, "iterations")
        layout.prop(self, "r_seed")
        layout.prop(self, "fitness_booster")
        layout.prop(self, "mutation")
        layout.prop(self, "max_time")
        self.wrapper_tracked_ui_draw_op(layout, "node.evolver_run", icon='RNA', text="RUN")
        if self.node_id in evolver_mem:
            self.wrapper_tracked_ui_draw_op(layout, "node.evolver_set_fittest", icon='RNA_ADD', text="Set Fittest")
            layout.prop(self, "output_all")

    def process(self):

        # end early?

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






classes = [SvEvolverRun,SvEvolverSetFittest, SvEvolverNode]
register, unregister = bpy.utils.register_classes_factory(classes)
