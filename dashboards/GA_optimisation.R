#****CHOICES******
df = read.csv('/Users/stelios/Dropbox/Freelance/Qredo/simulation/final_data/use_case3_all.csv')
response_choose = c('dspend','failed','orphans')
response_choice = response_choose[2]
pop_size = 200
iters=500
island=TRUE

perc_evil_users=0.6
perc_evil_minters=0.6

evil_sim=TRUE 

#******CODE*********
library(GA)
df$transactions_threshold_to_beacon = df$beacon_num_trans_threshold/df$mean_num_transactions
df$dspend_to_users = df$dspend_all/df$num_users
df$minters_to_users = df$num_minters/df$num_users
df$losers_to_minters = df$loser_nodes/df$num_minters
df$orphans_to_total= df$num_orphan_transactions/(df$mean_num_transactions*100)
df$beacon_percentage_selection=df$broadcast_percentage_selection
#print(head(df))

df$detected_dspend = as.factor(df$dspend_main>0 & df$failed=='False')

if (response_choice=='dspend'){
response = df$detected_dspend
}else if(response_choice=='failed'){
response = df$failed
}else if(response_choice=='orphans'){
response = df$orphans_to_total
}

library(randomForest)
model = randomForest(response~transactions_threshold_to_beacon+minters_to_users
                    +transaction_volume+decision_thres+perc_evil_minters+perc_evil_users+average_minter_speed+
                      broadcast_percentage_selection,data=df,mtry=7,probability = TRUE,keep.inbag = TRUE)
model



lbound = c(0.01,0.01,0.01,500,0.50001,0.01)
rbound = c(0.9,100,0.2,10000,0.9,0.9)



f<-function(x,regression){
  
  artificial_df = df[1,]
  
  artificial_df$minters_to_users = x[1]
  artificial_df$transactions_threshold_to_beacon = x[2]
  artificial_df$transaction_volume = x[3]
  artificial_df$average_minter_speed = x[4]
  artificial_df$decision_thres = x[5]
  artificial_df$perc_evil_users = perc_evil_users
  artificial_df$perc_evil_minters = perc_evil_minters
  artificial_df$beacon_percentage_selection = x[6]
  
  
  
  if (regression==TRUE){
    if (evil_sim){
      score=predict(model,artificial_df)
      
    }else{
      score=-predict(model,artificial_df)
      
    }
  }else if(regression==FALSE){
    if (evil_sim){
      score=predict(model,artificial_df,type='prob')[2]
    }else{
      score=predict(model,artificial_df,type='prob')[1]
    }
  }
  return(score)
  
}

if (response_choice=='orphans'){
  fitnessf = function(x) f(x,regression=TRUE)
}else{
  fitnessf = function(x) f(x,regression=FALSE)
}



if (island){
GA <- gaisl(type = "real-valued", 
            fitness =  function(x) fitnessf(x),
            lower = lbound, upper = rbound, 
            popSize = pop_size, 
            maxiter = iters, run = 100,
            numIslands = 4, 
            migrationRate = 0.2,
            migrationInterval = 20)
}else{
  GA <- ga(type = "real-valued", fitness=fitnessf , lower = lbound, 
           upper = rbound,popSize=pop_size,maxiter=iters)
}

plot(GA)
summary(GA)

sol=GA@solution[1,]
minters_to_users = sol[1]
transactions_threshold_to_beacon = sol[2]
transaction_volume = sol[3]
average_minter_speed = sol[4]
decision_thres = sol[5]
beacon_percentage_selection = sol[6]

print('SOLUTION:')
results=data.frame(minters_to_users,transactions_threshold_to_beacon,transaction_volume,
           average_minter_speed,decision_thres,beacon_percentage_selection)
print(results)

print(paste('Final fitness: ',fitnessf(sol)))
