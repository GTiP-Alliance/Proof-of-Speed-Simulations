df = read.csv('/Users/stelios/Dropbox/Freelance/Qredo/simulation/use_case_3_all.csv')

df$X=NULL
#create new variables
df$transactions_threshold_to_beacon = df$beacon_num_trans_threshold/df$mean_num_transactions
df$dspend_to_users = df$dspend_all/df$num_users
df$minters_to_users = df$num_minters/df$num_users
df$losers_to_minters = df$loser_nodes/df$num_minters

#detect if double spending exists int he main
sum(df$dspend_main)



#understand what makes a simulation fail
m_logistic = glm(df$failed~df$transactions_threshold_to_beacon+df$minters_to_users
                 +df$transaction_volume+df$decision_thres+df$perc_evil_minters+df$perc_evil_users+
                   df$majority_threshold,family=binomial(link='logit'))


#understand loser nodes (nodes with no reward)
m_losers = lm(df$losers_to_minters~df$transactions_threshold_to_beacon+df$minters_to_users
       +df$transaction_volume+df$decision_thres+df$perc_evil_minters+df$perc_evil_users+
         df$majority_threshold)

#understand double spend
m_dspend = lm(df$dspend_to_users~df$transactions_threshold_to_beacon+df$minters_to_users
       +df$transaction_volume+df$decision_thres+df$perc_evil_minters+df$perc_evil_users+
         df$majority_threshold)
summary(m_dspend)


