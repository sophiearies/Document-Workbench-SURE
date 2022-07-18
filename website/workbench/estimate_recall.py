# File: estimate_recall.py
# Purpose: Runs point process (inhomogenous Poisson Process with exponential rate function) to estimate number of
#          relevant documents remaining in the ranking following screening of top-ranked documents. 
# Author: Mark Stevenson
# 1/7/2022


# IMPORT LIBRARIES
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import poisson

# GLOBAL PARAMETERS
min_rel_in_sample = 20 # min number rel docs must be initial sample to proceed with algorithm 
n_windows = 10  # number of windows to make from sample
des_prob = 0.95  # Confidence in estimate of number of remaining relevant documents
                 # (e.g. 0.95 means number of remaining documents will be no more than estimate, with 95% confidence) 


# Exponential model 
def exp_model_func(x, a, k): # x = vector x values
    return a*np.exp(-k*x)  


# Integral of model functions
def model_integral(a, k, n_docs):
    return (a/-k)*(np.exp(-k*n_docs)-1)


# fn to define windows of indexes to examine 
def make_windows(n_windows, n_samp_docs, n_docs):

    # n_samp_docs = int(round(n_docs*sample_prop))
    window_size = int(n_samp_docs/n_windows)
    w_e = window_size  # end index current last window
    windows = [(0,w_e)]  # window (x,y) = window from rank x+1 to idx y

    while w_e < n_samp_docs:
        w_s =  windows[-1][-1] 
        w_e = w_s  + window_size 
        windows.append((w_s,w_e))
    
    windows = windows[:-1]

    return(windows)
    
    
 # fn to calculate points that will be used to fit curve
def get_points(windows, window_size, rel_list):

    # x-values are midpoints between start and end of windows
    x = [round(np.mean([w_s,w_e])) for (w_s,w_e) in windows]

    # y-values are the rate at which relevant documents occur in the window
    # ex: rate 0.1 = 0.1 rel docs per doc, or 1 in 10 docs are relevant
    y = [np.sum(rel_list[w_s:w_e]) for (w_s,w_e) in windows]
    y = [y_i/window_size for y_i in y]

    # convert lists to numpy arrays
    x = np.array(x)
    y = np.array(y)

    return (x,y)

 # function to predict max number of relevant documents
def run_poisson_cdf(des_prob, n_docs, mu):

    i = 0
    cum_prob = poisson.cdf(i, mu)
    while  (i < n_docs) and (cum_prob < des_prob):
        i += 1 
        cum_prob = poisson.cdf(i, mu)

    return i




# Function to run point process approach (inhomogenous poisson process)
def predict_unseen_rel(n_docs, rel_list): 
    # n_docs: total number of documents in collection
    # rel_list: binary list of relevance judgements for documents screened so far (in order they were screened)
    #
    # Returns: estimated number of relevant documents in unscreened portion (or -1 if unable to make estimate) 


    # Count number of documents that have been screened, and number of those which are relevant
    n_samp_docs = len(rel_list)
    rel_count = np.sum(rel_list)

    
    pred_unobserved = -1  # Estimated number of relevant documents remaining (-1 == unable to make estimate)
    # Check that enough relevant documents have been observed
    if(rel_count >= min_rel_in_sample):
        # get points
        windows = make_windows(n_windows, n_samp_docs, n_docs)
        window_size = windows[0][1]

        # calculate points that will be used to fit curve
        x,y = get_points(windows, window_size, rel_list)  
       
        # print(f"x: {x}\ny: {y}")

        # try to fit curve
        good_curve_fit = 0
        try:
            p0 = [0.1, 0.001 ]  # initialise curve parameters
            opt, pcov = curve_fit(exp_model_func, x, y, p0)  # fit curve
            good_curve_fit = 1
    
        except Exception as error: 
            pass
            # e = str(error)
            # print(e)
                
        # Run point process 
        if(good_curve_fit == 1):
            # get y-values for fitted curve                    
            a, k = opt
            y2 = exp_model_func(x, a, k) 
 
        # Check error in curve fit (using normalised RMSE)
        #predicted_y = exp_model_func(x, a, k)

        #residuals = np.array(y - predicted_y)
        #diff = np.max(y) - np.min(y)
        #norm_rmse = sum(residuals**2) / diff

      
        # if(norm_rmse < 0.05):
        #if(norm_rmse < 1):

        # Run point process (Inhomogenous Poisson)
        mu = model_integral(a, k, n_docs) - model_integral(a, k, n_samp_docs)
        pred_unobserved = run_poisson_cdf(des_prob, n_docs, mu)

            
        return pred_unobserved
 


def main():
    number_of_docs = 1000
    rel_list = [1, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1]
    rel_list = [1, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0]

    predicted_unseen_rel = predict_unseen_rel(number_of_docs, rel_list)
    print(f"predicted_unseen_rel: {predicted_unseen_rel}")
    
    print(type(number_of_docs))
    print(type(rel_list))

    
if __name__ == "__main__":
    main()
