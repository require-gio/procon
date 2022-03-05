'''
    The following code is mainly adopted from PM4Py (More Info: https://pm4py.fit.fraunhofer.de).
    Changes relate to the support for reset/inhibitor nets.

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
from copy import copy
from procon.objects.petri_net.obj import PetriNet, Marking

from pm4py.objects.petri_net.utils import align_utils, check_soundness
from pm4py.statistics.variants.log import get as variants_module
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.util.xes_constants import DEFAULT_NAME_KEY, DEFAULT_TRACEID_KEY
from pm4py.objects.log.obj import Trace
import time
from pm4py.util import exec_utils
from enum import Enum
import sys
from pm4py.util.constants import PARAMETER_CONSTANT_ACTIVITY_KEY, PARAMETER_CONSTANT_CASEID_KEY
import pkgutil
from typing import Optional, Dict, Any, Union, Tuple
from pm4py.objects.log.obj import EventLog, EventStream, Trace
from pm4py.util import typing
import pandas as pd
from procon.algorithm import a_star

class Parameters(Enum):
    PARAM_TRACE_COST_FUNCTION = 'trace_cost_function'
    PARAM_MODEL_COST_FUNCTION = 'model_cost_function'
    PARAM_SYNC_COST_FUNCTION = 'sync_cost_function'
    PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE = 'ret_tuple_as_trans_desc'
    PARAM_TRACE_NET_COSTS = "trace_net_costs"
    TRACE_NET_CONSTR_FUNCTION = "trace_net_constr_function"
    TRACE_NET_COST_AWARE_CONSTR_FUNCTION = "trace_net_cost_aware_constr_function"
    PARAM_MAX_ALIGN_TIME_TRACE = "max_align_time_trace"
    PARAM_MAX_ALIGN_TIME = "max_align_time"
    PARAMETER_VARIANT_DELIMITER = "variant_delimiter"
    CASE_ID_KEY = PARAMETER_CONSTANT_CASEID_KEY
    ACTIVITY_KEY = PARAMETER_CONSTANT_ACTIVITY_KEY
    VARIANTS_IDX = "variants_idx"
    SHOW_PROGRESS_BAR = "show_progress_bar"
    CORES = 'cores'
    BEST_WORST_COST_INTERNAL = "best_worst_cost_internal"
    FITNESS_ROUND_DIGITS = "fitness_round_digits"


def apply_trace(trace, petri_net, initial_marking, final_marking, parameters=None):
    """
    apply alignments to a trace
    Parameters
    -----------
    trace
        :class:`pm4py.log.log.Trace` trace of events
    petri_net
        :class:`pm4py.objects.petri.petrinet.PetriNet` the model to use for the alignment
    initial_marking
        :class:`pm4py.objects.petri.petrinet.Marking` initial marking of the net
    final_marking
        :class:`pm4py.objects.petri.petrinet.Marking` final marking of the net
    variant
        selected variant of the algorithm, possible values: {\'Variants.VERSION_STATE_EQUATION_A_STAR, Variants.VERSION_DIJKSTRA_NO_HEURISTICS \'}
    parameters
        :class:`dict` parameters of the algorithm, for key \'state_equation_a_star\':
            Parameters.ACTIVITY_KEY -> Attribute in the log that contains the activity
            Parameters.PARAM_MODEL_COST_FUNCTION ->
            mapping of each transition in the model to corresponding synchronous costs
            Parameters.PARAM_SYNC_COST_FUNCTION ->
            mapping of each transition in the model to corresponding model cost
            Parameters.PARAM_TRACE_COST_FUNCTION ->
            mapping of each index of the trace to a positive cost value
    Returns
    -----------
    alignment
        :class:`dict` with keys **alignment**, **cost**, **visited_states**, **queued_states** and
        **traversed_arcs**
        The alignment is a sequence of labels of the form (a,t), (a,>>), or (>>,t)
        representing synchronous/log/model-moves.
    """
    if parameters is None:
        parameters = copy({PARAMETER_CONSTANT_ACTIVITY_KEY: DEFAULT_NAME_KEY})

    parameters = copy(parameters)
    best_worst_cost = exec_utils.get_param_value(Parameters.BEST_WORST_COST_INTERNAL, parameters,
                                                 __get_best_worst_cost(petri_net, initial_marking, final_marking, parameters))

    ali = a_star.apply(trace, petri_net, initial_marking, final_marking,
                                                 parameters=parameters)

    trace_cost_function = exec_utils.get_param_value(Parameters.PARAM_TRACE_COST_FUNCTION, parameters, [])
    # Instead of using the length of the trace, use the sum of the trace cost function
    trace_cost_function_sum = sum(trace_cost_function)

    ltrace_bwc = trace_cost_function_sum + best_worst_cost

    fitness = 1 - (ali['cost'] // align_utils.STD_MODEL_LOG_MOVE_COST) / (
                ltrace_bwc // align_utils.STD_MODEL_LOG_MOVE_COST) if ltrace_bwc > 0 else 0

    ali["fitness"] = fitness
    # returning also the best worst cost, for log fitness computation
    ali["bwc"] = ltrace_bwc

    return ali


def __get_best_worst_cost(petri_net, initial_marking, final_marking, parameters):
    parameters_best_worst = copy(parameters)

    best_worst_cost = a_star.get_best_worst_cost(petri_net, initial_marking, final_marking,
                                                                          parameters=parameters_best_worst)

    return best_worst_cost


def __get_progress_bar(num_variants, parameters):
    show_progress_bar = exec_utils.get_param_value(Parameters.SHOW_PROGRESS_BAR, parameters, True)
    progress = None
    if pkgutil.find_loader("tqdm") and show_progress_bar and num_variants > 1:
        from tqdm.auto import tqdm
        progress = tqdm(total=num_variants, desc="aligning log, completed variants :: ")
    return progress


def __close_progress_bar(progress):
    if progress is not None:
        progress.close()
    del progress