import numpy as np
import matplotlib.pyplot as plt
import scipy
from scipy import optimize

def function(x, a, b):
   return a*x + b

x = np.linspace(start=-50, stop=10, num=40)
y = function(x, 6, 2)

np.random.seed(6)
noise = 20*np.random.normal(size=y.size)
y = y + noise

popt,cov = scipy.optimize.curve_fit(function, x, y)
a,b= popt

x_new_value = np.arange(min(x), 30, 5)
y_new_value = function(x_new_value, a, b)

plt.scatter(x,y,color="green")
plt.plot(x_new_value,y_new_value,color="red")
plt.xlabel('X')
plt.ylabel('Y')
print("Estimated value of a : "+ str(a))
print("Estimated value of b : " + str(b))
plt.show()