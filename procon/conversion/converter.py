import uuid
from enum import Enum

from procon.conversion.reduction import apply_reset_inhibitor_net_reduction
from procon.objects.petri_net.obj import PetriNet, Marking
from procon.objects.petri_net.utils import add_arc_from_to, get_place_by_name, remove_arc, remove_place, get_transition_by_name, \
    add_reset_arc_from_to, get_place_by_prefix_postfix, is_reset_arc, is_normal_arc
from procon.objects.bpmn.utils import get_boundary_events_of_activity, get_all_nodes_inside_process, get_subprocesses_sorted_by_depth, \
    get_termination_events_of_subprocess, get_node_by_id
from pm4py.util import exec_utils
from procon.objects.petri_net import properties
from collections import defaultdict
from procon.objects.bpmn.obj import BPMN

# specifies whether or not boundary transitions and events should be treated as tasks, i.e no silent transitions
INCLUDE_EVENTS = "include_events"

def apply(bpmn_graph, parameters=None):
    """
    Converts a BPMN graph to an accepting Reset net

    Parameters
    --------------
    bpmn_graph
        BPMN graph
    parameters
        Parameters of the algorithm

    Returns
    --------------
    net
        Reset net
    im
        Initial marking
    fm
        Final marking
    """
    if parameters is None:
        parameters = {}

    include_events = parameters[INCLUDE_EVENTS] if INCLUDE_EVENTS in parameters else True

    # Preprocessing step that removes multiple arcs from a task/event object and replaces them with a XOR
    nodes = [node for node in bpmn_graph.get_nodes()]
    for node in nodes:
        if not isinstance(node, BPMN.Gateway):
            if len(node.get_in_arcs()) > 1:
                inputs = [flow.get_source() for flow in node.get_in_arcs()]
                flows = [flow for flow in node.get_in_arcs()]
                for flow in flows:
                    bpmn_graph.remove_flow(flow)
                exclusive_gateway = BPMN.ExclusiveGateway(id="XOR-input-" + node.get_id(), name="XOR-input-" + node.get_id(), 
                gateway_direction=BPMN.Gateway.Direction.CONVERGING, process=node.get_process())
                bpmn_graph.add_node(exclusive_gateway)
                for input_node in inputs:
                    flow =  BPMN.SequenceFlow(input_node, exclusive_gateway)
                    bpmn_graph.add_flow(flow)
                output_flow = BPMN.SequenceFlow(exclusive_gateway, node)
                bpmn_graph.add_flow(output_flow)
            if len(node.get_out_arcs()) > 1:
                outputs = [flow.get_target() for flow in node.get_out_arcs()]
                flows = [flow for flow in node.get_out_arcs()]
                for flow in flows:
                    bpmn_graph.remove_flow(flow)
                exclusive_gateway = BPMN.ExclusiveGateway(id="XOR-output-" + node.get_id(), name="XOR-output-" + node.get_id(), 
                gateway_direction=BPMN.Gateway.Direction.DIVERGING, process=node.get_process())
                bpmn_graph.add_node(exclusive_gateway)
                for output_node in outputs:
                    flow =  BPMN.SequenceFlow(exclusive_gateway, output_node)
                    bpmn_graph.add_flow(flow)
                input_flow = BPMN.SequenceFlow(node, exclusive_gateway)
                bpmn_graph.add_flow(input_flow)

    # 1. initialize empty model
    net = PetriNet(bpmn_graph.get_name())
    im = Marking()
    fm = Marking()

    # 2. generate one place for each arc/flow
    flow_place = {}
    for flow in bpmn_graph.get_flows():
        # generate a place for each flow
        flow_id = str(flow.get_id())
        if isinstance(flow.source, BPMN.StartEvent):
            place = PetriNet.Place("source@@@" + flow_id + "@@@" + flow.get_process(), properties={"process": flow.get_process()})
        elif isinstance(flow.target, BPMN.EndEvent):
            prefix = "sink"
            suffix = flow_id
            if isinstance(flow.target, BPMN.ErrorEndEvent):
                prefix = "error"
                suffix = flow.target.get_name() + "@@@" + flow_id 
            elif isinstance(flow.target, BPMN.CancelEndEvent):
                prefix = "cancel"
                suffix = flow.target.get_name() + "@@@" + flow_id 
            elif isinstance(flow.target, BPMN.MessageEndEvent):
                prefix = "message"
                suffix = flow.target.get_name() + "@@@" + flow_id 
            elif isinstance(flow.target, BPMN.TerminateEndEvent):
                prefix = "terminate"
                suffix = flow.target.get_name() + "@@@" + flow_id 
            place = PetriNet.Place(prefix + "@@@" + suffix + "@@@" + flow.get_process(), properties={"process": flow.get_process()})
        else:
            place = PetriNet.Place(flow_id + "@@@" + flow.get_process(), properties={"process": flow.get_process()})
        net.places.add(place)
        flow_place[flow] = place

    # 3. loop through each node and transform them without composing them completely yet
    end_places = defaultdict(list)
    for node in bpmn_graph.get_nodes():
        node_id = str(node.get_id())
        if isinstance(node, BPMN.StartEvent):
            start_place = flow_place[node.get_out_arcs()[0]]
            # if this is a global start event, add it to initial marking
            if node.get_process() == bpmn_graph.get_process_id():
                im[start_place] = 1
        elif isinstance(node, (BPMN.IntermediateCatchEvent, BPMN.IntermediateThrowEvent, BPMN.Task)) or \
             (isinstance(node, BPMN.Gateway) and node.get_gateway_direction() == BPMN.Gateway.Direction.UNSPECIFIED and \
                 len(node.get_in_arcs()) == 1 and len(node.get_out_arcs()) == 1):
                if len(node.get_in_arcs()) > 0 and len(node.get_out_arcs()) > 0: # temporary fix
                    in_arc_place = flow_place[node.get_in_arcs()[0]]
                    transition = PetriNet.Transition(name="t@@@" + node_id + "@@@" + node.get_process(), label=str(node.get_name()) if (node.get_name() != "" and not \
                        (isinstance(node, BPMN.Gateway) and node.get_gateway_direction() == BPMN.Gateway.Direction.UNSPECIFIED)) else None, properties={"process": node.get_process()})
                    net.transitions.add(transition)
                    out_arc_place = flow_place[node.get_out_arcs()[0]]
                    # add arc from incoming flow place to (silent) transition
                    add_arc_from_to(in_arc_place, transition, net)
                    # add arc from (silent) transition to outgoing flow place
                    add_arc_from_to(transition, out_arc_place, net)
        elif isinstance(node, BPMN.EndEvent):
            end_place = flow_place[node.get_in_arcs()[0]]
            end_places[node.get_process()].append(end_place)
            # if this is a global end event, add it to final marking
            if isinstance(node, BPMN.NormalEndEvent) and node.get_process() == bpmn_graph.get_process_id():
                fm[end_place] = 1
        elif isinstance(node, BPMN.ParallelGateway):
            if node.get_gateway_direction() == BPMN.Gateway.Direction.DIVERGING or len(node.get_out_arcs()) > 1:
                in_arc_place = flow_place[node.get_in_arcs()[0]]
                transition = PetriNet.Transition(name="t@@@" + node_id + "@@@" + node.get_process(), label=None, properties={"process": node.get_process()})
                net.transitions.add(transition)
                out_arc_places = [flow_place[out_arc] for out_arc in node.get_out_arcs()]
                # add arc from incoming flow place to silent transition
                add_arc_from_to(in_arc_place, transition, net)
                # add arc from silent transition to all outgoing flow places
                for out_arc_place in out_arc_places:
                    add_arc_from_to(transition, out_arc_place, net)
            elif node.get_gateway_direction() == BPMN.Gateway.Direction.CONVERGING or len(node.get_in_arcs()) > 1:
                in_arc_places = [flow_place[in_arc] for in_arc in node.get_in_arcs()]
                transition = PetriNet.Transition(name="t@@@" + node_id + "@@@" + node.get_process(), label=None, properties={"process": node.get_process()})
                net.transitions.add(transition)
                out_arc_place = flow_place[node.get_out_arcs()[0]]
                # add arc from all incoming flow places to silent transition
                for in_arc_place in in_arc_places:
                    add_arc_from_to(in_arc_place, transition, net)
                # add arc from silent transition to outgoing flow place
                add_arc_from_to(transition, out_arc_place, net)
        elif isinstance(node, BPMN.ExclusiveGateway):
            if node.get_gateway_direction() == BPMN.Gateway.Direction.DIVERGING or len(node.get_out_arcs()) > 1:
                in_arc_place = flow_place[node.get_in_arcs()[0]]
                out_arc_places = [flow_place[out_arc] for out_arc in node.get_out_arcs()]
                # add silent transition or each out arc (decision option)
                for i, out_arc_place in enumerate(out_arc_places):
                    transition = PetriNet.Transition(name="t@@@" + node_id + str(i) + "@@@" + node.get_process(), label=None, properties={"process": node.get_process()})
                    net.transitions.add(transition)
                    # add arc from incoming flow place to silent transition
                    add_arc_from_to(in_arc_place, transition, net)
                    # add arc from silent transition to outgoing flow place
                    add_arc_from_to(transition, out_arc_place, net)
            elif node.get_gateway_direction() == BPMN.Gateway.Direction.CONVERGING or len(node.get_in_arcs()) > 1:
                in_arc_places = [flow_place[in_arc] for in_arc in node.get_in_arcs()]
                out_arc_place = flow_place[node.get_out_arcs()[0]]
                # add silent transition or each in arc (decision option)
                for i, in_arc_place in enumerate(in_arc_places):
                    transition = PetriNet.Transition(name="t@@@" + node_id + str(i) + "@@@" + node.get_process(), label=None, properties={"process": node.get_process()})
                    net.transitions.add(transition)
                    # add arc from incoming flow place to silent transition
                    add_arc_from_to(in_arc_place, transition, net)
                    # add arc from silent transition to outgoing flow place
                    add_arc_from_to(transition, out_arc_place, net)
        elif isinstance(node, BPMN.InclusiveGateway):
            raise Exception

    # 4. loop through each node again, this time we glue together subprocesses with the outside world by two silent transitions
    for subprocess in get_subprocesses_sorted_by_depth(bpmn_graph):
        activity_id = subprocess.get_id()
        # assuming one unique source of the subprocess, there needs to be a silent transition from the incoming flow place to the source place
        in_arc_place = flow_place[subprocess.get_in_arcs()[0]]
        source_place = get_place_by_prefix_postfix(net, "source", activity_id, "@@@")
        silent_start_transition = PetriNet.Transition(name="t-start-subprocess@@@" + activity_id + "@@@" + subprocess.get_process(),
            label=None, properties={"process": subprocess.get_process()})
        net.transitions.add(silent_start_transition)
            # add arc from incoming flow place to newly created silent transition
        add_arc_from_to(in_arc_place, silent_start_transition, net)
        # add arc from silent transition to source place of subprocess
        add_arc_from_to(silent_start_transition, source_place, net)
        # assuming block strucuturedness, there is a unique normal end event in the subprocess that needs to be connected to the outgoing flow of the subprocess
        out_arc_place = flow_place[subprocess.get_out_arcs()[0]]
        # get "normal" end event place of subprocess
        sink_place = get_place_by_prefix_postfix(net, "sink", activity_id, "@@@")
        silent_end_transition = PetriNet.Transition(name="t-end-subprocess@@@" + activity_id + "@@@" + subprocess.get_process(),
            label=None, properties={"process": subprocess.get_process()})
        net.transitions.add(silent_end_transition)
        # add arc from subprocess end place to newly created silent transition
        add_arc_from_to(sink_place, silent_end_transition, net)
        # add arc from silent transition to outgoing flow place
        add_arc_from_to(silent_end_transition, out_arc_place, net)

    # 5. loop through tasks and handle their boundary events
    for node in bpmn_graph.get_nodes():
        node_id = str(node.get_id())
        if isinstance(node, BPMN.Activity):
        #if isinstance(node, BPMN.BoundaryEvent):
            activity_id = node.get_id()
            boundary_events = get_boundary_events_of_activity(activity_id, bpmn_graph)
            if len(boundary_events) > 0:
                if isinstance(node, BPMN.Task):
                    in_arc_place = flow_place[node.get_in_arcs()[0]]
                    for boundary_event in boundary_events:
                        boundary_transition = PetriNet.Transition(name="t-boundary@@@" + str(boundary_event.get_id()) + "@@@" + node.get_process(), \
                            label=boundary_event.get_name() if boundary_event.get_name() != "" else None, properties={"process": node.get_process()})
                        net.transitions.add(boundary_transition)
                        out_arc_place = flow_place[boundary_event.get_out_arcs()[0]]
                        # add arc from incoming flow place to newly created (silent) transition
                        add_arc_from_to(in_arc_place, boundary_transition, net)
                        # add arc from newly created (silent) transition to outgoing flow place
                        add_arc_from_to(boundary_transition, out_arc_place, net)

    # 6. loop through subprocesses and handle their boundary events
    for subprocess in get_subprocesses_sorted_by_depth(bpmn_graph):
        activity_id = subprocess.get_id()
        boundary_events = get_boundary_events_of_activity(activity_id, bpmn_graph)
        normal_sink_place = get_place_by_prefix_postfix(net, "sink", activity_id, "@@@")
        if len(boundary_events) > 0:
            external_exception_places = []
            reset_transitions = []
            ignore_places = []
            for boundary_event in boundary_events:
                boundary_event_name = boundary_event.get_name()

                # IMPORTANT: we strictly assume that the end event inside the subprocess and the corresponding Boundary Event have the same name
                concrete_type = "error" if isinstance(boundary_event, BPMN.ErrorBoundaryEvent) else "cancel" if isinstance(boundary_event, BPMN.CancelBoundaryEvent) else "message"
                boundary_transition_label = None if not include_events or boundary_event_name == "" else boundary_event_name
                boundary_transition = PetriNet.Transition(name="t-boundary@@@" + str(boundary_event.get_id()) + "@@@" + subprocess.get_process(),
                    label=boundary_transition_label, properties={"process": subprocess.get_process()})
                net.transitions.add(boundary_transition)
                out_arc_place = flow_place[boundary_event.get_out_arcs()[0]]
                # add arc from newly created (silent) transition to outgoing flow place
                add_arc_from_to(boundary_transition, out_arc_place, net)

                # internal exception
                if isinstance(boundary_event, (BPMN.ErrorBoundaryEvent, BPMN.CancelBoundaryEvent)):
                    # get all end events with the same name
                    error_events = []
                    for n in bpmn_graph.get_nodes():
                        if n.get_process() == boundary_event.get_activity() and isinstance(n, BPMN.EndEvent) and n.get_name() == boundary_event_name:
                            error_events.append(n)
                    # get corresponding places
                    subprocess_end_places = [place for place in end_places[activity_id] if place.name.split("@@@")[0] == concrete_type and \
                        place.name.split("@@@")[1] == boundary_event_name and place.name.split("@@@")[-1] == activity_id]
                    main_end_place = subprocess_end_places[0]
                    ignore_places.append(main_end_place)
                    # add arc from end event place to newly created (silent) transition
                    add_arc_from_to(main_end_place, boundary_transition, net)
                    # get pre transitions
                    # put this line after the removal of redundant places ?
                    pre_transition = list(main_end_place.in_arcs)[0].source
                    reset_transitions.append(pre_transition)
                    # remove the other redundant places and redirect all arcs to the main place
                    for place in subprocess_end_places[1:]:
                        while True:
                            if len(place.in_arcs) > 0:
                                add_arc_from_to(list(place.in_arcs)[0].source, main_end_place, net)
                                remove_arc(net, list(place.in_arcs)[0])
                            else:
                                break
                        remove_place(net, place)

                    
                   
                    places_inside_subprocess = [place for place in net.places if "process" in place.properties and place.properties["process"] == activity_id]
                    for place in places_inside_subprocess:
                        if place not in ignore_places and place != normal_sink_place:
                            add_reset_arc_from_to(place, pre_transition, net)

                # external exception
                else:
                    subprocess_start_transition = get_transition_by_name(net, "t-start-subprocess@@@" + activity_id + "@@@" + subprocess.get_process())
                    subprocess_end_transition = get_transition_by_name(net, "t-end-subprocess@@@" + activity_id + "@@@" + subprocess.get_process())
                    boundary_start_place = PetriNet.Place("boundary@@@" + str(boundary_event.get_id()) + "@@@" + activity_id, properties={"process": activity_id})
                    net.places.add(boundary_start_place)
                    ignore_places.append(boundary_start_place)
                    external_exception_places.append(boundary_start_place)
                    add_arc_from_to(subprocess_start_transition, boundary_start_place, net)
                    add_arc_from_to(boundary_start_place, subprocess_end_transition, net)
                    add_arc_from_to(boundary_start_place, boundary_transition, net)

                    # add reset arc from all places to the boundary transition
                    places_inside_subprocess = [place for place in net.places if "process" in place.properties and place.properties["process"] == activity_id]
                    for place in places_inside_subprocess:
                        if place not in ignore_places:
                            add_reset_arc_from_to(place, boundary_transition, net)

            # add arcs in order to prevent multiple boundary events to fire
            for place in external_exception_places:
                for transition in reset_transitions:
                    add_reset_arc_from_to(place, transition, net)
    
        # handle termination event inside subprocess
        termination_events = get_termination_events_of_subprocess(activity_id, bpmn_graph)
      
        for termination_event in termination_events:
            in_flow = list(termination_event.in_arcs)[0]
            termination_end_place = flow_place[in_flow]
            termination_transition = list(termination_end_place.in_arcs)[0].source

            
            for place in net.places:
                if "process" in place.properties and place.properties["process"] == activity_id and place != termination_end_place:
                    add_reset_arc_from_to(place, termination_transition, net)

            # add arc to outgoing place of subprocess
            subprocess_end_transition_out_arc_place = list(get_transition_by_name(net, "t-end-subprocess@@@" + activity_id + "@@@" + subprocess.get_process()).out_arcs)[0].target
            terminate_skip_trans = PetriNet.Transition("t-terminate-end@@@" + termination_event.get_id() + "@@@" + activity_id + "@@@" + subprocess.get_process(),
                label=None, properties={"process": subprocess.get_process()})
            net.transitions.add(terminate_skip_trans)
            add_arc_from_to(termination_end_place, terminate_skip_trans, net)
            add_arc_from_to(terminate_skip_trans, subprocess_end_transition_out_arc_place, net)

        # TODO: rename all places and transitions inside the subprocess so they refer to the subprocess that is higher in hierarchy --> makes it possible to handle subs in subs
        # on the other hand, the termination event handling on global scale could have a problem with ambiguous names, ideally, we remove the prefix on the already handled
        # subprocess end activities
        for place in net.places:
            if "process" in place.properties and place.properties["process"] == activity_id:
                place.properties["process"] = subprocess.get_process()
        for transition in net.transitions:
            if "process" in transition.properties and transition.properties["process"] == activity_id:
                transition.properties["process"] = subprocess.get_process()
                

    # handle termination end events globally
    main_process_id = bpmn_graph.get_process_id()
    termination_events = get_termination_events_of_subprocess(main_process_id, bpmn_graph)
    for termination_event in termination_events:
            in_flow = list(termination_event.in_arcs)[0]
            termination_end_place = flow_place[in_flow]
            termination_transition = list(termination_end_place.in_arcs)[0].source
            pre_places = [arc.source for arc in termination_transition.in_arcs if is_normal_arc(arc)]
           
            for place in net.places:
                # add reset arc for all places except the terminate end place
                if len(place.name.split("@@@")) > 0 and  place.name.split("@@@")[0] != "terminate"  and place not in pre_places:
                    add_reset_arc_from_to(place, termination_transition, net)

            # add arc to global sink place
            global_end_place = get_place_by_prefix_postfix(net, "sink", main_process_id, "@@@")
            terminate_skip_trans = PetriNet.Transition("t-terminate-end@@@" + termination_event.get_id() + "@@@" + main_process_id,
                label=None, properties={"process": main_process_id})
            net.transitions.add(terminate_skip_trans)
            add_arc_from_to(termination_end_place, terminate_skip_trans, net)
            add_arc_from_to(terminate_skip_trans, global_end_place, net)

    # apply reduction rules
    apply_reset_inhibitor_net_reduction(net, im, fm)

    return net, im, fm
