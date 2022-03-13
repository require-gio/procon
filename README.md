# procon
procon is an extension to the popular pm4py process mining library with the goal to enable conformance checking on BPMN models.
Assume you have an advanced BPMN 2.0 model, maybe with cancellation features, and you have gathered event data, e.g., from your
ERP or CRM system. You are very likely interested to see how well the real worl process behavior matches the desired process model.
procon gives you the opportunity to do that with only a few lines of Python code!

## Installation
procon can be installed on Python 3.7.x / 3.8.x / 3.9.x by doing:
```bash
pip install -U procon
```

## Example
The following example shows you how to import a bpmn model and an event log to then derive conformance statistics based on them.

```python
import os
import procon

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
```

Input BPMN model:\
<img src="https://github.com/require-gio/procon/blob/release/images/example.png" alt="example" width="700" style="background-color: white"/>


Output Table:\
<img src="https://github.com/require-gio/procon/blob/release/images/example-result.png" alt="example-result" width="700" style="background-color: white"/>


The meaning of the columns is as follows:
* Index/Activity: Name of the activity
* Occurrences: Total occurrences of the activity in the event log
* ![#3d8a0e](https://via.placeholder.com/15/3d8a0e/000000?text=+) `Correct: Number of times the activity appeared at the desired point in time according to the process model`
* ![#de9414](https://via.placeholder.com/15/de9414/000000?text=+) `Wrong Position: Number of times the activity appeared in a case in an undesired order`
* ![#ea0a8e](https://via.placeholder.com/15/ea0a8e/000000?text=+) `Missing: Number of times the activity was completely missing in a case although it was expected to appear`