__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'dev' # options are: dev, test, prod

from scipy.optimize import minimize,dual_annealing
import subprocess 
import numpy as np 
from functools import partial 
import time 
import os 
import matplotlib.pyplot as plt

"""
Calibration suite for a general model. BETA requires further testing. Usage at own risk.
"""

class DistanceMeasure:
    """
    Generic class for distance measure.
    """

    def __init__(self,method):
        """
        param kind: determines the method that is applied to compute the distance measure
        """
        self.method = method
        self.callable_dict = {
            "rmse": self.rmse
        }

        self.logger = [] # logs all distances computed 

        self.counter = 0

    def d(self, predictions, targets, params, d_params):
        """
        compute the distance 

        :param prediction: vector of predictions y~[t]
        :param targets: vector of targets y[t]
        :param params: vector of fit paramters used to generate y~[t]
        :param d_params: dict of parameters for calculation of distance
        """

        self.counter += 1 
        if self.counter == 10:
            self.counter = 0
            plt.figure()
            plt.style.use("macro")

            colors = ["black","red","blue","lime","magenta","orange"]
            for i in range(predictions.shape[1]):
                plt.plot(predictions[:,i],linestyle="dotted",color=colors[i%len(colors)],alpha=.8)
        
            for i in range(targets.shape[1]):
                plt.plot(targets[:,i],linestyle="solid",color=colors[i%len(colors)])
            
            plt.xlabel("Time")
            plt.ylabel("Value")
            filename = "./figures/" + str(time.time())+ ".png"
            print("filename",filename)
            plt.savefig(filename)
            plt.close()


        if self.method in self.callable_dict:

            callable = self.callable_dict[self.method]
            return callable(predictions,targets,params,d_params) 
        
        else:

            raise NotImplementedError("Could not find any implementation for '%s'" % self.method)



    def rmse(self,predictions, targets, params,d_params): 
        """
        Root-mean-square error

        d_params {"lambda": ...} regularization parameter
        """

        # compute a distance of dimenion of the number of observables in the data (or simulation)
       
        # evaluate the disance with a norm
        d = np.linalg.norm(predictions-targets,ord=2)
        p = d_params["lambda"] # 0.001 # regularization term 
        l = np.sum(np.power(params,2))  # regularization parameter

        L = d + l*p

        self.logger.append(L)

        return L 


class CalibrationRoutine:
    """
    Generic class for model calibration
    """

    def __init__(self, simulation_ref, datashape, param_bounds, param_init, method="scipy", mode="callable"):
        """
        Calibration for models outputting several time series

        :param simulation_ref: 
                in 'shell' mode:  str, path to a python file to be executed as the model      
                in 'callable' mode: 

        :param datashape: tuple (m,n), exected dimensions of output data   
        :param method: method to use for calibration
        :param param_bounds: parameter boundaries dictionary of the form {str(name): tuple(min,max)}
        :param param_init: initial conditions for parameters
        :param mode: 'shell' or 'callable'
        """

        self.method_dict = {
            "scipy": partial(self.calibrate_scipy,method="SLSQP") # uses scipy.optimize to get the work done
        }

        self.simulation_ref  = simulation_ref
        self.param_bounds = param_bounds
        self.x0 = param_init
        self.datashape = datashape 
        self.data_measured = None 

        self.method = method # determine a calibration method
        self.dmeasure = DistanceMeasure("rmse") # define a distance measure

        self.mode = mode
        
    def plot(self):
        plt.figure()
        plt.style.use("macro")
        plt.semilogy(self.dmeasure.logger)
        plt.xlabel("Iteration")
        plt.ylabel("Objective Value")
        plt.title("Learning Curve")
        plt.show()

        self.dmeasure.logger = []

    def iter(self,params):
        """
        run one iteration of the model 
        :param params: a list or arrays of parameters as input to the model
        """

        if self.mode == "shell":

            start = time.time()
            args = " ".join(list(["%.10f"%p for p in params]))
            proc = subprocess.run("python %s %s" % (self.simulation_ref,args), stdout = subprocess.PIPE) # execute process
            bufferfile = proc.stdout.decode("utf-8") # get the output

            print("BUFFERFILE",bufferfile)
            data = np.load(bufferfile)   # read flat data
            os.unlink(bufferfile) # delete the temporary file after reading

            #print("DATA ITER",data)
            data = data.reshape(self.datashape) # re-shape data to original shape

            stop = time.time()
            print("%.2f" % (stop-start)," sec.; ", "DATA",data.shape, "Params", params)
            # print(stop-start)

            return data # return simulated data array

        elif self.mode == "callable":

            calble = self.simulation_ref
            data = calble(params)
            
            return data 

    def calibrate(self, data, n_funcev, d_params):
        """
        calibrate model parameters for a specific model

        :param data: dict of the form {name:array} with the calibration data
        :param n_funcev: number of function evaluations
        :param d_params: parameters for the distance measure
        """

        callable = self.method_dict[self.method] # find the calibration method to use
        callable(data_measured=data,bounds=self.param_bounds,n_funcev=n_funcev,d_params=d_params) # call the calibration method
        self.plot()

    def objective(self,pars,data,d_params):
            """
            opimization objective 

            :param  pars: parameters used to compute y~[t]
            :param data: observed data y[t]
            :pram d_params: parameters for distance measure d(y, y~)

            """
            
            data_measured = data
            self.data_measured = data_measured
            # print("data_simulated",pars)
            data_simulated = self.iter(pars)

            assert data_simulated.shape == self.datashape, "Simulated data has not the expected shape %s. It has shape %s" % (str(self.datashape),str(data_simulated.shape))
            
            dm =  self.dmeasure.d(data,data_simulated,pars,d_params)
            print("d = ", dm, "params", pars)
            
            return dm 


    def plot_fit(self,xi,*args):
        print("ITER")
        print("*args",*args)
        plt.figure()
        plt.style.use("macro")

        colors = ["black","red","blue","lime","magenta","orange"]
        for i in range(self.data_measured.shape[1]):
            plt.plot(self.data_measured[:,i],linestyle="dotted",color=colors[i%len(colors)],alpha=.8)
        
        simu = self.iter(xi)

        for i in range(self.data_measured.shape[1]):
            plt.plot(simu[:,i],linestyle="solid",color=colors[i%len(colors)])
        
        plt.xlabel("Time")
        plt.ylabel("Value")
        filename = "./figures/" + str(time.time())+ ".png"
        print("filename",filename)
        plt.savefig(filename)
        plt.close()


    def calibrate_scipy(self,data_measured,bounds,n_funcev,d_params,method):
        """
        calibration step 

        :param data: ndarray of shape (T,N) where T is the number of time steps and N is the number of different time series in the data
        :param bounds: ndarray of shape (P,2) where P is the number of parameters in the model
        :param n_funcev: desired number of function evaluations
        :param params: dict, further parameters of the calibration routine
        :param n_funcev: number of function evaluations
        """
        
        # 1) construct objective function
        #self.bjective(.):
        
        # 2) choose a starting point for parameters
        # self.x0 

        # 3a) pre-minimize 
        class MyBounds:
            # https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.basinhopping.html
            def __init__(self,xmax,xmin):
                self.xmax = xmax 
                self.xmin = xmin
            
            def __call__(self,**kwagrs):
                x = kwargs["x_new"]
                tmax = bool(np.all(x <= self.xmax))
                tmin = bool(np.all(x >= self.xmin))
                print("accepted", tmax, tmin)
                return tmax and tmin

        my_bounds = MyBounds([b[1] for b in bounds], [b[0] for b in bounds])

        def printfun(x, f, accepted):
            print("at minimum %.4f accepted %d" % (f, int(accepted)))
            # sys.stdout.flush()

        # res = basinhopping(partial(self.objective,data=data), self.x0,niter = 1, T = 10, stepsize=1, disp = True, callback=printfun, accept_test = my_bounds)

        # rough pre-optimization to find a global optimum
        # x0=self.x0
        res = dual_annealing(partial(self.objective,d_params=d_params,data=data_measured), callback=self.plot_fit, bounds = bounds,x0=self.x0,maxiter=10000,maxfun=int(0.1*n_funcev)) # ,tol=0.1,workers=2,bounds=bounds, maxiter= 1)

        # 3) minimize!
        res = minimize(partial(self.objective,d_params=d_params,data=data_measured), res.x, callback=self.plot_fit,  bounds=bounds,method =method, options= {"maxiter": int(0.9*n_funcev)})

        # 4) return result
        self.plot_fit(res.x)

        # TODO maybe save a backup of res before plotting (?) in case the user shuts down the plot with the terminal or so

        print("OPTIMIZAITON RESULT", str(res))
        return res.x 
