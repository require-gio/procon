'''
    The following code owned by Procon and its author (More Info: https://github.com/require-gio/procon).

    Procon is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Procon is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Procon.  If not, see <https://www.gnu.org/licenses/>.
'''
from procon.objects.petri_net.obj import PetriNet
from procon.objects.petri_net.utils import remove_arc, remove_transition, remove_place, add_arc_from_to, normal_pre_set, normal_post_set, \
    is_reset_arc, is_normal_arc, is_inhibitor_arc, add_reset_arc_from_to, add_inhibitor_arc_from_to, reset_pre_set, reset_post_set, inhibitor_post_set, \
        inhibitor_pre_set
from copy import copy
import itertools
from itertools import combinations, chain



def apply_fst_rule(net):
    """
    Apply the Fusion of Series Transitions (FST) rule

    Parameters
    --------------
    net
        Reset Inhibitor net
    """
    cont = True
    while cont:
        cont = False
        for p, t, u in itertools.product(net.places, net.transitions, net.transitions):
            if (len(list(p.in_arcs)) == 1 and list(p.in_arcs)[0].source == t) and \
                (len(list(p.out_arcs)) == 1 and list(p.out_arcs)[0].target == u) and \
                (len(list(u.in_arcs)) == 1 and list(u.in_arcs)[0].source == p) and \
                (len(normal_post_set(t).intersection(normal_post_set(u))) == 0) and \
                (set().union(*[inhibitor_post_set(place) for place in normal_post_set(u)]) == inhibitor_post_set(p)) and \
                (set().union(*[reset_post_set(place) for place in normal_post_set(u)]) == reset_post_set(p)) and \
                (len(reset_pre_set(u)) == 0 and len(inhibitor_pre_set(u)) == 0):
                if u.label == None:
                    remove_place(net, p)
                    for target in normal_post_set(u):
                        add_arc_from_to(t, target, net)
                    remove_transition(net, u)
                    cont = True
                    break
    
    return net


def apply_fsp_rule(net, im={}, fm={}):
    """
    Apply the Fusion of Series Places (FSP) rule

    Parameters
    --------------
    net
        Reset Inhibitor net
    """
    cont = True
    while cont:
        cont = False
        for p, q, t in itertools.product(net.places, net.places, net.transitions):
            if t.label == None: # only silent transitions may be removed either way
                if (len(t.in_arcs) == 1 and list(t.in_arcs)[0].source == p) and \
                    (len(t.out_arcs) == 1 and list(t.out_arcs)[0].target == q) and \
                    (len(normal_post_set(p)) == 1 and list(normal_post_set(p))[0] == t) and \
                    (len(normal_pre_set(p).intersection(normal_pre_set(q))) == 0) and \
                    (reset_post_set(p) == reset_post_set(q)) and \
                    (inhibitor_post_set(p) == inhibitor_post_set(q)) and \
                    (len(reset_pre_set(t)) == 0 and len(inhibitor_pre_set(t)) == 0):
                    # remove place p and transition t
                    remove_transition(net, t)
                    for source in normal_pre_set(p):
                        add_arc_from_to(source, q, net)
                    remove_place(net, p)
                    if p in im:
                        del im[p]
                        im[q] = 1
                    cont = True
                    break

    return net, im, fm


def apply_fpt_rule(net):
    """
    Apply the Fusion of Parallel Transitions (FPT) rule

    Parameters
    --------------
    net
        Reset Inhibitor net
    """
    cont = True
    while cont:
        cont = False
        for V in power_set([transition for transition in net.transitions if transition.label == None], 2):
            condition = True
            for x, y in itertools.product(V, V):
                if x != y:
                    if not ((normal_pre_set(x) == normal_pre_set(y)) and \
                        (normal_post_set(x) == normal_post_set(y)) and \
                        (reset_pre_set(x) == reset_pre_set(y)) and \
                        (inhibitor_pre_set(x) == inhibitor_pre_set(y))):
                        condition = False
                        break
            # V is a valid candidate
            if condition:
                # remove transitions except the first one
                for t in V[1:]:
                    remove_transition(net, t)
                cont = True
                break
    return net


def apply_fpp_rule(net, im={}):
    """
    Apply the Fusion of Parallel Places (FPP) rule

    Parameters
    --------------
    net
        Reset Inhibitor net
    """
    cont = True
    while cont:
        cont = False
        for Q in power_set(net.places, 2):
            condition = True
            for x, y in itertools.product(Q, Q):
                if x != y:
                    if not ((normal_pre_set(x) == normal_pre_set(y)) and \
                        (normal_post_set(x) == normal_post_set(y)) and \
                        (reset_post_set(x) == reset_post_set(y)) and \
                        (inhibitor_post_set(x) == inhibitor_post_set(y))):
                        condition = False
                        break

            for x in Q:
                if x in im:
                    for y in Q:
                        if y in im and im[x] > im[y]:
                            if not (len(inhibitor_post_set(x)) == 0):
                                condition = False
                                break
                    else:
                        continue
                    break
            # Q is a valid candidate
            if condition:
                # remove places except the first one
                for p in Q[1:]:
                    remove_place(net, p)
                cont = True
                break
    return net


def apply_elt_rule(net):
    """
    Apply the Elimination of Self-Loop Transitions (ELT) rule

    Parameters
    --------------
    net
        Reset Inhibitor net
    """
    cont = True
    while cont:
        cont = False
        for p, t in itertools.product(net.places, [t for t in net.transitions if t.label == None]):
            if (len(list(t.in_arcs)) == 1 and list(t.in_arcs)[0].source == p) and \
                (len(list(t.out_arcs)) == 1 and list(t.out_arcs)[0].target == p) and \
                (len(list(p.in_arcs)) >= 2) and \
                (len(reset_pre_set(t)) == 0 and len(inhibitor_pre_set(t)) == 0):
                    remove_transition(net, t)
                    cont = True
                    break
    
    return net



def apply_elp_rule(net, im={}):
    """
    Apply the Elimination of Self-Loop Places (ELP) rule

    Parameters
    --------------
    net
        Reset Inhibitor net
    """
    cont = True
    while cont:
        cont = False
        for p in [place for place in net.places]:
            if (set([arc.target for arc in p.out_arcs]).issubset(set([arc.source for arc in p.in_arcs]))) and \
                (p in im and im[p] >= 1) and \
                (reset_post_set(p).union(set([arc.target for arc in p.out_arcs])) == set([arc.source for arc in p.in_arcs])) and \
                (len(inhibitor_post_set(p)) == 0):
                remove_place(net, p)
                cont = True
                break
    
    return net


def apply_a_rule(net):
    """
    Apply the Abstraction (A) rule

    Parameters
    --------------
    net
        Reset Inhibitor net
    """
    cont = True
    while cont:
        cont = False
        for Q, U in itertools.product(power_set(net.places, 1), power_set(net.transitions, 1)):
            for s, t in itertools.product([s for s in net.places if s not in Q], [t for t in net.transitions if (t not in U) and (t.label == None)]):
                if ((normal_pre_set(t) == {s}) and \
                    (normal_post_set(s) == {t}) and \
                    (normal_pre_set(s) == set(U)) and \
                    (normal_post_set(t) == set(Q)) and \
                    (len(set(itertools.product(normal_pre_set(s), normal_post_set(t))).intersection(set([(arc.source, arc.target) for arc in net.arcs if is_normal_arc(arc)])))) == 0) and \
                    (len(reset_pre_set(t)) == 0) and \
                    (len(inhibitor_pre_set(t)) == 0):

                    # check conditions on Q
                    condition = True
                    for q in Q:
                        if not ((reset_post_set(s) == reset_post_set(q)) and \
                        (inhibitor_post_set(s) == inhibitor_post_set(q))):
                            condition = False
                            break
                    # Q is a valid candidate
                    if condition:
                        for u in U:
                            for q in Q:
                                add_arc_from_to(u, q, net)
                        remove_place(net, s)
                        remove_transition(net, t)
                        cont = True
                        break
    return net


def apply_r_rule(net):
    """
    Apply the Reset Reduction (R) rule

    Parameters
    --------------
    net
        Reset Inhibitor net
    """
    cont = True
    while cont:
        cont = False
        for p, t in itertools.product(net.places, net.transitions):
            if p in reset_pre_set(t).intersection(inhibitor_pre_set(t)):
                for arc in [arc for arc in net.arcs]:
                    if arc.source == p and arc.target == t and is_reset_arc(arc):
                        remove_arc(net, arc)
                cont = True
                break
    
    return net


def power_set(iterable, min=0):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(min, len(s)+1))


def apply_reset_inhibitor_net_reduction(net, im={}, fm={}):
    """
    Apply a thorough reduction to the Reset Inhibitor net

    Parameters
    --------------
    net
        Reset Inhibitor net
    """
    apply_fst_rule(net)
    apply_fsp_rule(net, im, fm)
    # (FPT) rule is exponential to model size
    # apply_fpt_rule(net)
    # (FPP) rule is exponential to model size
    # apply_fpp_rule(net, im)
    apply_elt_rule(net)
    apply_elp_rule(net, im)
    # (A) rule is exponential to model size
    # apply_a_rule(net)
    apply_r_rule(net)
    return net, im, fm