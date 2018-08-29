#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 12:56:12 2018

@author: stelios
"""
import numpy as np
from numpy.random import randint, rand
import random
import string
import pandas as pd
import copy
from core_classes import *


def choose_based_on_speed(minters,transaction,minters_df,speed_upper_limit=1000):  
    #a simple minter selection mechanism for broadcasting that chooses minters based on how fast they are
    rand_speeds = randint(0,speed_upper_limit,len(minters))
    
#    for counter,m in enumerate(minters):
#        if rand_speeds[counter]<=m.speed:
#            m.add_transaction(transaction)
    minters_df['passed'] = minters_df.speed > rand_speeds
    selected_ids = minters_df[minters_df['passed']==True].ID.values.tolist()
    
    for m in minters:
        if m.unique_id in selected_ids:
            m.add_transaction(transaction)
            selected_ids.remove(m.unique_id)
    
            
def choose_based_on_random(minters,transaction,minters_df,prob=0.5):
    #choose X% of the minters to receive a broadcasted transaction
    randoms = rand(len(minters))
#    for counter,m in enumerate(minters):
#        if randoms[counter]<=prob:
#            m.add_transaction(transaction)
    minters_df['passed'] = 0.5 > randoms
    selected_ids = minters_df[minters_df['passed']==True].ID.values.tolist()
    
    for m in minters:
        if m.unique_id in selected_ids:
            m.add_transaction(transaction)
            selected_ids.remove(m.unique_id)
            
def choose_based_on_length(minters,minters_df,transaction):
    lengths=[]
    for m in minters:
        lengths.append(len(m.proposed_checkpoint.transactions)+1)
    lengths=np.array(lengths)
    lengths=lengths/(lengths.max())
    
    #if this is the first iteration choose on speed
    if np.sum(lengths)==len(lengths) or rand()<0.1:
       choose_based_on_speed(minters,transaction,speed_upper_limit=1000,minters_df=minters_df) 
    else:
        for counter,m in enumerate(minters):
            if rand()<lengths[counter]:
                m.add_transaction(transaction)
            
            
def initiliaze_users(num_users,wealth,perc_evil=0.0):
    users = []
    for i in range(num_users):
        if rand()<=perc_evil:
            users.append(User(num_tokens=np.abs(np.random.normal(wealth)),evil=True))
        else:
            users.append(User(num_tokens=np.abs(np.random.normal(wealth))))
        
    return users
    
def initialize_minters(num_minters,speeds,perc_evil=0.0,evilness_factor=0.1,
                       perc_compliant=1.0,compliance_number=0.5):
    minters = []
    for m in range(num_minters):
        mint = Minter(speed=speeds[m])
        if rand()<=perc_evil:
            mint.evil = True
            mint.evilness_factor = evilness_factor  
        if rand()>perc_compliant:
            mint.compliant=False
            mint.compliance_number=compliance_number  
                            
        minters.append(mint)
    
    return minters
    
def beacon_selection_default(candidate_minters,minters_df, perc=0.1):
    #simply select an odd number of minters at random, default is 10% of the population
    num_chosen = int(perc*len(candidate_minters))
    if num_chosen % 2==0:
        num_chosen+=1
    
    chosen_ones = random.sample(candidate_minters,num_chosen)
    return chosen_ones
    
def beacon_selection_speed(candidate_minters,minters_df, perc=0.1):
    #select an odd number of minters, based on speed
    num_chosen = int(perc*len(candidate_minters))
    if num_chosen % 2==0:
        num_chosen+=1
    
    speeds = minters_df.speed
    speeds = speeds/(speeds.max()+0.1)
    
    minters_df['passed'] = minters_df.speed > rand(len(candidate_minters))
    minters_df=minters_df[minters_df['passed']==True]
    
    selected = minters_df.sample(num_chosen)
    
    selected_final=[]
    for m in candidate_minters:
        if m.unique_id in selected.ID.values.tolist():
            selected_final.append(m)
            if len(selected_final)==num_chosen:
                break
    
    return selected_final
            
    
        
def beacon_decision_default(selected_minters,percentage):
    #default function simply decide to a checkpoint when the majority is reached
    
    agreement_reached = False
    proposed_checkpoint = None
    num_selected = len(selected_minters)
    #the number of nodes that need to agree. Make sure it is an odd number.
    agreed_required = percentage
    if agreed_required % 2 == 0:
        agreed_required+=1
    
    #this matrix holds information on which minters agree
    match_matrix = np.zeros([num_selected,num_selected])
    
    #check all the checkpoints between the minters
    for counter1, s1 in enumerate(selected_minters):
        for counter2, s2 in enumerate(selected_minters):
            if s1!=s2:
                if s1.proposed_checkpoint==s2.proposed_checkpoint:
                    match_matrix[counter1,counter2]=1
                else:
                   #set1=set(s1.proposed_checkpoint.transactions)
                   #set2=set(s2.proposed_checkpoint.transactions)
                   
                   #if set1.issubset(set2) or set2.issubset(set1):
                   #   match_matrix[counter1,counter2]=1 
                   pass
                   
                   
    
    num_matches = match_matrix.sum(axis=1)/len(match_matrix)*1.0
    for i in range(num_selected):
        if num_matches[i]>=agreed_required:
            proposed_checkpoint = selected_minters[i].proposed_checkpoint
            agreement_reached = True
            break
    
    speeds = []
    ids = []
    for s in selected_minters:
        speeds.append(s.speed)
        ids.append(s.unique_id)
    
    success_df = pd.DataFrame({'id':ids,'num_matches':num_matches,'speed':speeds})

    #keep only potential winners
    winners=success_df['num_matches']>=percentage
    success_df['could_be_winners']=winners
    success_df = success_df[success_df['could_be_winners']==True]
    
    required_num = int(np.ceil(len(selected_minters)*percentage))
    if len(success_df)>=required_num:
        success_df.sort_values('speed',ascending=False,inplace=True)
        #choose the minters that sent the message fast based on speed
        success_df.speed = success_df.speed/(success_df.speed.max()+2*np.abs(np.random.randn()))
        success_df['winner']=False
        
        #write a while loop to find the winners!
        index=0
        patience = 0
        while success_df.winner.sum()<required_num:
            print('trying to find winners iteration number '+str(index))
            if rand()<success_df.speed.values[index]:
                success_df.ix[index,'winner']=True
            index+=1
            if index>=len(success_df)-1:
                index=0
                
            patience+=1
            #if this process cannot generate winners randomly, then all of the minters are the winners
            #this is an arbitrary rule so that the simulation does not get stuck
            if patience>len(selected_minters)*10:
                success_df['winner']=True

    return agreement_reached, proposed_checkpoint        


def agreement_and_reward_function_default(state,selected_minters,agreed_checkpoint,reward):
    state.last_checkpoint = agreed_checkpoint
    not_comply=0
    #all of the minters not in the set update their checkpoints
    for mint in state.minters:
        if mint not in selected_minters:
            mint.set_checkpoint(agreed_checkpoint)
        else:
            if mint.compliant==True:
                if mint.proposed_checkpoint==agreed_checkpoint:
                    mint.tokens+=reward
                else:
                    mint.set_checkpoint(agreed_checkpoint)
            else:
                if rand()<mint.compliance_number:
                    mint.set_checkpoint(agreed_checkpoint)
                else:
                    not_comply+=1
    return not_comply
    
def beacon_shout_default(perc,threshold,state):
    right_time = False
    
    num_chosen = int(perc*len(state.minters))    
    chosen_ones = random.sample(state.minters,num_chosen)
    
    data = []
    
    for minter in chosen_ones:
        data.append(len(minter.proposed_checkpoint.transactions))
        
    #number of transactions required before the beacon shouts
    if np.median(data)>threshold:
        right_time=True
    
    return right_time