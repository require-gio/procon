from procon.objects.bpmn.obj import BPMN


def get_node_by_id(id, bpmn_graph):
    """
    Returns the node with specified id

    Parameters
    ------------
    id
        id string
    bpmn_graph
        BPMN graph

    Returns
    ------------
    node that matches the id
    """
    for node in bpmn_graph.get_nodes():
        if node.get_id() == id:
            return node
    return None

def get_global_start_events(bpmn_graph):
    start_events = []
    for node in bpmn_graph.get_nodes():
        if isinstance(node, BPMN.StartEvent):
            if node.get_process() == bpmn_graph.get_process_id():
                start_events.append(node)
    return start_events


def get_boundary_events_of_activity(activity_id, bpmn_graph):
    boundary_events = []
    for node in bpmn_graph.get_nodes():
        if isinstance(node, BPMN.BoundaryEvent):
            node_activity_id = node.get_activity()
            if node_activity_id == activity_id:
                boundary_events.append(node)
    return boundary_events

def get_external_boundary_events_of_activity(activity_id, bpmn_graph):
    boundary_events = []
    for node in bpmn_graph.get_nodes():
        if isinstance(node, BPMN.MessageBoundaryEvent):
            node_activity_id = node.get_activity()
            if node_activity_id == activity_id:
                boundary_events.append(node)
    return boundary_events

def get_all_nodes_inside_process(process_id, bpmn_graph, deep=True):
    nodes = []
    for node in bpmn_graph.get_nodes():
        if deep:
            if process_id in get_processes_deep(node, bpmn_graph):
                nodes.append(node)
        else:
            if node.get_process() == process_id:
                nodes.append(node)
    return nodes

# return the direct children of a subprocess
def get_all_direct_child_subprocesses(process_id, bpmn_graph, include_normal=False):
    nodes = set()
    for node in bpmn_graph.get_nodes():
        if isinstance(node, BPMN.SubProcess) and node.get_process() == process_id:
            if not include_normal:
                boundary_events = get_boundary_events_of_activity(node.get_id(), bpmn_graph)
                # termination events inside subprocess
                termination_events = get_termination_events_of_subprocess_for_pnet(node.get_id(), bpmn_graph)
                if len(boundary_events) > 0 or len(termination_events) > 0:
                    nodes.add(node)
            else:
                nodes.add(node)
    return nodes

# return the direct and indirect children of a subprocess
def get_all_child_subprocesses(process_id, bpmn_graph, include_normal=False):
    sub_processes = set()
    for child in get_all_direct_child_subprocesses(process_id, bpmn_graph, include_normal):
        sub_processes.add(child)
        sub_processes = sub_processes.union(get_all_child_subprocesses(child.get_id(), bpmn_graph, include_normal))
    return sub_processes

def get_processes_deep(node, bpmn_graph):
    if node.get_process() == bpmn_graph.get_process_id():
        return [bpmn_graph.get_process_id()]
    else:
        return [node.get_process()] + get_processes_deep(get_node_by_id(node.get_process(), bpmn_graph), bpmn_graph)


def get_subprocesses_sorted_by_depth(bpmn_graph):
    return sorted([node for node in bpmn_graph.get_nodes() if isinstance(node, BPMN.SubProcess)], key=lambda x: x.get_depth(), reverse=True)

def get_termination_events_of_subprocess(activity_id, bpmn_graph):
    events = []
    for node in bpmn_graph.get_nodes():
        if node.get_process() == activity_id and isinstance(node, BPMN.TerminateEndEvent):
            events.append(node)
    return events

def get_termination_events_of_subprocess_for_pnet(activity_id, bpmn_graph):
    events = []
    for node in bpmn_graph.get_nodes():
        if node.get_process() == activity_id and isinstance(node, (BPMN.IntermediateCatchEvent, BPMN.IntermediateThrowEvent)):
            cond = False
            for boundary_event in get_boundary_events_of_activity(activity_id, bpmn_graph):
                if boundary_event.get_name() == node.get_name():
                    cond = True
            if not cond:
                events.append(node)
    return events


def get_start_events_of_subprocess(activity_id, bpmn_graph):
    events = []
    for node in bpmn_graph.get_nodes():
        if node.get_process() == activity_id and isinstance(node, BPMN.StartEvent):
            events.append(node)
    return events

def get_end_events_of_subprocess(activity_id, bpmn_graph):
    events = []
    for node in bpmn_graph.get_nodes():
        if node.get_process() == activity_id and isinstance(node, BPMN.EndEvent):
            events.append(node)
    return events


"""
Here we define a special version of the bpmn graph, where subprocess end events or (global) termination events are treated as throw events.
If we map an end event, then the throw event will be redirected to a new xor gate, which can be seen as the closing xor gate that corresponds to the xor gate,
which initially opened the side branch. In the case of a termination event at the end of a branch coming from  a catch event, we would like it to redirect a
throwing event to the out-arc of the corresponding subprocess.
"""
def bpmn_graph_end_events_as_throw_events(bpmn_graph):
    events = []
    for node in bpmn_graph.get_nodes():
        # subprocess end event
        if node.get_process() != bpmn_graph.get_process_id() and isinstance(node, BPMN.EndEvent) and not isinstance(node, BPMN.NormalEndEvent):

            events.append(node)
    return events

"""
For a given end event, we will find the diverging xor gate which is the source of the token
def branch_xor_gate(event, bpmn_graph):
    incoming_flow = event.get_in_arcs()[0]


def follow_up_contains_closing_gate(event, bpmn_graph):
    if isinstance(event, BPMN.NormalEndEvent) or isinstance(event, BPMN.Gateway) and event.get_gateway_direction() == BPMN.Gateway.Direction.CONVERGING:
        return True
    else:
        return follow_up_contains_closing_gate(event, bpmn_graph):
"""