'''
    The following code is mainly adopted from PM4Py (More Info: https://pm4py.fit.fraunhofer.de).
    Changes relate to the support for reset/inhibitor nets.

    PM4Py is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    PM4Py is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with PM4Py.  If not, see <https://www.gnu.org/licenses/>.
'''
from collections import Counter
from copy import deepcopy
from enum import Enum


class Marking(Counter):
    pass

    def __hash__(self):
        r = 0
        for p in self.items():
            r += 31 * hash(p[0]) * p[1]
        return r

    def __eq__(self, other):
        if not self.keys() == other.keys():
            return False
        for p in self.keys():
            if other.get(p) != self.get(p):
                return False
        return True

    def __le__(self, other):
        if not self.keys() <= other.keys():
            return False
        for p in self.keys():
            if other.get(p) < self.get(p):
                return False
        return True

    def __add__(self, other):
        m = Marking()
        for p in self.items():
            m[p[0]] = p[1]
        for p in other.items():
            m[p[0]] += p[1]
        return m

    def __sub__(self, other):
        m = Marking()
        for p in self.items():
            m[p[0]] = p[1]
        for p in other.items():
            m[p[0]] -= p[1]
            if m[p[0]] == 0:
                del m[p[0]]
        return m

    def __repr__(self):
        # return str([str(p.name) + ":" + str(self.get(p)) for p in self.keys()])
        # The previous representation had a bug, it took into account the order of the places with tokens
        return str([str(p.name) + ":" + str(self.get(p)) for p in sorted(list(self.keys()), key=lambda x: x.name)])

    def __deepcopy__(self, memodict={}):
        marking = Marking()
        memodict[id(self)] = marking
        for place in self:
            place_occ = self[place]
            new_place = memodict[id(place)] if id(place) in memodict else PetriNet.Place(place.name,
                                                                                         properties=place.properties)
            marking[new_place] = place_occ
        return marking


class PetriNet(object):

    class Place(object):

        def __init__(self, name, in_arcs=None, out_arcs=None, properties=None):
            self.__name = name
            self.__in_arcs = set() if in_arcs is None else in_arcs
            self.__out_arcs = set() if out_arcs is None else out_arcs
            self.__properties = dict() if properties is None else properties
            self.ass_trans = set()

        def __getstate__(self):
            # dump a tuple instead of a set so that the __hash__ function won't be called
            return tuple([self.__name, self.__properties, list(self.ass_trans)])

        def __setstate__(self, state):
            self.__name = state[0]
            self.__in_arcs = set()
            self.__out_arcs = set()
            self.__properties = state[1]
            self.ass_trans = set(state[2])

        def __set_name(self, name):
            self.__name = name

        def __get_name(self):
            return self.__name

        def __get_out_arcs(self):
            return self.__out_arcs

        def __get_in_arcs(self):
            return self.__in_arcs

        def __get_properties(self):
            return self.__properties

        def __repr__(self):
            return str(self.__name)

        def __eq__(self, other):
            # keep the ID for now in places
            return hash(self) == hash(other)

        def __hash__(self):
            # keep the ID for now in places
            return hash(str(self.__name))

        def __deepcopy__(self, memodict={}):
            if id(self) in memodict:
                return memodict[id(self)]
            new_place = PetriNet.Place(self.__name, properties=self.properties)
            memodict[id(self)] = new_place
            for arc in self.in_arcs:
                new_arc = deepcopy(arc, memo=memodict)
                new_place.in_arcs.add(new_arc)
            for arc in self.out_arcs:
                new_arc = deepcopy(arc, memo=memodict)
                new_place.out_arcs.add(new_arc)
            return new_place

        name = property(__get_name, __set_name)
        in_arcs = property(__get_in_arcs)
        out_arcs = property(__get_out_arcs)
        properties = property(__get_properties)

    class Transition(object):

        def __init__(self, name, label=None, in_arcs=None, out_arcs=None, properties=None):
            self.__name = name
            self.__label = None if label is None else label
            self.__in_arcs = set() if in_arcs is None else in_arcs
            self.__out_arcs = set() if out_arcs is None else out_arcs
            self.__properties = dict() if properties is None else properties
            self.add_marking = Marking()
            self.sub_marking = Marking()

        def __getstate__(self):
            # dump a tuple instead of a set so that the __hash__ function won't be called
            return tuple([self.__name, self.__label, self.__properties, self.add_marking, self.sub_marking])

        def __setstate__(self, state):
            self.__name = state[0]
            self.__label = state[1]
            self.__in_arcs = set()
            #for arc in state[1]:
            #    arc.target = self
            #    self.in_arcs.add(arc)
            self.__out_arcs = set()
            #for arc in state[2]:
            #    arc.source = self
            #    self.__out_arcs.add(arc)
            self.__properties = state[2]
            self.add_marking = state[3]
            self.sub_marking = state[4]

        def __set_name(self, name):
            self.__name = name

        def __get_name(self):
            return self.__name

        def __set_label(self, label):
            self.__label = label

        def __get_label(self):
            return self.__label

        def __get_out_arcs(self):
            return self.__out_arcs

        def __get_in_arcs(self):
            return self.__in_arcs

        def __get_properties(self):
            return self.__properties

        def __repr__(self):
            if self.__label is None:
                return str(self.__name)
            else:
                return str(self.__label)

        def __eq__(self, other):
            # keep the ID for now in transitions
            return hash(self) == hash(other)

        def __hash__(self):
            # keep the ID for now in transitions
            return hash(str(self.__name))

        def __deepcopy__(self, memodict={}):
            if id(self) in memodict:
                return memodict[id(self)]
            new_trans = PetriNet.Transition(self.__name, self.__label, properties=self.__properties)
            memodict[id(self)] = new_trans
            for arc in self.__in_arcs:
                new_arc = deepcopy(arc, memo=memodict)
                new_trans.in_arcs.add(new_arc)
            for arc in self.__out_arcs:
                new_arc = deepcopy(arc, memo=memodict)
                new_trans.out_arcs.add(new_arc)
            return new_trans

        name = property(__get_name, __set_name)
        label = property(__get_label, __set_label)
        in_arcs = property(__get_in_arcs)
        out_arcs = property(__get_out_arcs)
        properties = property(__get_properties)

    class Arc(object):

        def __init__(self, source, target, weight=1, properties=None):
            if type(source) is type(target):
                raise Exception('Petri nets are bipartite graphs!')
            self.__source = source
            self.__target = target
            self.__weight = weight
            self.__properties = dict() if properties is None else properties

        def __getstate__(self):
            # dump a tuple instead of a set so that the __hash__ function won't be called
            return tuple([self.__source, self.__target, self.__weight, self.__properties])

        def __setstate__(self, state):
            self.__source = state[0]
            self.__target = state[1]
            self.__weight = state[2]
            self.__properties = state[3]
            self.__source.out_arcs.add(self)
            self.__target.in_arcs.add(self)


        def __get_source(self):
            return self.__source

        def __set_source(self, source):
            self.__source = source

        def __get_target(self):
            return self.__target

        def __set_target(self, target):
            self.__target = target

        def __set_weight(self, weight):
            self.__weight = weight

        def __get_weight(self):
            return self.__weight

        def __get_properties(self):
            return self.__properties

        def __set_properties(self, properties):
            self.__properties = properties

        def __repr__(self):
            if type(self.__source) is PetriNet.Transition:
                if self.__source.label:
                    return "(t)" + str(self.__source.label) + "->" + "(p)" + str(self.__target.name)
                else:
                    return "(t)" + str(self.__source.name) + "->" + "(p)" + str(self.__target.name)
            if type(self.__target) is PetriNet.Transition:
                if self.__target.label:
                    return "(p)" + str(self.__source.name) + "->" + "(t)" + str(self.__target.label)
                else:
                    return "(p)" + str(self.__source.name) + "->" + "(t)" + str(self.__target.name)


        def __hash__(self):
            return (hash(self.__source) + hash(self.__target)) % 479001599

        def __eq__(self, other):
            return self.__source == other.source and self.__target == other.target

        def __deepcopy__(self, memodict={}):
            if id(self) in memodict:
                return memodict[id(self)]
            new_source = memodict[id(self.source)] if id(self.source) in memodict else deepcopy(self.source,
                                                                                                memo=memodict)
            new_target = memodict[id(self.target)] if id(self.target) in memodict else deepcopy(self.target,
                                                                                                memo=memodict)
            memodict[id(self.source)] = new_source
            memodict[id(self.target)] = new_target
            new_arc = PetriNet.Arc(new_source, new_target, weight=self.weight, properties=self.properties)
            memodict[id(self)] = new_arc
            return new_arc

        source = property(__get_source, __set_source)
        target = property(__get_target, __set_target)
        weight = property(__get_weight, __set_weight)
        properties = property(__get_properties, __set_properties)

    def __init__(self, name=None, places=None, transitions=None, arcs=None, properties=None):
        self.__name = "" if name is None else name
        self.__places = set() if places is None else places
        self.__transitions = set() if transitions is None else transitions
        self.__arcs = set() if arcs is None else arcs
        self.__properties = dict() if properties is None else properties

    def __get_name(self):
        return self.__name

    def __set_name(self, name):
        self.__name = name

    def __get_places(self):
        return self.__places

    def __get_transitions(self):
        return self.__transitions

    def __get_arcs(self):
        return self.__arcs

    def __get_properties(self):
        return self.__properties

    def __hash__(self):
        ret = 0
        for p in self.__places:
            ret += hash(p)
            ret = ret % 479001599
        for t in self.__transitions:
            ret += hash(t)
            ret = ret % 479001599
        return ret

    def __eq__(self, other):
        # for the Petri net equality keep the ID for now
        return id(self) == id(other)

    def __deepcopy__(self, memodict={}):
        from procon.objects.petri_net.utils import add_arc_from_to
        this_copy = PetriNet(self.name)
        memodict[id(self)] = this_copy
        for place in self.places:
            place_copy = PetriNet.Place(place.name, properties=place.properties)
            this_copy.places.add(place_copy)
            memodict[id(place)] = place_copy
        for trans in self.transitions:
            trans_copy = PetriNet.Transition(trans.name, trans.label, properties=trans.properties)
            this_copy.transitions.add(trans_copy)
            memodict[id(trans)] = trans_copy
        for arc in self.arcs:
            add_arc_from_to(memodict[id(arc.source)], memodict[id(arc.target)], this_copy, weight=arc.weight, properties=arc.properties)
        return this_copy

    name = property(__get_name, __set_name)
    places = property(__get_places)
    transitions = property(__get_transitions)
    arcs = property(__get_arcs)
    properties = property(__get_properties)
