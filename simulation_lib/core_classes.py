#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 20 18:14:33 2018

@author: stelios
"""
import numpy as np
from numpy.random import randint, rand
import random
import string
import pandas as pd
import copy



class Minter:
    last_checkpoint = None
    proposed_checkpoint = None
    #speed is a variable of the power of a minter
    speed  = 10
    #affiliation is the company this mint belongs to
    affiliation = 'the world'
    #evil nodes will try to give false information and pass wrong transactions (that surpass the user's amount)
    evil = False
    evilness_factor = 0.1
    #Compliant nodes will always read the new checkpoint. Otherwise they will stay with the old and
    #maybe renew their checkpoint randomly at the next beacon. This is either malicious behavior
    #or the minter has not been set up appropriately
    compliant=True
    #the percentage probability of the minter complying
    compliance_number=0.5
    
    #geographical parameters
    geo_x = 0
    geo_y = 0
    
    double_spending = 0
        
    tokens = 0
    
    unique_id = None
    
    def __init__(self,speed = 10,evil=False,compliant=True,compliance_number=0.5,evilness_factor=0.1,geo_x=0,geo_y=0):
        self.speed = speed
        self.evil = evil
        self.evilness_factor = evilness_factor
        self.compliant=compliant
        self.compliance_number=compliance_number
        self.unique_id = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(64)])
        self.geo_x = geo_x
        self.geo_y = geo_y

        
    def add_transaction(self,transaction):
        if self.verify_transaction(transaction):
            self.proposed_checkpoint.add_transaction(transaction)
            return True
        else:
            return False
        
    def verify_transaction(self,transaction):
        #write code to check in the dag
        #check whether the amounts make sense
        sender_list = self.proposed_checkpoint.retrieve_sender(transaction.user_a)
        
        total_amount_so_far = 0
        for s in sender_list:
            total_amount_so_far+=s.amount
        
        money_available = self.proposed_checkpoint.users[transaction.user_a.unique_id].num_tokens
        
        if total_amount_so_far+transaction.amount <= money_available:
            return True
        else:
            if not self.evil:     
                return False
            else:
                if rand() < self.evilness_factor:
                    self.double_spending+=1
                    self.proposed_checkpoint.double_spending+=1
                    return True
        
    def set_checkpoint(self,checkpoint):
        self.last_checkpoint = checkpoint
        self.proposed_checkpoint = Checkpoint([],[])
        self.proposed_checkpoint.users = self.last_checkpoint.users.copy()
        

    
class Transaction():
    #send money from user_a to user_b
    user_a=None
    user_b=None
    amount=0
    def __init__(self,user_a,user_b,amount):
        self.user_a = user_a
        self.user_b = user_b
        self.amount = amount
    
         
class User:
    num_tokens = 0
    evil = False
    unique_id = None
    geo_x = 0
    geo_y = 0
    
    def __init__(self,num_tokens=0,geo_x=0,geo_y=0,evil=False):
        self.unique_id = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(64)])
        self.num_tokens=num_tokens
        self.geo_x = geo_x
        self.geo_y = geo_y
        self.evil=evil
        
    def get_tokens(self):
        return self.num_tokens
        
    def add_tokens(self,tokens):
        self.num_tokens+=tokens
        
    def remove_tokens(self,tokens):
        self.num_tokens-=tokens
        
        
    
        
class Checkpoint:
    users = {}
    transactions = []
    unique_id = None
    double_spending = 0
    
    def add_transaction(self,transaction):
        self.transactions.append(transaction)
        
    def __init__(self,users_initial, transactions):
        for user in users_initial:  
            self.users[user.unique_id] = user
        self.transactions = transactions
        self.unique_id = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(24)])
        self.double_spending = 0
        
    def retrieve_sender(self,sender):
        sender_list = []
        for t in self.transactions:
            if t.user_a.unique_id == sender.unique_id:
                sender_list.append(t)
        return sender_list
        
    def __eq__(self, other):
        transactions_match = True
        
        if len(self.transactions)==len(other.transactions):
            for t1 in self.transactions:
                for t2 in other.transactions:
                    if t1 not in other.transactions:
                        transactions_match=False
                        break
        else:
            transactions_match = False
        
        users_match = True
        if len(self.users)==len(other.users):
            for key,item in self.users.items():
                if other.users[key].num_tokens!=item.num_tokens:
                    users_match=False
                    break
        else:
            users_match = False
            
        if users_match and transactions_match:
            return True
        else:
            return False    
        
    
class State_of_the_world: 
    #this function keeps the objective state of the world
    
    last_checkpoint = None
    minters = []
    users = {}
    #this represents the absolute truth in the world
    ground_truth_transactions = []
    #this is the function that is used in order to select the minters that receive broadcasted messages
    client_broadcast_function = None
    
    #stores whether this state was a beacon
    beacon=False
    
    #list of lists with the ground truth produced between checkpoints
    #ground_truth_store = []
    
    #records whether there was an agreement for the last beacon
    agreement=None
    
    #the number of minters that are not complying with the latest checkpoint
    not_comply = 0
    
        
    def verify_transaction(self,transaction):
        #check the transaction by checking the account balances of the users
        #add the transaction to the ground truth
        user_a = self.users[transaction.user_a.unique_id]
        user_b = self.users[transaction.user_b.unique_id]
        amount = transaction.amount
        
        if user_a.num_tokens<=amount:
            user_a.remove_tokens(amount)
            user_b.add_tokens(amount)

        self.ground_truth_transactions.append(transaction)
    
    def broadcast_transactions(self,transactions):
        #send the transactions to the minters, and add them to the state of the world if they are valid
        for t in transactions:
            self.client_broadcast_function(minters=self.minters,minters_df=self.minters_df,transaction=t)
            self.verify_transaction(t)
        return
        
    def reset(self):
        self.ground_truth_transactions = []
        return 
        
    def __init__(self,users,minters,client_broadcast_function):
        self.client_broadcast_function = client_broadcast_function
        for user in users:  
            self.users[user.unique_id] = user       
        self.minters = minters
        self.ground_truth_transactions = [] 
        self.last_checkpoint = Checkpoint(users,[])
        
        for m in minters:
            m.set_checkpoint(self.last_checkpoint)
        
        self._make_minter_df()
            
        
        #trick to speed up computations
    def _make_minter_df(self):
        data = []
        
        for m in self.minters:
            data.append({'ID':m.unique_id,'speed':m.speed})
            
        df = pd.DataFrame(data)
        
        self.minters_df=df 
    
        
        
class Simulation:
    state = None
    #determines the percentage of active users per cycle
    transaction_volume = 0.1
    beacon_selection = None
    beacon_decision = None
    beacon_percentage=0.1
    beacon_threshold=20
    percentage_decision = 0.6
    percentage_selection = 0.1
    reward = 1 
    
    
    def __init__(self,users,minters,client_broadcast_function,beacon_selection,
                 beacon_decision,agreement_and_reward_function,reward,beacon_shout_function,
                 percentage_decision=0.6,evil_functions=[],
                 transaction_volume=0.1,percentage_selection=0.1,
                 beacon_percentage=0.1,beacon_threshold=20):
        self.state = State_of_the_world(users,minters,client_broadcast_function)
        self.transaction_volume = transaction_volume
        self.beacon_selection = beacon_selection
        self.beacon_decision = beacon_decision
        self.percentage_decision = percentage_decision
        self.agreement_and_reward_function = agreement_and_reward_function
        self.reward = reward
        self.percentage_selection = percentage_selection
        self.beacon_shout_function=beacon_shout_function
        self.beacon_percentage=beacon_percentage
        self.beacon_threshold=beacon_threshold
        

                
        
    def run_iter(self):
        #reset transactions for this iteration
        self.state.reset()
        active_users = []
        transactions = []
        
        #generate transactions
        for u in self.state.users.items():
            if rand() < self.transaction_volume:
                active_users.append(u)
            
        for key,user1 in active_users:
            extra=0
            if user1.evil:
                #if the user is evil the he will try to move some random amount irrespective
                #of the total tokens he possesses
                amount = abs(np.random.normal(user1.num_tokens))
                extra = amount - user1.num_tokens
                amount = user1.num_tokens
            else:
                #use a power of 4 to bias the amounts moved towards smaller fractions of the total account
                amount = user1.num_tokens*rand()**4
            user2 = random.choice(active_users)[1]
            
            if user1.unique_id!=user2.unique_id:
                transactions.append(Transaction(user_a=user1,user_b=user2,amount=amount))
                
            if extra>0:
                user3 = random.choice(active_users)[1]
                if user1.unique_id!=user3.unique_id:
                    transactions.append(Transaction(user_a=user1,user_b=user3,amount=extra))
                            
        self.state.broadcast_transactions(transactions)
        self.state.beacon=False
        
        return self.state
    
    def run_beacon(self):
        #find the set of minters to decide on the new checkpoint   
        selected = self.beacon_selection(candidate_minters=self.state.minters,
                                         minters_df=self.state.minters_df,perc=self.percentage_selection)  
        
        agreement, new_checkpoint = self.beacon_decision(selected,self.percentage_decision)
        new_state=0
                        
        #update the checkpoint for the state of the world
        if agreement:
            not_comply=self.agreement_and_reward_function(state=self.state,selected_minters=selected,
                                               agreed_checkpoint=new_checkpoint,reward=self.reward)
            self.state.not_comply=not_comply
        
        self.state.beacon=True
        self.state.agreement=agreement    
        
        return agreement
        
    def beacon_shout(self):
        
        right_time = self.beacon_shout_function(state=self.state,perc=self.beacon_percentage,
                                                threshold=self.beacon_threshold)
        
        return right_time

        
        
class Recorder:
    states = None
    
    def __init__(self):
        self.states = []
    
    def read_simulation(self,simulation):
        self.states.append(copy.deepcopy(simulation.state))
        
    def detect_double_spending_across_all_minters(self):
        #return a pandas dataframe with minters and double spending across epochs
        result = []
        
        for t in self.states:
            double_spending=0
            for m in t.minters:
                double_spending+=m.double_spending
            result.append(double_spending)
                
        return result
        
    def detect_double_spending_in_main_checkpoint(self):
        #return a pandas dataframe with double spending for the main checkpoint
        result = []
        
        for t in self.states:
            result.append(t.last_checkpoint.double_spending)
                
        return result
        
        
    def get_users_wealth(self):
        #return a pandas dataframe with users and their wealth across all epochs
        #PROBABLY not very useful as the wealth of the users is assumed to stay stable
        return
        
    def get_checkpoints(self):
        #return a pandas dataframe where each row is a minter
        #and each column is an epoch, and each cell describes the checkpoint they are using.
        
        index = []
        for m in self.states[0].minters:
            index.append(m.unique_id)
        df = pd.DataFrame(np.zeros([len(self.states[0].minters),len(self.states)]),index=index)
        
        for i in range(len(self.states)):
            for m in self.states[i].minters:
                df.ix[m.unique_id,i] = m.last_checkpoint.unique_id
        
        return df
        
    def get_agreement_for_accounts(self):
        #checks whether the account balances held for all users are in accordance between minters
        #this function is only using the last state of the simulation
        
        #return value is the total number of incosistent accounts across checkpoints
        #and the total number of accounts which are wrong in the main checkpoint
        minters_amounts = []
        
        for m in self.states[len(self.states)-1].minters:
            for key,user in m.last_checkpoint.users.items():
                minters_amounts.append([m.unique_id,user.unique_id,user.num_tokens])
                
        df = pd.DataFrame(minters_amounts,columns=['minters','users','user_balance'])
        
        common_checkpoint = self.states[len(self.states)-1].last_checkpoint
        
        main_check_inco=0
        inconsistent=0
        for user_id in df.users:
            df2=df.ix[df.users==user_id]
            if len(df2.user_balance.unique())>1:
                inconsistent+=1   
            
            #check whether the amount held in the last checkpoint is the majority
            accepted_amount = common_checkpoint.users[user_id].num_tokens
            percentages = df2.user_balance.astype('category').value_counts()/len(df2)
            dominant_amount = percentages[percentages==percentages.max()].index[0]
            if dominant_amount!=accepted_amount:
                main_check_inco+=1
                
        
        return main_check_inco,inconsistent
        
        
    def get_loser_nodes(self):
    #gets nodes that never got any reward   
        num=0
        
        for m in self.states[len(self.states)-1].minters:
            if m.tokens==0:
                num+=1                
        return num
        
    def get_num_compliant_nodes(self):
        
        result=[]
        
        checks = self.get_checkpoints()
        
        for counter,s in enumerate(self.states):
            main_checkpoint = s.last_checkpoint
            compliance = np.sum(checks.ix[:,counter]==main_checkpoint.unique_id)/len(checks)
            result.append(compliance)
            
        return result
        
    def get_num_transactions(self):
        #return the total number of transactions per epoch
        trans = []
        
        for t in self.states:
            trans.append(len(t.ground_truth_transactions))
        
        return trans
        
    def get_circulation(self):
        #get the total amount of tokens circulating each epoch
        
        return

    def get_minters_tokens(self):
        index = []
        for m in self.states[0].minters:
            index.append(m.unique_id)
        df = pd.DataFrame(np.zeros([len(self.states[0].minters),len(self.states)]),index=index)
        
        for i in range(len(self.states)):
            for m in self.states[i].minters:
                df.ix[m.unique_id,i] = m.tokens
        
        return df  
        
    def get_not_compliant(self):
        #get the number of minters which are not compliant to the last checkpoint
        result = []
        
        for t in self.states:
            result.append(t.not_comply)
                
        return result
        
    def get_beacons_and_agreements(self):
        res = []
        for counter,s in enumerate(self.states):
            if s.beacon==True:
               res.append([counter,s.agreement]) 
        
        df = pd.DataFrame(res)
        df.columns=['iteration','agreement']
        return df
        
    def get_orphan_transactions(self):
        all_trans = []
        ground_truth = []
        
        #aggregate all transactions
        for t in self.states:
            for k in t.last_checkpoint.transactions:
                all_trans.append(k)
            for j in t.ground_truth_transactions:
                ground_truth.append(j)
            
        all_trans=np.array(all_trans)
        all_trans=np.ndarray.flatten(all_trans)
        
        ground_truth=np.array(ground_truth)
        ground_truth=np.ndarray.flatten(ground_truth)
        
        difference = set(ground_truth) - set(all_trans)
        
        return len(difference)
        
    def get_gini(self):
        last_state=self.states[len(self.states)-1]
        wealth=[]
        for m in last_state.minters:
            wealth.append(float(m.tokens))
        gini=self._gini_coef(np.array(wealth))
        return gini
        
    def get_speeds(self):
        last_state=self.states[len(self.states)-1]
        speed=[]
        for m in last_state.minters:
            speed.append(float(m.speed))
        
        return np.mean(speed)
        
            
    def _gini_coef(self,array):
        """Calculate the Gini coefficient of a numpy array."""
        # based on bottom eq: http://www.statsdirect.com/help/content/image/stat0206_wmf.gif
        # from: http://www.statsdirect.com/help/default.htm#nonparametric_methods/gini.htm
        array = array.flatten() #all values are treated equally, arrays must be 1d
        if np.amin(array) < 0:
            array -= np.amin(array) #values cannot be negative
        array += 0.0000001 #values cannot be 0
        array = np.sort(array) #values must be sorted
        index = np.arange(1,array.shape[0]+1) #index per array element
        n = array.shape[0]#number of array elements
        return ((np.sum((2 * index - n  - 1) * array)) / (n * np.sum(array))) #Gini coefficient
        
        
    
        


        
    