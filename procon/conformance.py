from procon.objects.bpmn import importer as bpmn_importer
from pm4py.objects.log.importer.xes import importer as xes_importer
from procon.algorithm import conformance
from pm4py.objects.log.util import dataframe_utils
from procon.conversion import converter as reset_net_converter
from pm4py.objects.conversion.log import converter as log_converter
import pandas as pd



def import_bpmn(path: str, parameters=None):
    return bpmn_importer.apply(path, parameters=parameters)

def import_event_log(path: str, parameters=None):
    log = xes_importer.apply(path, parameters=parameters)
    return log_converter.apply(log, variant=log_converter.Variants.TO_DATA_FRAME)

def import_dataframe(path: str, sep=',', timestamp_column="time:timestamp", parameters=None):
    log_csv = pd.read_csv(path, sep=',')
    log_csv = dataframe_utils.convert_timestamp_columns_in_df(log_csv)
    return log_csv.sort_values(timestamp_column)

def compute_alignments(df, bpmn_graph, parameters=None):
    """
    Return alignment objects based on the given model and event data

    Parameters
    -------------
    df
        input event log as dataframe
    bpmnString
        bpmn model object
    parameters
        Parameters of the algorithm

    Returns
    ------------
    alignments
        alignments between bpmn model and event data
    """
    return conformance.compute_alignments(df, bpmn_graph, parameters=parameters)

def derive_statistics(alignments, df, bpmn_graph, parameters=None):
    return conformance.derive_statistics(alignments, df, bpmn_graph, parameters=parameters)