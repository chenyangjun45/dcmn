# !/usr/bin/env python3
import logging, json
from collections import defaultdict
from ast import literal_eval
import os, sys

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s')
logger = logging.Logger(__name__)
logger.setLevel(logging.INFO)

def load_jsonl(filepath):
    '''
    this function will load a *.jsonl file by the name of filepath,
    note: each line of this file is a dict {}, not standard json
    '''
    logger.info('Load jsonl file from {}'.format(filepath))
    with open(filepath, 'r') as f:
        data = [json.loads(line) for line in f]

    return data

def load_sentences(filepath, keys=['obs1', 'obs2', 'hyp1', 'hyp2']):
    '''
    this function will use load_jsonl to load the jsonl file, extract
    the observations and hypotheses, return list of strings
    '''
    raw_data = load_jsonl(filepath)
    samples = defaultdict(list)
    logger.info('Build the dictionary for each kind of sentences')
    for entry in raw_data:
        for key in keys:
            samples[key].append(entry[key])
    samples_list = list(samples.values())
    ret = [sample for sample in zip(*samples_list)]
    return ret

def load_labels(filepath):
    '''
    this function will load the given label from `filepath`
    '''
    logger.info('Load labels')
    with open(filepath, 'r') as f:
        # the label in original file counts from 1 instead of 0
        ret = [literal_eval(line)-1 for line in f]
    return ret

def _get_threads():
    """ Returns the number of available threads on a posix/win based system """
    if sys.platform == 'win32':
        # return (int)(os.environ['NUMBER_OF_PROCESSORS'])
        return 0    # save trouble, do not use multiprocessing on windows
    else:
        return (int)(os.popen('grep -c cores /proc/cpuinfo').read())