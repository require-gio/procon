'''
    The following code is mainly adopted from PM4Py (More Info: https://pm4py.fit.fraunhofer.de).
    Changes relate to the support for cancellation features and advanced BPMN constructs.

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
from typing import DefaultDict
import uuid
from enum import Enum
from collections import Counter, defaultdict
import operator

DEFAULT_PROCESS = str(uuid.uuid4())


class BPMN(object):
    class BPMNNode(object):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            self.__id = ("id"+ str(uuid.uuid4())) if id == "" else id
            self.__name = name
            self.__in_arcs = list() if in_arcs is None else in_arcs
            self.__out_arcs = list() if out_arcs is None else out_arcs
            self.__x = 0
            self.__y = 0
            self.__width = 100
            self.__height = 100
            self.__process = DEFAULT_PROCESS if process == None else process

        def get_id(self):
            return self.__id

        def get_name(self):
            return self.__name

        def set_x(self, x):
            self.__x = x

        def set_y(self, y):
            self.__y = y

        def get_x(self):
            return self.__x

        def get_y(self):
            return self.__y

        def get_width(self):
            return self.__width

        def set_width(self, width):
            self.__width = width

        def get_height(self):
            return self.__height

        def set_height(self, height):
            self.__height = height

        def get_in_arcs(self):
            return self.__in_arcs

        def get_out_arcs(self):
            return self.__out_arcs

        def add_in_arc(self, in_arc):
            if in_arc not in self.__in_arcs:
                self.__in_arcs.append(in_arc)

        def add_out_arc(self, out_arc):
            if out_arc not in self.__out_arcs:
                self.__out_arcs.append(out_arc)

        def remove_in_arc(self, in_arc):
            self.__in_arcs.remove(in_arc)

        def remove_out_arc(self, out_arc):
            self.__out_arcs.remove(out_arc)

        def get_process(self):
            return self.__process

        def set_process(self, process):
            self.__process = process

        def __hash__(self):
            return hash(self.id)
        
        def __eq__(self, other):
            # keep the ID for now in places
            return hash(self) == hash(other)

        def __repr__(self):
            return str(self.__id + "@" + self.__name)

        def __str__(self):
            return self.__repr__()

        name = property(get_name)
        id = property(get_id)
        in_arcs = property(get_in_arcs)
        out_arcs = property(get_out_arcs)
        process = property(get_process, set_process)


    # event classes

    class Event(BPMNNode):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            BPMN.BPMNNode.__init__(self, id, name, in_arcs, out_arcs, process=process)



    class StartEvent(Event):
        def __init__(self, id="", isInterrupting=False, name="", parallelMultiple=False, in_arcs=None, out_arcs=None, process=None):
            BPMN.Event.__init__(self, id, name, in_arcs, out_arcs, process=process)
            self.__isInterrupting = isInterrupting
            self.__parallelMultiple = parallelMultiple

        def get_isInterrupting(self):
            return self.__isInterrupting

        def get_parallelMultiple(self):
            return self.__parallelMultiple

    class NormalStartEvent(StartEvent):
        def __init__(self, id="", isInterrupting=False, name="", parallelMultiple=False, in_arcs=None, out_arcs=None, process=None):
            BPMN.StartEvent.__init__(self, id, isInterrupting, name, parallelMultiple, in_arcs, out_arcs, process=process)

    class MessageStartEvent(StartEvent):
        def __init__(self, id="", isInterrupting=False, name="", parallelMultiple=False, in_arcs=None, out_arcs=None, process=None):
            BPMN.StartEvent.__init__(self, id, isInterrupting, name, parallelMultiple, in_arcs, out_arcs, process=process)



    class IntermediateCatchEvent(Event): 
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            BPMN.Event.__init__(self, id, name, in_arcs, out_arcs, process=process)

    class MessageIntermediateCatchEvent(IntermediateCatchEvent):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            BPMN.IntermediateCatchEvent.__init__(self, id, name, in_arcs, out_arcs, process=process)

    class ErrorIntermediateCatchEvent(IntermediateCatchEvent):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            BPMN.IntermediateCatchEvent.__init__(self, id, name, in_arcs, out_arcs, process=process)

    class CancelIntermediateCatchEvent(IntermediateCatchEvent):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            BPMN.IntermediateCatchEvent.__init__(self, id, name, in_arcs, out_arcs, process=process)



    class BoundaryEvent(Event): 
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None, activity=None):
            self.__activity = activity
            BPMN.Event.__init__(self, id, name, in_arcs, out_arcs, process=process)
        
        def get_activity(self):
            return self.__activity

    class MessageBoundaryEvent(BoundaryEvent):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None, activity=None):
            BPMN.BoundaryEvent.__init__(self, id, name, in_arcs, out_arcs, process=process, activity=activity)

    class ErrorBoundaryEvent(BoundaryEvent):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None, activity=None):
            BPMN.BoundaryEvent.__init__(self, id, name, in_arcs, out_arcs, process=process, activity=activity)

    class CancelBoundaryEvent(BoundaryEvent):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None, activity=None):
            BPMN.BoundaryEvent.__init__(self, id, name, in_arcs, out_arcs, process=process, activity=activity)



    class IntermediateThrowEvent(Event): 
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            BPMN.Event.__init__(self, id, name, in_arcs, out_arcs, process=process)

    class MessageIntermediateThrowEvent(IntermediateThrowEvent):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            BPMN.IntermediateThrowEvent.__init__(self, id, name, in_arcs, out_arcs, process=process)

    class NormalIntermediateThrowEvent(IntermediateThrowEvent):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            BPMN.IntermediateThrowEvent.__init__(self, id, name, in_arcs, out_arcs, process=process)



    class EndEvent(Event):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            BPMN.Event.__init__(self, id, name, in_arcs, out_arcs, process=process)

    class NormalEndEvent(EndEvent):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            BPMN.EndEvent.__init__(self, id, name, in_arcs, out_arcs, process=process)
        
    class MessageEndEvent(EndEvent):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            BPMN.EndEvent.__init__(self, id, name, in_arcs, out_arcs, process=process)

    class TerminateEndEvent(EndEvent):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            BPMN.EndEvent.__init__(self, id, name, in_arcs, out_arcs, process=process)

    class ErrorEndEvent(EndEvent):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            BPMN.EndEvent.__init__(self, id, name, in_arcs, out_arcs, process=process)
    
    class CancelEndEvent(EndEvent):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            BPMN.EndEvent.__init__(self, id, name, in_arcs, out_arcs, process=process)



    # activity node classes

    class Activity(BPMNNode):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            BPMN.BPMNNode.__init__(self, id, name, in_arcs, out_arcs, process=process)

    class Task(Activity):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
            BPMN.Activity.__init__(self, id, name, in_arcs, out_arcs, process=process)

    class SubProcess(Activity):
        def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None, depth=None):
            self.__depth = depth
            BPMN.Activity.__init__(self, id, name, in_arcs, out_arcs, process=process)

        def get_depth(self):
            return self.__depth

    # class CollapsedSubProcess(Activity):
    #    def __init__(self, id="", name="", in_arcs=None, out_arcs=None, process=None):
    #        BPMN.Activity.__init__(self, id, name, in_arcs, out_arcs, process=process)

    # gateway classes

    class Gateway(BPMNNode):
        class Direction(Enum):
            UNSPECIFIED = "Unspecified"
            DIVERGING = "Diverging"
            CONVERGING = "Converging"

        def __init__(self, id="", name="", gateway_direction=Direction.UNSPECIFIED, in_arcs=None, out_arcs=None, process=None):
            BPMN.BPMNNode.__init__(self, id, name, in_arcs, out_arcs, process=process)
            self.__gateway_direction = gateway_direction

        def get_gateway_direction(self):
            return self.__gateway_direction

    class ParallelGateway(Gateway):
        def __init__(self, id="", name="", gateway_direction=None, in_arcs=None, out_arcs=None, process=None):
            gateway_direction = gateway_direction if gateway_direction is not None else BPMN.Gateway.Direction.UNSPECIFIED
            BPMN.Gateway.__init__(self, id, name, gateway_direction, in_arcs, out_arcs, process=process)
        
    class ExclusiveGateway(Gateway):
        def __init__(self, id="", name="", gateway_direction=None, in_arcs=None, out_arcs=None, process=None):
            gateway_direction = gateway_direction if gateway_direction is not None else BPMN.Gateway.Direction.UNSPECIFIED
            BPMN.Gateway.__init__(self, id, name, gateway_direction, in_arcs, out_arcs, process=process)

    class InclusiveGateway(Gateway):
        def __init__(self, id="", name="", gateway_direction=None, in_arcs=None, out_arcs=None, process=None):
            gateway_direction = gateway_direction if gateway_direction is not None else BPMN.Gateway.Direction.UNSPECIFIED
            BPMN.Gateway.__init__(self, id, name, gateway_direction, in_arcs, out_arcs, process=process)

    # flow (arc) classes

    class Flow(object):

        def __init__(self, source, target, id="", name="", process=None):
            self.__id = uuid.uuid4() if id == "" else id
            self.__name = name
            self.__source = source
            source.add_out_arc(self)
            self.__target = target
            target.add_in_arc(self)
            self.__waypoints = list()
            self.__waypoints.append((source.get_x(), source.get_y()))
            self.__waypoints.append((target.get_x(), target.get_y()))
            self.__process = DEFAULT_PROCESS if process == None else process

        def get_id(self):
            return self.__id

        def get_name(self):
            return self.__name

        def get_source(self):
            return self.__source

        def get_target(self):
            return self.__target

        def add_waypoint(self, waypoint):
            self.__waypoints.append(waypoint)

        def del_waypoints(self):
            self.__waypoints = list()

        def get_waypoints(self):
            return self.__waypoints

        def get_process(self):
            return self.__process

        def set_process(self, process):
            self.__process = process

        def __repr__(self):
            u_id = str(self.__source.get_id()) + "@" + str(self.__source.get_name())
            v_id = str(self.__target.get_id()) + "@" + str(self.__target.get_name())
            return u_id + " -> " + v_id

        def __str__(self):
            return self.__repr__()

        source = property(get_source)
        target = property(get_target)
    
    class SequenceFlow(Flow):
        def __init__(self, source, target, id="", name="", process=None):
            BPMN.Flow.__init__(self, source, target, id=id, name=name, process=process)
    
    class MessageFlow(Flow):
        def __init__(self, source, target, id="", name="", process=None):
            BPMN.Flow.__init__(self, source, target, id=id, name=name, process=process)


    def __init__(self, process_id=None, name="", nodes=None, flows=None):
        import networkx as nx

        self.__process_id = str(uuid.uuid4()) if process_id == None else process_id
        self.__name = name
        self.__graph = nx.MultiDiGraph()
        self.__nodes = set() if nodes is None else nodes
        self.__flows = set() if flows is None else flows

        if nodes is not None:
            for node in nodes:
                self.__graph.add_node(node)
        if flows is not None:
            for flow in flows:
                self.__graph.add_edge(flow.get_source(), flow.get_target())
    
    def get_process_id(self):
        return self.__process_id
    
    def set_process_id(self, process_id):
        self.__process_id = process_id

    def get_nodes(self):
        return self.__nodes

    def get_flows(self):
        return self.__flows

    def get_graph(self):
        return self.__graph

    def get_name(self):
        return self.__name

    def add_node(self, node):
        self.__nodes.add(node)
        self.__graph.add_node(node)

    def remove_node(self, node):
        if node in self.__nodes:
            self.__nodes.remove(node)
            self.__graph.remove_node(node)

    def remove_flow(self, flow):
        source = flow.get_source()
        target = flow.get_target()
        if source in self.__nodes:
            source.remove_out_arc(flow)
        if target in self.__nodes:
            target.remove_in_arc(flow)
        self.__flows.remove(flow)
        self.__graph.remove_edge(source, target)

    def add_flow(self, flow):
        if not isinstance(flow, BPMN.Flow):
            raise Exception()
        source = flow.get_source()
        target = flow.get_target()
        if source not in self.__nodes:
            self.add_node(source)
        if target not in self.__nodes:
            self.add_node(target)
        self.__flows.add(flow)
        self.__graph.add_edge(source, target, id=flow.get_id(), name=flow.get_name())
        source.add_out_arc(flow)
        target.add_in_arc(flow)
