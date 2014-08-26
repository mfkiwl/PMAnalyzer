# GrowthCurve.py
# Bacteria growth curve class to extract parameters
# Use with Phenotype MicroArray analysis pipeline
#
# Author: Daniel A Cuevas
# Created on 21 Nov. 2013
# Updated on 26 Aug. 2014


import pylab as py
import scipy.optimize as optimize
import sys


class GrowthCurve:
    '''Bacteria growth curve class'''
    def __init__(self, data, time):
        # data format: multidimensional numpy array
        #              Each inner array is an array of OD values
        #              ordered by time.
        #              This is important for determining the median

        self.dataReps = data  # OD data values (replicates implied)
        #self.dataMed = py.median(self.dataReps, axis=0)
        self.time = time  # time values
        self.y0 = self.dataReps[1]
        self.asymptote = self.__calcAsymptote()
        self.maxGrowthRate, self.mgrTime = self.__calcMGR()
        self.asymptote, self.maxGrowthRate, self.lag = self.__calcParameters(
            (self.asymptote, self.maxGrowthRate, 0.5), self.time, self.dataReps)

        self.dataLogistic = logistic(self.y0, self.time,
                                     self.asymptote, self.maxGrowthRate, self.lag)
        self.growthLevel = self.__calcGrowth()
        self.sse = sum((self.dataLogistic - self.dataReps) ** 2)

    def __calcParameters(self, y0, t, raw):
        '''Perform curve-fitting optimization to obtain parameters'''
        try:
            results = optimize.minimize(self.__logisticSSE, y0, args=(t, raw),
                                        bounds=((0.01, y0[0]),
                                                (0, None),
                                                (0, None)))
        except RuntimeError as e:
            print(e)
            print(self.dataReps)
            sys.exit(1)

        return results.x

    def __logisticSSE(self, params, t, y):
        a, mgr, l = params
        return py.sum((logistic(t, self.y0, a, mgr, l) - y) ** 2)

    def __calcAsymptote(self):
        '''Obtain the value of the highest OD reading'''
        # Calculate asymptote using a sliding window of 3 data points
        stop = len(self.time) - 3
        maxA = -1
        for idx in range(1, stop):
            av = py.mean(self.dataReps[idx:idx + 3])
            if av > maxA:
                maxA = av
        return maxA

    def __calcMGR(self):
        '''Obtain the value of the max growth'''
        # Calculate max growth rate using a sliding window of 4 data points
        stop = len(self.time) - 4
        maxGR = 0
        t = 0
        for idx in range(1, stop):

            # Growth rate calculation:
            # (log(i+3) - log(i)) / (time(i+3) - time(i))
            gr = ((py.log(self.dataReps[idx + 3]) - py.log(self.dataReps[idx])) /
                  (self.time[idx + 3] - self.time[idx]))
            if idx == 1 or gr > maxGR:
                maxGR = gr
                t = self.time[idx + 2]  # Midpoint time value

        return maxGR, t

    def __calcGrowth(self):
        '''Calculate growth level using an adjusted harmonic mean'''
        return len(self.dataLogistic) / py.sum((1 / (self.dataLogistic +
                                                     self.asymptote)))


def logistic(t, y0, a, mgr, l):
    '''Logistic modeling'''
    startOD = y0
    lg = startOD + ((a - startOD) /
                    (1 + py.exp((((mgr / a) * (l - t)) + 2))))
    return lg
