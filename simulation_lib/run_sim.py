#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 12:53:56 2018

@author: stelios
"""

import numpy as np
from numpy.random import randint, rand
import random
import string
import pandas as pd
import copy
import pandas as pd
from scenario_functions import *
import sys, getopt
import os.path



def run_sim(num_users,users_wealth,perc_evil_users,num_minters,minters_speeds,
            perc_evil_minters,evilness_factor,perc_compliant,compliance_number,client_broadcast_function,
            beacon_selection_function,beacon_decision_function,agreement_reward_function,beacon_shout_function,
            decision_threshold_percentage,percentage_selection,transaction_volume,beacon_percentage,
            beacon_threshold,iters):
    
    users_init = initiliaze_users(num_users,users_wealth,perc_evil=perc_evil_users)
    minters_init = initialize_minters(num_minters,minters_speeds,
                                      perc_evil=perc_evil_minters,evilness_factor=evilness_factor,
                                      perc_compliant=perc_compliant,
                                      compliance_number=compliance_number)
    
    sim = Simulation(users=users_init,minters=minters_init,
                     client_broadcast_function = client_broadcast_function,
                     beacon_selection=beacon_selection_function,
                     beacon_decision = beacon_decision_function,
                     agreement_and_reward_function = agreement_reward_function,
                     percentage_decision=decision_threshold_percentage,
                     reward=1,percentage_selection=percentage_selection,
                     transaction_volume=transaction_volume,
                     beacon_shout_function=beacon_shout_function,
                     beacon_percentage=beacon_percentage,
                     beacon_threshold=beacon_threshold)
    
    rec = Recorder()
    
    failed=False
    #measures whether the beacon ever shouted
    beacon_shout=False
    kill_sim=False
    for i in range(iters):
        if kill_sim:
            break
        print(i)
        #choose users and add some transactions
        #the speed determines which nodes get the transactions first
        if sim.beacon_shout():
            beacon_shout=True
            agreement = sim.run_beacon()
            if not agreement:
                print('no agreement reached!')
                j=0
                while not sim.run_beacon():
                    print('trying to reach agreement')
                    j+=1
                    if j>10:
                        print('impossible to reach consensus!')
                        kill_sim=True
                        failed=True
                        break
                    pass
            else:
                print('agreement reached')
        else:
            sim.run_iter()
        rec.read_simulation(sim)
        
    checks = rec.get_checkpoints()
    trans = rec.get_num_transactions()
    dspend = rec.detect_double_spending_in_main_checkpoint()
    dspend_all = rec.detect_double_spending_across_all_minters()
    #mint_tokens = rec.get_minters_tokens()
    #nc = rec.get_not_compliant()
    #beacons = rec.get_beacons_and_agreements()
    num_losers = rec.get_loser_nodes()
    num_orphans = rec.get_orphan_transactions()
    gini = rec.get_gini()
    av_speeds=rec.get_speeds()
    
    data = {'num_orphan_transactions':num_orphans,'loser_nodes':num_losers,'dspend_main':sum(dspend),
            'dspend_all':sum(dspend_all),'failed':failed,'mean_num_transactions':np.mean(trans),
            'num_minters':num_minters,'num_users':num_users,'perc_evil_users':perc_evil_users,
            'perc_evil_minters':perc_evil_minters,'decision_thres':decision_threshold_percentage,
            'broadcast_percentage_selection':percentage_selection,'majority_threshold':beacon_percentage,
            'beacon_num_trans_threshold':beacon_threshold,'transaction_volume':transaction_volume,'gini':gini,
            'average_minter_speed':av_speeds,'beacon_shout':beacon_shout}

    return data
    
def monte_carlo(iters=100,client_broadcast_function=None,beacon_selection_function=None):
    #SIMULATION PARAMETERS
    users_wealth = 1000
    num_users = randint(100,500)
    #The upper limit is 2500
    num_minters = randint(50,120)
    minters_speeds = randint(500,randint(1000,20000),num_minters)
    
    perc_compliant=1.0
    compliance_number=1.0
    
    perc_evil_users=np.random.uniform(0,0.7)
    perc_evil_minters=np.random.uniform(0,0.7)
    evilness_factor=0.5
    
    decision_threshold_percentage=rand()
    if decision_threshold_percentage<0.5:
        decision_threshold_percentage=0.50001
        
    #how many minters to choose to form the next checkpoint
    percentage_selection=np.random.uniform(0.05,0.5)
    
    ##how many minters to sample before deciding on shouting the beacon
    beacon_percentage=0.2
    #how many transactions need to be recorded (median num transactions sampled across all minters)
    #before the beacon shouts
    beacon_threshold = randint(10,int(num_users*2))
    
    transaction_volume = np.random.uniform(0,0.2)
    
    iters = iters
    
    if client_broadcast_function==None:
        client_broadcast_function=choose_based_on_speed
    if beacon_selection_function==None:
        beacon_selection_function=beacon_selection_speed
    beacon_decision_function=beacon_decision_default
    agreement_reward_function=agreement_and_reward_function_default
    beacon_shout_function=beacon_shout_default
    
    
    df_results = run_sim(num_users=num_users,users_wealth=users_wealth,perc_evil_users=perc_evil_users,
                         num_minters=num_minters,minters_speeds=minters_speeds,
            perc_evil_minters=perc_evil_minters,evilness_factor=evilness_factor,
            perc_compliant=perc_compliant,compliance_number=compliance_number,
            client_broadcast_function=client_broadcast_function,
            beacon_selection_function=beacon_selection_function,
            beacon_decision_function=beacon_decision_function,decision_threshold_percentage=decision_threshold_percentage,
            agreement_reward_function=agreement_reward_function,beacon_shout_function=beacon_shout_default,
            percentage_selection = percentage_selection,transaction_volume=transaction_volume,
            beacon_percentage=beacon_percentage,beacon_threshold=beacon_threshold,iters=iters)
     
    return df_results       

#store = []
#total_iters = 100
#for it in range(0,total_iters):
#    store.append(monte_carlo(100,))
#
#df = pd.DataFrame(store)


def main(argv):
    inputfile = ''
    outputfile = ''
    use_case = 1
    it=10
    try:
        opts, args = getopt.getopt(argv,"ho:u:r:",["ofile=","use_case=","iterations="])
    except getopt.GetoptError:
        print('run_sim.py -o <outputfile> -u <use_case> -r <iterations>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('run_sim.py -o <outputfile> -u <use_case> -r <iterations>')
            sys.exit()
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in("-u","--use_case"):
            use_case = int(arg)
        elif opt in("-r","--iterations"):
            it = int(arg)       
    print(args)
    print('Output file is "', outputfile)
    print('Use case is ', str(use_case))
    print('Num iterations are ', str(it))
    
    if use_case==1:
        client_broadcast_function=choose_based_on_random
        beacon_selection_function=beacon_selection_default
    elif use_case==2:
        client_broadcast_function=choose_based_on_random
        beacon_selection_function=beacon_selection_speed
    elif use_case==3:
        client_broadcast_function=choose_based_on_speed
        beacon_selection_function=beacon_selection_default
    elif use_case==4:
        client_broadcast_function=choose_based_on_speed
        beacon_selection_function=beacon_selection_speed
    elif use_case==5:
        client_broadcast_function=choose_based_on_length
        beacon_selection_function=beacon_selection_default
    
    store=[]
    for it in range(0,it):
        print('iteration number:'+str(it))
        store.append(monte_carlo(50,client_broadcast_function,beacon_selection_function))
        df = pd.DataFrame(store)
        if it>0 or os.path.isfile(outputfile):
            df = df.ix[df.shape[0]-1:,:]
            df.to_csv(outputfile,header=False,mode='a+')
        else:
            df.to_csv(outputfile)

if __name__ == "__main__":
    main(sys.argv[1:])