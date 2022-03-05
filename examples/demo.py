import os
import procon
import pandas as pd


# IMPORTANT: In case you want to make use of parallel programming, you need to encapsulate the conformance checking
# code inside a __name__ == '__main__' guard
if __name__ == '__main__':
    # import .bpmn file
    bpmn_graph = procon.import_bpmn(os.path.join("test_data","example.bpmn"))

    # import event log as a dataframe
    df = procon.import_event_log(os.path.join("test_data","example.xes"))
    # alternatively, you can directly import a dataframe via pandas
    # for more info see https://pm4py.fit.fraunhofer.de/documentation#importing
    
    parameters = {}
    # should boundary events be treated as labelled activities?
    parameters['include_events'] = True
    # derive alignemnts between event log and model
    alignments = procon.compute_alignments(df, bpmn_graph, parameters=parameters)

    # ideally, you save the alignments object in some file via pickle in case you do not want to wait the whole time again ;-)
    # import pickle
    # file_pi = open(os.path.join("path", "to", "alignments.obj"), 'wb')
    # pickle.dump(alignments, file_pi)

    # finally, derive conformance statistics from the alignments
    res = procon.derive_statistics(alignments, df, bpmn_graph, parameters=parameters)
    # save the resulting dataframe to a csv file on your machine
    res.to_csv(os.path.join("conformance-result.csv"))
