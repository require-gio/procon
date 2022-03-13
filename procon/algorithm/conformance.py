'''
    The following code owned by procon and its author (More Info: https://github.com/require-gio/procon).

    Procon is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Procon is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Procon.  If not, see <https://www.gnu.org/licenses/>.
'''
from procon.conversion import converter
from procon.conversion.converter import INCLUDE_EVENTS
from procon.objects.bpmn import importer as bpmn_importer
from procon.algorithm import alignments
from procon.objects.petri_net.utils import is_petri_net
from pm4py.objects.petri_net.utils import check_soundness
from pm4py.algo.filtering.pandas.attributes import attributes_filter
from procon.objects.bpmn.obj import BPMN


from pm4py.util import constants as pm4_constants
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.algo.filtering.common.filtering_constants import CASE_CONCEPT_NAME
from pm4py.objects.log.util import xes
from pm4py.statistics.traces.generic.pandas import case_statistics
from pm4py import format_dataframe

from pm4py.util import constants
from pm4py.objects.log.obj import Trace, Event

from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import re
import random
import os
import psutil
from tqdm import tqdm

import xml.etree.ElementTree as ET
import lxml
from lxml import etree
from xml.dom import minidom
import numpy as np
import pandas as pd

CHUNK_SIZE = 10
CORES_PARAM = "cores"

def compute_alignment(log, net, initial_marking, final_marking, parameters):
    import pm4pycvxopt
    variant_keys = [item[0] for item in log]
    log = [item[1] for item in log]
    aligned_traces = []
    for trace in log:
        aligned_traces.append(alignments.apply_trace(trace, net, initial_marking, final_marking, parameters=parameters))
    res = list(zip(variant_keys, aligned_traces))
    return res

def chunks(lst, n, randomize=False):
    """Yield successive n-sized chunks from lst."""
    if randomize:
        random.shuffle(lst)
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def move_stats(alignments):
    """
    Calculate statistics based on alignments
    """
    modelStats = Counter()
    syncStats = Counter()
    logStats = Counter()
    missStats = Counter()
    logPositions = defaultdict(Counter)
    for alignment in alignments:
        for moveTuple in alignment['alignment']:
            if moveTuple[0] == ">>":
                modelStats[moveTuple[1]] += 1
                # check whether the event is completely missing or not in this case
                if moveTuple[1] not in [_moveTuple[0] for _moveTuple in alignment['alignment']]: # not even a log move found
                    missStats[moveTuple[1]] += 1
                else: # count how often and where (between which two events) a model move appeared as a log move within the same trace
                    logTrace = [_moveTuple[0] for _moveTuple in alignment['alignment'] if _moveTuple[0] != ">>"]
                    for i in range(len(logTrace)):
                        if logTrace[i] == moveTuple[1]:
                            before = "start" if i == 0 else logTrace[i-1]
                            after = "end" if i == len(logTrace) - 1 else logTrace[i+1]
                            logPositions[moveTuple[1]][(before, after)] += 1

            elif moveTuple[1] == ">>":
                logStats[moveTuple[0]] += 1
            elif moveTuple[0] == moveTuple[1]:
                syncStats[moveTuple[1]] += 1
    return modelStats, syncStats, logStats, missStats, logPositions

def compute_alignments(df, bpmn_graph, parameters=None):
    """
    Gets the bpmn model enhanced with alignment based conformance information

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
    if parameters is None:
        parameters = {}

    activity_key = parameters[
        pm4_constants.PARAMETER_CONSTANT_ACTIVITY_KEY] if pm4_constants.PARAMETER_CONSTANT_ACTIVITY_KEY in parameters else xes.DEFAULT_NAME_KEY
    case_id_glue = parameters[
        pm4_constants.PARAMETER_CONSTANT_CASEID_KEY] if pm4_constants.PARAMETER_CONSTANT_CASEID_KEY in parameters else CASE_CONCEPT_NAME

    # convert bpmn to Reset net
    reset_net, initial_marking, final_marking = converter.apply(bpmn_graph, parameters=parameters)

    # TODO
    if is_petri_net(reset_net) and not check_soundness.check_easy_soundness_net_in_fin_marking(reset_net, initial_marking, final_marking):
        raise Exception("trying to apply alignments on a Petri net that is not a easy sound net!!")

    # convert df to log 
    # TODO: evaulathe which aproach is faster: df to log conversion or the taken approach with variants
    #converter_parameters = {log_converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY: case_id_glue}
    #log = log_converter.apply(format_dataframe(df, case_id=case_id_glue, activity_key=activity_key, timestamp_key=timestamp_key),
    #    parameters=converter_parameters, variant=log_converter.Variants.TO_EVENT_LOG)
    variants_df = variants = case_statistics.get_variants_df(df,
                                          parameters={case_statistics.Parameters.CASE_ID_KEY: case_id_glue,
                                                      case_statistics.Parameters.ACTIVITY_KEY: activity_key})
    variants_df['index1'] = variants_df.index
    variants_dict = variants_df.groupby("variant")["index1"].count().to_dict()
    # TODO: this approach is instable when there are activities containing a comma in their names
    variants = [(variant, Trace([Event({"concept:name": activity}) for activity in variant.split(",")])) for variant in variants_dict.keys()]
    # TODO: the align params needs to be uncommented in order to have a perfect match between bpmn model tasks and log activities
    # however, this is only required when there are tasks with the same label involved. in that case, instead of elemtn names
    # element ids must me used and ideally, the petri net transitions are named accordingly
    align_parameters = {}
    # align_parameters["ret_tuple_as_trans_desc"] = True

    sub_logs = list(chunks(variants, CHUNK_SIZE, False))
    # gets the amount of real physical cores, so no artificial hyperthreading cores are counted
    num_cores = parameters[CORES_PARAM] if CORES_PARAM in parameters else max(1, psutil.cpu_count(logical=False) - 1)

    proceed = tqdm(desc='Alignments', unit='', total=len(variants))
    with ProcessPoolExecutor(max_workers=num_cores) as executor:
        df_data = []
        futures = []
        for j, sub_log in enumerate(sub_logs):
            futures.append(executor.submit(compute_alignment, sub_log, reset_net, initial_marking, final_marking, align_parameters))
        for i, future in enumerate(as_completed(futures)):
            proceed.update(len(future.result()))
            df_data.append(future.result())
    proceed.close()
   
    # put alignments into a list
    alignments = [alignment for alignmentList in df_data for key, alignment in alignmentList for _ in range(variants_dict[key])]
   
    return alignments


def derive_statistics(alignments, df, bpmn_graph, parameters=None):
    include_events = parameters[INCLUDE_EVENTS] if INCLUDE_EVENTS in parameters else True
    activity_key = parameters[
        pm4_constants.PARAMETER_CONSTANT_ACTIVITY_KEY] if pm4_constants.PARAMETER_CONSTANT_ACTIVITY_KEY in parameters else xes.DEFAULT_NAME_KEY

    # get statistics about how many model moves, synchronous moves, log moves etc. appeared
    modelStats, syncStats, logStats, missStats, logPositions = move_stats(alignments)
    # count activity occurrences
    activities_count = attributes_filter.get_attribute_values(df, activity_key, parameters=parameters)

    # create table from the obtained statistics
    result = []
    columns = ["Activity", "Occurrences", "Correct", "Wrong Position", "Missing"]
    for node in bpmn_graph.get_nodes():
        if isinstance(node, (BPMN.IntermediateCatchEvent, BPMN.IntermediateThrowEvent, BPMN.Task)) or \
            (isinstance(node, BPMN.BoundaryEvent) and include_events):
            activity = node.get_name()
            missMoves = missStats[activity] if activity in missStats else 0
            modelLogMoves = (modelStats[activity] if activity in modelStats else 0) - missMoves
            syncMoves = syncStats[activity] if activity in syncStats else 0
            occurrences = activities_count[activity] if activity in activities_count else 0
            result.append([
                activity, occurrences, syncMoves, modelLogMoves, missMoves
            ])

    # finally, encapsulate the data in a pandas dataframe indexed by activites and sorted by event occurrences
    result = pd.DataFrame(result, columns=columns)
    result.index = result["Activity"]
    result.drop("Activity", axis=1, inplace=True)
    result.sort_values(by="Occurrences", ascending=False, inplace=True)
    return result
