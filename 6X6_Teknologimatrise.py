#THIS CODE IS SHAKER PROPERTY BICTH 

#MATRIXSOLVER 4747474

import numpy as np 

#   𝑥01,  𝑥12,     𝑥20,    𝑥23,    𝑥30,     𝑥31
A = np.array([
[    1,    -1,     -1,       0,      0,      1,    0], #1
[    0,     1,      0,      -1,     -1,      0,    0], #2
[    0,     0,      1,       0,      1,     -1,   -1], #3
[    0,     1,      0,       0,      0,      0,    0], #4
[   -0.1,   0,      1,       0,      0,     -0.1,  0], #5
[    0,    -0.9,    0,       0,      1,      0,    0], #6
[    0,     0,  -0.15,       0,  -0.15,      1,    0], #7
])

y = np.array([[0], [0], [0], [95000], [0], [0], [0]])

x = np.linalg.inv(A)@y
print("Svar: ")
print("")
print(x)