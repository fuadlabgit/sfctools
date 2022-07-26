import numpy as np
import pandas 
from datetime import datetime
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt


def convert_quarterly_to_datetime(df):
    """
    converts a dataframe with a string index of form '2020-Q2' (typical Eurostat format)
    to a dataframe with a datetime index 

    :param df: a pandas dataframe
    :return: df_converted, a pandas dataframe with datetime-formatted index
    """
    # https://stackoverflow.com/questions/53898482/clean-way-to-convert-quarterly-periods-to-datetime-in-pandas
    df.index = pandas.PeriodIndex(df.index, freq='Q').to_timestamp()

    return df 


def convert_numeric(df):
    """
    converts all column of a dataframe 
    
    :param df: a pandas dataframe
    :return: converted dataframe
    """

    for column in df.columns:
        df[column] = pandas.to_numeric(df[column])

    print("df\n",df)
    return df 



def stretch_to_length(df,new_length,method="cubic"):
    """
    stretches a dataframe with datetime index to a new, higher length (by interpolation of the values).
    
    :param df: a pandas data frame with datetime-formatted index
    :param new_length: new desired length 
    :param method: intrepolation style (default 'cubic')

    :return df_new: the stretched dataframe
    """
    factor = (new_length/(len(df)))
    assert factor > 1.0, "new_length smaller than original length. aborting."
    df_new = stretch_pandas(df, factor, kind=method)
    assert len(df_new) == new_length, "internal error."
    return df_new 


def stretch_datetime(x, factor):
    """
    stretches a series or array containing datetime objects by a certain factor

    :param x: an array 
    :param factor: int, factor > 1 by which to stretch the data
    """
    x = np.array(x)

    assert type(x[0]) == datetime.date or np.issubdtype(x.dtype, np.datetime64), "Data index does not seem to be datetime. It is %s" % type(x[0])
    assert factor >= 1.0, "streching by less than factor 1.0 impossible."

    dt = max(x)-min(x)
    sign = 1
    if x[1] < x[0]:
        sign = -1

    ds = sign * dt/((len(x))*factor -1)

    new_ar = []

    if ds >= 0:
        #print("dt >=0")
        s = min(x) # x[0]

        while s <= max(x): #[-1]:
            #print("s", s)
            new_ar.append(s)
            s += ds

    elif ds < 0:
        #print("dt< 0","max,min",max(x),min(x))
        s = max(x)

        while s >= min(x):
            new_ar.append(s)
            #print("s", s)
            s += ds

    #print("stetch")
    #print(len(x))
    #print(len(new_ar))
    return pandas.Series(new_ar)


def interpolate(y,stretch_factor,kind="cubic"):
    """
    interpolates an array using scipy interp1d. 

    x is datetime, y is float or somehow numerical
    stretch_factor = 3 # quarter to month
    """
    x = np.arange(len(y))
    f = interp1d(x, y, kind=kind)
    x_new = np.linspace(0, len(y)-1, int(stretch_factor*len(y)))
    y_new = f(x_new)

    return y_new


def stretch_pandas(s, factor, kind="cubic"):
    """
    stretch a pandas dataframe or series by a certain factor 

    :param s: pandas dataframe or series
    :param factor: factor by which you want to stretch

    """
    try:
        s = s.to_frame()
    except:
        pass

    t = s.index # should be datetime
    indexname = s.index.name
    t2 = stretch_datetime(t, factor)

    #print("stretched time series",len(t2))

    new_data = {indexname:t2}
    for column in s.columns:
        new_data[column] = interpolate(s[column],factor,kind=kind)

    df =  pandas.DataFrame(new_data).set_index(indexname)
    #print("new df")
    return df


def log_difference(x0):
    """
    computes difference of log[x0], i.e. log[x1/x0] of a pandas time series
    """
    x = np.array(x0,dtype=float)

    y = np.zeros(len(x)-1)

    for i in range(len(x)-1):
        y[i] = np.log(x[i+1]) - np.log(x[i])

    z =  y - np.mean(y)
    z /= max(z)

    return z # pandas.Series(z,index=x0.index[:-1])
   

def difference(x0):
    """
    computes difference of x0, i.e. [x1-x0] of a pandas time series
    """
    x = np.array(x0,dtype=float)

    y = np.zeros(len(x)-1)

    for i in range(len(x)-1):
        y[i] = x[i+1] - x[i] # np.log(x[i+1]) - np.log(x[i])

    z = y - np.mean(y)
    z /= max(z)

    return pandas.Series(z,index=x0.index[:-1])


def percentage_change(x0):
    """
    computes difference of x0, i.e. [x1-x0] of a pandas time series
    """
    x = np.array(x0,dtype=float)

    y = np.zeros(len(x)-1)

    for i in range(len(x)-1):
        if x[i] != 0:
            y[i] = 100*(x[i+1] - x[i]) / x[i] # np.log(x[i+1]) - np.log(x[i])
        else:
            y[i] = np.inf

    return pandas.Series(y,index=x0.index[:-1])


def cross_correlate(x1,x2,lags=15):
    """
    computes the cross-correlation of x1 and x2 using plt.xcorr
    returns dataframe with xcorr data
    """
    # res = plt.xcorr(x1, x2 , plt.gca(), color="black", maxlags=lags,)
    # lag_data = res[0]
    # corr_data = res[1]

    x1 -= np.mean(x1)
    x2 -= np.mean(x2)

    x1 /= np.std(x1)
    x2 /= np.std(x2)

    corr_data = np.correlate(x1, x2, 'full' ,lags=lags)
    lag_data = np.arange(-len(x1) + 1, len(x1))
    corr_data = np.divide(corr_data,(len(x1)))

    res_df = pandas.DataFrame({"Lag":lag_data,"Cross-Correlation":corr_data}).set_index("Lag")
    # print(res_df.loc[[1,5],:])

    return res_df


def cross_correlate_plot(x1,x2,normalize=True,ax=None,show_plot=True,ylabel="Cross-Correlation",lags=15,color="black"):
    """
    generates a cross-correlation plot of x1 and x2

    :param lags: maxium number of lags to show
    :param ylabel: 
    :param normalize:
    :param color: color of the plot 
    """
    if ax is None:
        fig = plt.figure(figsize=(4,3))
        ax = fig.add_subplot(111)
    else:
        ax = plt.gca()
        fig = plt.gcf()

    try:
        plt.style.use("macro")
    except:
        pass

    ax.set_xlabel("Lag")
    ax.set_ylabel(ylabel)

    x1 = np.array(x1)
    x2 = np.array(x2)

    lags2 = range(-len(x1)+1, len(x2))
    cs = []
    for lag in lags2:
        idx_lower_x1 = max(lag, 0)
        idx_lower_x2 = max(-lag, 0)
        idx_upper_x1 = min(len(x1), len(x1)+lag)
        idx_upper_x2 = min(len(x2), len(x2)-lag)
        b1 = x1[idx_lower_x1:idx_upper_x1]
        b2 = x2[idx_lower_x2:idx_upper_x2]
        c = np.correlate(b1, b2)[0]
        if normalize:
            c = c / np.sqrt((b1**2).sum() * (b2**2).sum())
        cs.append(c)

    # plt.xcorr(x1, x2, ax, color=color, maxlags=lags)
    corrCoef = np.array(cs) # np.correlate(x1, x2, 'full') # ,lags=lags)
    lagsOut = np.arange(-len(x1) + 1, len(x1))

    ax.bar(lagsOut, corrCoef,color=color,width=0.4)

    plt.tight_layout()
    ax.set_xlim([-lags,lags])

    if show_plot:
        plt.show()
    