'''
    This file is part of PM4Py (More Info: https://pm4py.fit.fraunhofer.de).

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
from procon.objects.bpmn.obj import BPMN
from pm4py.util import constants
import uuid


class Counts:
    def __init__(self):
        self.number_processes = 0


def parse_element(bpmn_graph, counts, curr_el, parents, incoming_dict, outgoing_dict, nodes_dict, nodes_bounds,
                  flow_info, process=None, node=None, bpmn_element=None, flow=None, rec_depth=0):
    """
    Parses a BPMN element from the XML file
    """
    tag = curr_el.tag.lower()
    if tag.endswith("subprocess"): # subprocess invocation
        name = curr_el.get("name").replace("\r", "").replace("\n", "") if "name" in curr_el.attrib else ""
        subprocess = BPMN.SubProcess(id=curr_el.get("id"), name=name, process=process, depth=rec_depth)
        bpmn_graph.add_node(subprocess)
        node = subprocess
        process = curr_el.get("id")
        nodes_dict[process] = node
    elif tag.endswith("process"): # process of the current subtree
        process = curr_el.get("id")
        bpmn_graph.set_process_id(process)
    elif tag.endswith("shape"): # shape of a node, contains x,y,width,height information
        bpmn_element = curr_el.get("bpmnElement")
    elif tag.endswith("task"): # simple task object
        id = curr_el.get("id")
        name = curr_el.get("name").replace("\r", "").replace("\n", "") if "name" in curr_el.attrib else ""
        #this_type = str(curr_el.tag)
        #this_type = this_type[this_type.index("}") + 1:]
        task = BPMN.Task(id=id, name=name, process=process)
        bpmn_graph.add_node(task)
        node = task
        nodes_dict[id] = node
    elif tag.endswith("startevent"): # start node starting the (sub)process
        id = curr_el.get("id")
        name = curr_el.get("name").replace("\r", " ").replace("\n", " ") if "name" in curr_el.attrib else ""
        event_definitions = [child.tag.lower().replace("eventdefinition","") for child in curr_el if child.tag.lower().endswith("eventdefinition")] 
        if len(event_definitions) > 0:
            event_type = event_definitions[0]
            if  event_type.endswith("message"):
                start_event = BPMN.MessageStartEvent(id=curr_el.get("id"), name=name, process=process)
            else: # TODO: expand functionality, support more start event types
                start_event = BPMN.NormalStartEvent(id=curr_el.get("id"), name=name, process=process)
        else:
            start_event = BPMN.NormalStartEvent(id=curr_el.get("id"), name=name, process=process)
        bpmn_graph.add_node(start_event)
        node = start_event
        nodes_dict[id] = node
    elif tag.endswith("endevent"): # end node ending the (sub)process
        id = curr_el.get("id")
        name = curr_el.get("name").replace("\r", " ").replace("\n", " ") if "name" in curr_el.attrib else ""
        event_definitions = [child.tag.lower().replace("eventdefinition","") for child in curr_el if child.tag.lower().endswith("eventdefinition")] 
        if len(event_definitions) > 0:
            event_type = event_definitions[0]
            if  event_type.endswith("message"):
                end_event = BPMN.MessageEndEvent(id=curr_el.get("id"), name=name, process=process)
            elif  event_type.endswith("terminate"):
                end_event = BPMN.TerminateEndEvent(id=curr_el.get("id"), name=name, process=process)
            elif  event_type.endswith("error"):
                end_event = BPMN.ErrorEndEvent(id=curr_el.get("id"), name=name, process=process)
            elif  event_type.endswith("cancel"):
                end_event = BPMN.CancelEndEvent(id=curr_el.get("id"), name=name, process=process)
            else: # TODO: expand functionality, support more start event types
                end_event = BPMN.NormalEndEvent(id=curr_el.get("id"), name=name, process=process)
        else:
            end_event = BPMN.NormalEndEvent(id=curr_el.get("id"), name=name, process=process)
        bpmn_graph.add_node(end_event)
        node = end_event
        nodes_dict[id] = node
    elif tag.endswith("intermediatecatchevent"): # intermediate event that happens (externally) and can be catched
        id = curr_el.get("id")
        name = curr_el.get("name").replace("\r", " ").replace("\n", " ") if "name" in curr_el.attrib else ""    
        event_definitions = [child.tag.lower().replace("eventdefinition","") for child in curr_el if child.tag.lower().endswith("eventdefinition")] 
        if len(event_definitions) > 0:
            event_type = event_definitions[0]
            if  event_type.endswith("message"):
                intermediate_catch_event = BPMN.MessageIntermediateCatchEvent(id=curr_el.get("id"), name=name, process=process)
            elif  event_type.endswith("error"):
                intermediate_catch_event = BPMN.ErrorIntermediateCatchEvent(id=curr_el.get("id"), name=name, process=process)
            elif  event_type.endswith("cancel"):
                intermediate_catch_event = BPMN.CancelIntermediateCatchEvent(id=curr_el.get("id"), name=name, process=process)
            else:
                intermediate_catch_event = BPMN.IntermediateCatchEvent(id=curr_el.get("id"), name=name, process=process)
        else:
            intermediate_catch_event = BPMN.IntermediateCatchEvent(id=curr_el.get("id"), name=name, process=process)
        bpmn_graph.add_node(intermediate_catch_event)
        node = intermediate_catch_event
        nodes_dict[id] = node
    elif tag.endswith("intermediatethrowevent"): # intermediate event that is activated through the (sub)process
        id = curr_el.get("id")
        name = curr_el.get("name").replace("\r", " ").replace("\n", " ") if "name" in curr_el.attrib else ""      
        event_definitions = [child.tag.lower().replace("eventdefinition","") for child in curr_el if child.tag.lower().endswith("eventdefinition")] 
        if len(event_definitions) > 0:
            event_type = event_definitions[0]
            if  event_type.endswith("message"):
                intermediate_throw_event = BPMN.MessageIntermediateThrowEvent(id=curr_el.get("id"), name=name, process=process)
            else:
                intermediate_throw_event = BPMN.NormalIntermediateThrowEvent(id=curr_el.get("id"), name=name, process=process)
        else:
            intermediate_throw_event = BPMN.NormalIntermediateThrowEvent(id=curr_el.get("id"), name=name, process=process)
        bpmn_graph.add_node(intermediate_throw_event)
        node = intermediate_throw_event
        nodes_dict[id] = node
    elif tag.endswith("boundaryevent"):
        id = curr_el.get("id")
        ref_activity = curr_el.get("attachedToRef")
        name = curr_el.get("name").replace("\r", " ").replace("\n", " ") if "name" in curr_el.attrib else ""     
        event_definitions = [child.tag.lower().replace("eventdefinition","") for child in curr_el if child.tag.lower().endswith("eventdefinition")]
        if len(event_definitions) > 0:
            event_type = event_definitions[0]
            if event_type.endswith("message"):
                boundary_event = BPMN.MessageBoundaryEvent(id=curr_el.get("id"), name=name, process=process, activity=ref_activity)
            elif  event_type.endswith("error"):
                boundary_event = BPMN.ErrorBoundaryEvent(id=curr_el.get("id"), name=name, process=process, activity=ref_activity)
            elif  event_type.endswith("cancel"):
                boundary_event = BPMN.CancelBoundaryEvent(id=curr_el.get("id"), name=name, process=process, activity=ref_activity)
            else:
                boundary_event = BPMN.BoundaryEvent(id=curr_el.get("id"), name=name, process=process, activity=ref_activity)
        else:
            boundary_event = BPMN.BoundaryEvent(id=curr_el.get("id"), name=name, process=process, activity=ref_activity)
        bpmn_graph.add_node(boundary_event)
        node = boundary_event
        nodes_dict[id] = node
    elif tag.endswith("edge"): # related to the x, y information of an arc
        bpmnElement = curr_el.get("bpmnElement")
        flow = bpmnElement
    elif tag.endswith("exclusivegateway"):
        id = curr_el.get("id")
        name = curr_el.get("name").replace("\r", "").replace("\n", "") if "name" in curr_el.attrib else ""
        try:
            direction = BPMN.Gateway.Direction[curr_el.get("gatewayDirection").upper()]
            exclusive_gateway = BPMN.ExclusiveGateway(id=curr_el.get("id"), name=name, gateway_direction=direction, process=process)
        except:
            exclusive_gateway = BPMN.ExclusiveGateway(id=curr_el.get("id"), name=name, gateway_direction=BPMN.Gateway.Direction.UNSPECIFIED, process=process)
        bpmn_graph.add_node(exclusive_gateway)
        node = exclusive_gateway
        nodes_dict[id] = node
    elif tag.endswith("parallelgateway"):
        id = curr_el.get("id")
        name = curr_el.get("name").replace("\r", "").replace("\n", "") if "name" in curr_el.attrib else ""
        try:
            direction = BPMN.Gateway.Direction[curr_el.get("gatewayDirection").upper()]
            parallel_gateway = BPMN.ParallelGateway(id=curr_el.get("id"), name=name, gateway_direction=direction, process=process)
        except:
            parallel_gateway = BPMN.ParallelGateway(id=curr_el.get("id"), name=name, gateway_direction=BPMN.Gateway.Direction.UNSPECIFIED, process=process)
        bpmn_graph.add_node(parallel_gateway)
        node = parallel_gateway
        nodes_dict[id] = node
    elif tag.endswith("inclusivegateway"):
        id = curr_el.get("id")
        name = curr_el.get("name").replace("\r", "").replace("\n", "") if "name" in curr_el.attrib else ""
        try:
            direction = BPMN.Gateway.Direction[curr_el.get("gatewayDirection").upper()]
            inclusive_gateway = BPMN.InclusiveGateway(id=curr_el.get("id"), name=name, gateway_direction=direction, process=process)
        except:
            inclusive_gateway = BPMN.InclusiveGateway(id=curr_el.get("id"), name=name, gateway_direction=BPMN.Gateway.Direction.UNSPECIFIED, process=process)
        bpmn_graph.add_node(inclusive_gateway)
        node = inclusive_gateway
        nodes_dict[id] = node
    elif tag.endswith("incoming"): # incoming flow of a node
        if node is not None:
            incoming_dict[curr_el.text.strip()] = node
    elif tag.endswith("outgoing"): # outgoing flow of a node
        if node is not None:
            outgoing_dict[curr_el.text.strip()] = node
    elif tag.endswith("sequenceflow"): # normal sequence flow between two nodes
        seq_flow_id = curr_el.get("id")
        source_ref = curr_el.get("sourceRef")
        target_ref = curr_el.get("targetRef")
        # fix 28/04/2021: do not assume anymore to read the nodes before the edges
        incoming_dict[seq_flow_id] = (target_ref, process)
        outgoing_dict[seq_flow_id] = (source_ref, process)
    #elif tag.endswith("messageflow"): # TODO: implement different treatment of message flows
    #    seq_flow_id = curr_el.get("id")
    #    source_ref = curr_el.get("sourceRef")
    #    target_ref = curr_el.get("targetRef")
    #    incoming_dict[seq_flow_id] = target_ref
    #    outgoing_dict[seq_flow_id] = source_ref
    elif tag.endswith("waypoint"): # contains information of x, y values of an edge
        if flow is not None:
            x = float(curr_el.get("x"))
            y = float(curr_el.get("y"))
            if not flow in flow_info:
                flow_info[flow] = []
            flow_info[flow].append((x, y))
    elif tag.endswith("label"): # label of a node, mostly at the end of a shape object
        bpmn_element = None
    elif tag.endswith("bounds"): # contains information of width, height, x, y of a node
        if bpmn_element is not None:
            x = float(curr_el.get("x"))
            y = float(curr_el.get("y"))
            width = float(curr_el.get("width"))
            height = float(curr_el.get("height"))
            nodes_bounds[bpmn_element] = {"x": x, "y": y, "width": width, "height": height}

    for child in curr_el:
        bpmn_graph = parse_element(bpmn_graph, counts, child, list(parents) + [child], incoming_dict, outgoing_dict,
                                   nodes_dict, nodes_bounds, flow_info, process=process, node=node,
                                   bpmn_element=bpmn_element,
                                   flow=flow, rec_depth=rec_depth + 1)
    # afterprocessing when the xml tree has been recursively parsed already
    if rec_depth == 0:
        # bpmn_graph.set_process_id(process)
        for seq_flow_id in incoming_dict:
            if incoming_dict[seq_flow_id][0] in nodes_dict:
                incoming_dict[(seq_flow_id)] = (nodes_dict[incoming_dict[seq_flow_id][0]], incoming_dict[seq_flow_id][1])
        for seq_flow_id in outgoing_dict:
            if outgoing_dict[seq_flow_id][0] in nodes_dict:
                outgoing_dict[seq_flow_id] = (nodes_dict[outgoing_dict[seq_flow_id][0]], incoming_dict[seq_flow_id][1])
        for flow_id in flow_info:
            if flow_id in outgoing_dict and flow_id in incoming_dict:
                flow = BPMN.SequenceFlow(outgoing_dict[flow_id][0], incoming_dict[flow_id][0], id=flow_id, name="", process=outgoing_dict[flow_id][1])
                bpmn_graph.add_flow(flow)
                flow.del_waypoints()
                for waypoint in flow_info[flow_id]:
                    flow.add_waypoint(waypoint)
        for node_id in nodes_bounds:
            if node_id in nodes_dict:
                bounds = nodes_bounds[node_id]
                node = nodes_dict[node_id]
                node.set_x(bounds["x"])
                node.set_y(bounds["y"])
                node.set_width(bounds["width"])
                node.set_height(bounds["height"])
    return bpmn_graph


def import_xml_tree_from_root(root):
    """
    Imports a BPMN graph from (the root of) an XML tree

    Parameters
    -------------
    root
        Root of the tree

    Returns
    -------------
    bpmn_graph
        BPMN graph
    """
    bpmn_graph = BPMN()
    counts = Counts()
    incoming_dict = {}
    outgoing_dict = {}
    nodes_dict = {}
    nodes_bounds = {}
    flow_info = {}

    return parse_element(bpmn_graph, counts, root, [], incoming_dict, outgoing_dict, nodes_dict, nodes_bounds,
                         flow_info)


def apply(path, parameters=None):
    """
    Imports a BPMN diagram from a file

    Parameters
    -------------
    path
        Path to the file
    parameters
        Parameters of the algorithm

    Returns
    -------------
    bpmn_graph
        BPMN graph
    """
    if parameters is None:
        parameters = {}

    from lxml import etree, objectify

    parser = etree.XMLParser(remove_comments=True)
    xml_tree = objectify.parse(path, parser=parser)

    return import_xml_tree_from_root(xml_tree.getroot())


def import_from_string(bpmn_string, parameters=None):
    """
    Imports a BPMN diagram from a string

    Parameters
    -------------
    path
        Path to the file
    parameters
        Parameters of the algorithm

    Returns
    -------------
    bpmn_graph
        BPMN graph
    """
    if parameters is None:
        parameters = {}

    if type(bpmn_string) is str:
        bpmn_string = bpmn_string.encode(constants.DEFAULT_ENCODING)

    from lxml import etree, objectify

    parser = etree.XMLParser(remove_comments=True)
    root = objectify.fromstring(bpmn_string, parser=parser)

    return import_xml_tree_from_root(root)
