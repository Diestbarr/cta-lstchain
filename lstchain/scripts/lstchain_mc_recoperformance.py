#!/usr/bin/env python3

"""
Pipeline to test train three Multi-layer Perceptron/Random Forest destinated to Energy, disp
reconstruction and to Gamma/Hadron separation and test the performance 
of the MLPClassifiers.

Inputs are DL1 files
Outputs are the  MLP/RF trained models

Usage:

$>python lstchain_mc_mlpperformance.py

"""

import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
from distutils.util import strtobool
from lstchain.reco import dl1_to_dl2
from lstchain.reco.utils import filter_events
from lstchain.visualization import plot_dl2
from lstchain.reco import utils
import astropy.units as u
from lstchain.io import standard_config, replace_config, read_configuration_file
from lstchain.io.io import dl1_params_lstcam_key
import time

try:
    import ctaplot
except ImportError as e:
    print("ctaplot not installed, some plotting function will be missing")

parser = argparse.ArgumentParser(description="Train and Apply Random Forests.")

# Required argument
parser.add_argument('--input-file-gamma-train', '--g-train', type=str,
                    dest='gammafile',
                    help='path to the dl1 file of gamma events for training')

parser.add_argument('--input-file-proton-train', '--p-train', type=str,
                    dest='protonfile',
                    help='path to the dl1 file of proton events for training')

parser.add_argument('--input-file-gamma-test', '--g-test', type=str,
                    dest='gammatest',
                    help='path to the dl1 file of gamma events for test')

parser.add_argument('--input-file-proton-test', '--p-test', type=str,
                    dest='protontest',
                    help='path to the dl1 file of proton events for test')

# Optional arguments

parser.add_argument('--store-rf', '-s', action='store', type=bool,
                    dest='storerf',
                    help='Boolean. True for storing trained RF in 3 files'
                         'Default=False, any user input will be considered True',
                    default=True)

parser.add_argument('--batch', '-b', action='store_true', dest='batch',
                    help='Boolean. True for running it without plotting output',
                    default=False)

parser.add_argument('--output_dir', '-o', action='store', type=str,
                    dest='path_models',
                    help='Path to store the resulting RF',
                    default='./saved_models/')

parser.add_argument('--config', '-c', action='store', type=str,
                    dest='config_file',
                    help='Path to a configuration file. If none is given, a standard configuration is applied',
                    default=None
                    )

args = parser.parse_args()

start_time = time.time()

def main():
    custom_config = {}
    if args.config_file is not None:
        try:
            custom_config = read_configuration_file(args.config_file)
        except("Custom configuration could not be loaded !!!"):
            pass

    config = replace_config(standard_config, custom_config)

    reg_energy, reg_disp_vector, cls_gh = dl1_to_dl2.build_models(
        args.gammafile,
        args.protonfile,
        save_models=args.storerf,
        path_models=args.path_models,
        custom_config=config,
    )

    gammas = filter_events(pd.read_hdf(args.gammatest, key=dl1_params_lstcam_key),
                           config["events_filters"],
                           )
    proton = filter_events(pd.read_hdf(args.protontest, key=dl1_params_lstcam_key),
                           config["events_filters"],
                           )

    data = pd.concat([gammas, proton], ignore_index=True)

    dl2 = dl1_to_dl2.apply_models(data, cls_gh, reg_energy, reg_disp_vector, custom_config=config)
    
    #Displays how long it has taken to train the algorithms
    Training_time = (time.time()-start_time)
    Minutes = round(Training_time/60)
    Seconds = round(Training_time%60,3)
    
    print("Training has taken", " %s minutes " % Minutes ,"and", "%s seconds " % Seconds) 

    ####PLOT SOME RESULTS#####

    selected_gammas = dl2.query('reco_type==0 & mc_type==0')

    plot_dl2.plot_features(dl2)
    if not args.batch:
        plt.show()

    plot_dl2.energy_results(selected_gammas)
    if not args.batch:
        plt.show()

    plot_dl2.direction_results(selected_gammas)
    if not args.batch:
        plt.show()

    plot_dl2.plot_disp_vector(selected_gammas)
    if not args.batch:
        plt.show()

    plot_dl2.plot_pos(dl2)
    if not args.batch:
        plt.show()

    plot_dl2.plot_roc_gamma(dl2)
    if not args.batch:
        plt.show()

    plt.hist(dl2[dl2['mc_type'] == 101]['gammaness'], bins=100)
    plt.hist(dl2[dl2['mc_type'] == 0]['gammaness'], bins=100)
    if not args.batch:
        plt.show()


if __name__ == '__main__':
    main()