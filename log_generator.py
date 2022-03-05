import pickle
from datetime import datetime, timedelta
import pm4py.objects.log.obj as log_instance
from enum import Enum
import random

from pm4py.visualization.petri_net import visualizer as pn_visualizer
from procon.objects.bpmn import importer as bpmn_importer
from procon.conversion import converter as reset_net_converter
import pickle
from pm4py.objects.log.exporter.xes import exporter as xes_exporter

bpmn_graph = bpmn_importer.apply("example.bpmn")

parameters = {}
# should boundary events be treated as labelled activities?
parameters['include_events'] = True
reset_net, initial_marking, final_marking = reset_net_converter.apply(bpmn_graph, parameters=parameters)

class NoiseType(Enum):
        ADD = 1
        REMOVE = 2
        SUBSTITUTE = 3


file_pi2 = open("language.obj", 'rb') 
bpmn_language = pickle.load(file_pi2)

noise_types = [NoiseType.ADD, NoiseType.REMOVE, NoiseType.SUBSTITUTE]
# list of events that the model can create
event_names = [t.label for t in reset_net.transitions if t.label != None]
curr_time = datetime.now()
# randomize the data with artificial noise


noise_level = 0
log = log_instance.EventLog()
for i, trace in enumerate(bpmn_language):
    if i > 100: 
        break
    elements = trace.split(",")
    new_trace = log_instance.Trace(attributes={"concept:name": str(i)})
    for i, element in enumerate(elements):
        time = 100 * i
        # add noise to the current trace and event
        if random.random() < noise_level:
            # switch noise type
            noise_type = random.choice(noise_types)
            if noise_type == NoiseType.ADD:
                # first add the normal element then the new random element chosen from the set of possible events
                new_trace.append( log_instance.Event({"concept:name": element, "time:timestamp": curr_time + timedelta(time + 1)}) )
                random_event = random.choice(event_names)
                new_trace.append( log_instance.Event({"concept:name": random_event, "time:timestamp": curr_time + timedelta(time + 2)}) )
            elif noise_type == NoiseType.REMOVE:
                continue
            else:
                random_event = random.choice([event_name for event_name in event_names if event_name != element])
                new_trace.append( log_instance.Event({"concept:name": random_event, "time:timestamp": curr_time + timedelta(time + 1)}) )
        else:
            new_trace.append( log_instance.Event({"concept:name": element, "time:timestamp": curr_time + timedelta(time + 1)}) )
    log.append(new_trace)



xes_exporter.apply(log, "example.xes")