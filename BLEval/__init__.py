
"""
BEELINE Evaluation (:mod:`BLEval`) module contains the following
:class:`BLEval.BLEval` and three additional classes used in the
definition of BLEval class 

- :class:`BLEval.ConfigParser` 
- :class:`BLEval.InputSettings` 
- :class:`BLEval.OutputSettings`


"""
import os
import yaml
import argparse
import itertools
import numpy as np
import pandas as pd
import networkx as nx
from tqdm import tqdm
import multiprocessing
from pathlib import Path
import concurrent.futures
from itertools import permutations
from collections import defaultdict
from multiprocessing import Pool, cpu_count
from networkx.convert_matrix import from_pandas_adjacency


# local imports
from BLEval.parseTime import getTime
from BLEval.computeDGAUC import PRROC
#from BLEval.computeBorda import Borda
#from BLEval.computeJaccard import Jaccard
##from BLEval.computeSpearman import Spearman
#from BLEval.computeNetMotifs import Motifs
#from BLEval.computeEarlyPrec import EarlyPrec
#from BLEval.computePathStats import pathAnalysis
#from BLEval.computeSignedEPrec import signedEPrec


class InputSettings(object):
    '''
    The class for storing the names of input files.
    This initilizes an InputSettings object based on the
    following three parameters.
    

    :param datadir:   input dataset root directory, typically 'inputs/'
    :type datadir: str

    :param datasets:   List of dataset names
    :type datasets: list
        
    :param algorithms:   List of algorithm names
    :type algorithms: list
    '''

    def __init__(self,
            datadir, datasets, algorithms) -> None:

        self.datadir = datadir
        self.datasets = datasets
        self.algorithms = algorithms


class OutputSettings(object):
    '''    
    The class for storing the names of directories that output should
    be written to. This initilizes an OutputSettings object based on the
    following two parameters.
    

    :param base_dir: output root directory, typically 'outputs/'
    :type base_dir: str
    :param output_prefix: A prefix added to the final output files.
    :type str:
    '''

    def __init__(self, base_dir, output_prefix: Path) -> None:
        self.base_dir = base_dir
        self.output_prefix = output_prefix




class BLEval(object):
    '''
    The BEELINE Evaluation object is created by parsing a user-provided configuration
    file. Its methods provide for further processing its inputs into
    a series of jobs to be run, as well as running these jobs.
    '''

    def __init__(self,
            input_settings: InputSettings,
            output_settings: OutputSettings) -> None:

        self.input_settings = input_settings
        self.output_settings = output_settings


    def computeAUC(self, directed = True):

        '''
        Computes areas under the precision-recall (PR) and
        and ROC plots for each algorithm-dataset combination.
      
        Parameters
        ----------
        directedFlag: bool
            A flag to specifiy whether to treat predictions
            as directed edges (directed = True) or 
            undirected edges (directed = False).
        
        :returns:
            - AUPRC: A dataframe containing AUPRC values for each algorithm-dataset combination
            - AUROC: A dataframe containing AUROC values for each algorithm-dataset combination
        '''
        AUPRCDict = {}
        AUROCDict = {}

        for dataset in tqdm(self.input_settings.datasets, 
                            total = len(self.input_settings.datasets), unit = " Datasets"):
            
            AUPRC, AUROC = PRROC(dataset, self.input_settings, 
                                    directed = directed, selfEdges = False, plotFlag = False)
            AUPRCDict[dataset['name']] = AUPRC
            AUROCDict[dataset['name']] = AUROC
        AUPRC = pd.DataFrame(AUPRCDict)
        AUROC = pd.DataFrame(AUROCDict)
        return AUPRC, AUROC
    

    def parseTime(self):
        """
        Parse time output for each
        algorithm-dataset combination.
        
        :returns:
            A dictionary of times for all dataset-algorithm combinations
        """
        TimeDict = dict()

        for dataset in tqdm(self.input_settings.datasets, 
                            total = len(self.input_settings.datasets), unit = " Datasets"):
            timevals  = getTime(self, dataset)
            TimeDict[dataset["name"]] = timevals

        return TimeDict

        

    



class ConfigParser(object):
    '''
    The class define static methods for parsing and storing the contents 
    of the config file that sets a that sets a large number of parameters 
    used in the BLEval.
    '''
    @staticmethod
    def parse(config_file_handle) -> BLEval:
        '''
        A method for parsing the input .yaml file.
        
        :param config_file_handle: Name of the .yaml file to be parsed
        :type config_file_handle: str
        
        :returns: 
            An object of class :class:`BLEval.BLEval`.

        '''
        config_map = yaml.load(config_file_handle)
        return BLEval(
            ConfigParser.__parse_input_settings(
                config_map['input_settings']),
            ConfigParser.__parse_output_settings(
                config_map['output_settings']))
    
    @staticmethod
    def __parse_input_settings(input_settings_map) -> InputSettings:
        '''
        A method for parsing and initializing 
        InputSettings object.
        '''
        input_dir = input_settings_map['input_dir']
        dataset_dir = input_settings_map['dataset_dir']
        datasets = input_settings_map['datasets']

        return InputSettings(
                Path(input_dir, dataset_dir),
                datasets,
                ConfigParser.__parse_algorithms(
                input_settings_map['algorithms']))


    @staticmethod
    def __parse_algorithms(algorithms_list):
        '''
        A method for parsing the list of algorithms
        that are being evaluated, along with
        any parameters being passed.
        
        Note that these parameters may not be
        used in the current evaluation, but can 
        be used at a later point.
        '''
        
        # Initilalize the list of algorithms
        algorithms = []
        
        # Parse contents of algorithms_list
        for algorithm in algorithms_list:
                combos = [dict(zip(algorithm['params'], val))
                    for val in itertools.product(
                        *(algorithm['params'][param]
                            for param in algorithm['params']))]
                for combo in combos:
                    algorithms.append([algorithm['name'],combo])
            

        return algorithms

    @staticmethod
    def __parse_output_settings(output_settings_map) -> OutputSettings:
        '''
        A method for parsing and initializing 
        Output object.
        '''
        output_dir = Path(output_settings_map['output_dir'])
        output_prefix = Path(output_settings_map['output_prefix'])

        return OutputSettings(output_dir,
                             output_prefix)
