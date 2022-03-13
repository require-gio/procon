from procon.objects.bpmn import importer as bpmn_importer
from pm4py.objects.log.importer.xes import importer as xes_importer
from procon.algorithm import conformance
from pm4py.objects.log.util import dataframe_utils
from procon.conversion import converter as reset_net_converter
from pm4py.objects.conversion.log import converter as log_converter
import pandas as pd
import inspect
import __main__



def import_bpmn(path: str, parameters=None):
    """
    Import a .bpmn file

    Parameters
    -------------
    path
        path to bpmn file
    parameters
        parameters of bpmn importer

    Returns
    ------------
    parsed bpmn object
    """
    return bpmn_importer.apply(path, parameters=parameters)

def import_event_log(path: str, parameters=None):
    """
    Import an event log from .xes format as a pandas dataframe

    Parameters
    -------------
    path
        path to xes file
    parameters
        parameters of pm4py xes importer

    Returns
    ------------
    pandas dataframe containing imported event data
    """
    log = xes_importer.apply(path, parameters=parameters)
    return log_converter.apply(log, variant=log_converter.Variants.TO_DATA_FRAME)

def import_dataframe(path: str, sep=',', timestamp_column="time:timestamp", parameters=None):
    """
    Import a csv file containing temporally ordered event data

    Parameters
    -------------
    path
        path to csv file
    sep
        csv separator
    timestamp_column
        name of timestamp columns
    parameters
        parameters of pandas csv importer

    Returns
    ------------
    pandas dataframe containing imported event data
    """
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
    bpmn_graph
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
    """
    Compute alignment-based statistics

    Parameters
    -------------
    alignments
        alignments between process model and event log
    df
        tabular event log object
    bpmn_graph
        bpmn model object
    parameters
        Parameters of the algorithm

    Returns
    ------------
        pandas dataframe containing the amount of occurrences for each activity as well as the number of correct, 
        missplaced and missing accordances between model and event log
    """
    return conformance.derive_statistics(alignments, df, bpmn_graph, parameters=parameters)