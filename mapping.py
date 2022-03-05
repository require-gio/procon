import os
import pickle
import procon
import pandas as pd
from pm4py.visualization.petri_net import visualizer as pn_visualizer


# IMPORTANT: In case you want to make use of parallel programming, you need to encapsulate the conformance checking
# code inside a __name__ == '__main__' guard
if __name__ == '__main__':
    bpmn_graph = procon.import_bpmn(os.path.join("examples","test_data","example.bpmn"))

    parameters = {}
    # should boundary events be treated as labelled activities?
    parameters['include_events'] = True
    #reset_net, initial_marking, final_marking = reset_net_converter.apply(bpmn_graph, parameters=parameters)

    #gviz = pn_visualizer.apply(reset_net, initial_marking, final_marking)
    #pn_visualizer.view(gviz)

    df = procon.import_event_log(os.path.join("examples","test_data","example.xes"))
    
    # derive alignemnts between event log and model
    alignments = procon.compute_alignments(df, bpmn_graph, parameters=parameters)

    # ideally, you save the alignments object in some file via pickle in case you do not want to wait the whole time again ;-)
    # import pickle
    # file_pi = open(os.path.join("path", "to", "alignments.obj"), 'wb')
    # pickle.dump(alignments, file_pi)

    # finally, derive conformance statistics from the alignments
    res = procon.derive_statistics(alignments, df, bpmn_graph, parameters=parameters)
    res.to_csv(os.path.join("conformance-result.csv"))
