from pm4py.visualization.petri_net import visualizer as pn_visualizer
from procon.objects.bpmn import importer as bpmn_importer
from procon.conversion import converter as reset_net_converter
import pickle
from procon.algorithm import conformance

from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.conversion.log import converter as log_converter

if __name__ == '__main__':
    bpmn_graph = bpmn_importer.apply("example2.bpmn")

    parameters = {}
    # should boundary events be treated as labelled activities?
    parameters['include_events'] = True
    #reset_net, initial_marking, final_marking = reset_net_converter.apply(bpmn_graph, parameters=parameters)

    #gviz = pn_visualizer.apply(reset_net, initial_marking, final_marking)
    #pn_visualizer.view(gviz)

    log = xes_importer.apply("example2.xes")
    df = log_converter.apply(log, variant=log_converter.Variants.TO_DATA_FRAME)
    res = conformance.apply(df, bpmn_graph, parameters=parameters)
    print(res)