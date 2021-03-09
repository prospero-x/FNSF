sometimes the total particle count in the IEAD isn't high enough to get
a high-resolution rustbca simulation. so we multiply the particle count
by some factor. Here we save the factors so that when we want to determine
real sputtering yield, we divide by these factors.
