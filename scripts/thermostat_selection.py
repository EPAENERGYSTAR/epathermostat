import numpy as np 
import pickle 
#Package Notes, Natsort 5.0.1 
from natsort import natsorted 
 
#DEBUG: state caching 
prng_state_exact = np.random.get_state() 
 
#DEBUG: Save state via pickle 
with open('prng_state.pickle','wb') as f: 
    pickle.dump(prng_state_exact,f) 
 
# #DEBUG: Code to load old state and set PRNG to that state 
# with open('prng_state.pickle','rb') as f: 
#     reload_state = pickle.load(f) 
# np.random.set_state(reload_state) 
 
#Load sample target data; Note if 0:n index replaced with data/thermostat id's, will sample unique id's instead of indicies 
EIAColdVCold = np.arange(500) 
EIAHotHumid = np.arange(500) 
EIAMixedHumid = np.arange(500) 
EIAHDMD = np.arange(500) 
EIAMarine = np.arange(500) 
 
#Natural Sort Imported data by value 
SampEIAColdVCold = natsorted(SampEIAColdVCold) 
SampEIAHotHumid = natsorted(SampEIAHotHumid) 
SampEIAMixedHumid = natsorted(SampEIAMixedHumid) 
SampEIAHDMD = natsorted(SampEIAHDMD) 
SampEIAMarine = natsorted(SampEIAMarine) 
 
#Sample target data, applying 1 seed per climate zone 
np.random.seed(101) 
SampEIAColdVCold = np.random.choice(EIAColdVCold,250, replace=False ) 
np.random.seed(102) 
SampEIAHotHumid = np.random.choice(EIAHotHumid,250, replace=False ) 
np.random.seed(103) 
SampEIAMixedHumid = np.random.choice(EIAMixedHumid,250, replace=False ) 
np.random.seed(104) 
SampEIAHDMD = np.random.choice(EIAHDMD,250, replace=False ) 
np.random.seed(105) 
SampEIAMarine = np.random.choice(EIAMarine,250, replace=False ) 
 
#Sort Sampled data by value 
SampEIAColdVCold = np.sort(SampEIAColdVCold) 
SampEIAHotHumid = np.sort(SampEIAHotHumid) 
SampEIAMixedHumid = np.sort(SampEIAMixedHumid) 
SampEIAHDMD = np.sort(SampEIAHDMD) 
SampEIAMarine = np.sort(SampEIAMarine) 
 
#Create matrix for all samples, Matrix format best for indicies 
SortedEIASample = np.vstack((SampEIAColdVCold,SampEIAHotHumid,SampEIAMixedHumid,SampEIAHDMD,SampEIAMarine)) 
 
#Create long format output, best for vector of thermostat id's 
results = SampEIAColdVCold 
outfile = np.append(results,[SampEIAHotHumid,SampEIAMixedHumid,SampEIAHDMD,SampEIAMarine]) 
 
#Save Sample items to file 
np.savetxt('PRNG.csv',SortedEIASample, delimiter=",") 
np.savetxt('PRNGvector.csv',outfile, delimiter=","
