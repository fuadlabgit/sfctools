__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'dev' # options are: dev, test, prod

from ..core.settings import Settings
from ..core.world import World
from ..core.flow_matrix import FlowMatrix
from pathlib import Path

import sys
import os
from datetime import datetime
import warnings
import pandas as pd


class ModelRunner:
    """
    A model runner is a generic 'frame' for running a model file. It requires a specific folder structure (see constructor).
    The usage of this is optional and voluntary. However, this could be helpful when running Monte-Carlo batches.
    """
    
    def __init__(self, settings_path, results_path, builder, iter):
        """
                
        :param settings_path: str or path to .yml file
        :param results_path: str or path, dir where results are written
        :param builder: executable, method to call when building agents
        :param iter: executable, method to call when iterating one simulation, should have argument N
        
        for number of time periods to run and return a pandas dataframe

        This runs a simulation and create logger files and data files
        
            | ./root
            | |_____output.txt   <<
            | |_____output.txt.errors << will contain all error messages
            | |_____output.txt.progress << will log the progress of the simulation run
            | |
            | |
            | |_____output.txt.0
            | |_____output.txt.1
            | |_____output.txt.2
            | |_____output.txt.3 << will contain the data of the actual runs


        """

        """
        below, we write some header information into some logger files
        The .pogress file 
        The .errors file    
        """

        Path(results_path).mkdir(parents=True, exist_ok=True)

        Settings().read_from_yaml(settings_path)  # read settings from yaml file

        with open(results_path + "output.txt", "w") as file:  # write the meta-info to results directory
            info = Settings().config_data["metainfo"]
            for k, v in info.items():
                file.write(str(k) + ":" + str(v) + "\n")

        with open(results_path + "progress.txt", "w") as file:  # write timestamp to progress logger file
            file.write(str(datetime.now()) + "\n")

        with open(results_path + "errors.txt", "w") as file:  # write timestamp to error file
            file.write(str(datetime.now()) + "\n")

        self.build_agents = builder
        self.iter = iter
        self.settings_path = settings_path
        self.results_path = results_path

    def run(self, M: int, N: int):
        """
        runs a monte-carlo simulation wih M monte carlo runs and N simulation periods per run.
        Outputs are written to logger files.

        :param M: number of monte-carlo runs
        :param N: number of time periods per monte-carlo run
        """

        sys.tracebacklimit = 1

        error_count = 0

        m = 0
        while m < M:

            with open(self.results_path + "progress.txt", "a") as file:
                file.write("[RUN %i]   " % m)

            try:

                World().reset()
                FlowMatrix().reset()

                self.build_agents()  # build the agents

                data = self.iter(N)  # iterate one simulation run

                # sys.stdout.flush()
                # sys.stderr.close()

                data.to_csv(self.results_path + "output.%i" % m,sep="\t",index=False)

                sys.stdout.write("[DATA]" + self.results_path + ".%i\n" % m)

                with open(self.results_path + "output.txt", "a") as file:  # write-append
                    # logging here
                    file.write(self.results_path + "output.%i\n" % m)

                with open(self.results_path + "progress.txt", "a") as file:
                    file.write("...SUCCESS!\n")

                sys.stdout.write("[UPDATE]%.6f\n" % (100. * m / M))

                m += 1

            except Exception as e:

                with open(self.results_path + "progress.txt", "a") as file:
                    file.write("...FAILED\n")

                with open(self.results_path + "errors.txt", "a") as file:

                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    e_str = ":".join([str(exc_type), str(fname), str(exc_tb.tb_lineno)]) +" "+ str(e)

                    file.write("[Error in run %i] " % m + e_str + "\n")

                    warnings.warn("[Error in run %i] " % m + e_str + "\n")

                error_count += 1
                if error_count == 10:
                    error = RuntimeError("ᵒᴼᵒ ✈__✈ █ █ ▄  Got a lot of errors. aborting. something must be wrong, see error logger file.")
                    raise error