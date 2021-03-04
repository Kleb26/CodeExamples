from __future__ import division
import numpy as np
import scipy as sci
import scipy.integrate as integrate
import scipy.special as scisp
import scipy.optimize as optimize
import matplotlib.pyplot as pyplot
import matplotlib.gridspec as gridspec
import matplotlib.ticker as ticker
import thermal_motion
import absorption


##########################################
#Physics constants
#source: physics.nist

k_b = 1.38064852 * 10**(-23) #J/K

e   = 1.6021766208*10**-19 #C

h   = 6.626070040 * 10**(-34) #Js
hbar= h/(2*np.pi)

imp0= 376.730313461 #Ohm

m_p = 1.672621898 *10**(-27) #kg

m_e = 9.10938356 *10**(-31) #kg

c   = 299792458 #m/s

a0  = 0.52917721067*10**-10 #m


#########################################
#Hydrogen + experiment

E1  = -13.6 #eV
E2  = -3.4 #eV

lifetime = 1.6*10**-9
#http://www.ioffe.ru/astro/QC/CMBR/sp_tr.html
#H.A. Bethe and E.E. Salpeter, "Quantum mechanics of one- and two- electron atoms", 1957

w0 = e*np.abs(E2 - E1)/hbar #rad/s
f0 = w0/(2*np.pi)

power      = 10**-3 #W
beam_width = 100*10**-6
intensity  = power / beam_width

Efield = absorption.P2Efield(intensity)

#######################################
#setup

Initial_T = 1 #K

pi_pulse  = 2*np.pi / absorption.Omega(Efield) #baseline for no detune


Omega = absorption.Omega(Efield)

lifetime_limit = np.pi / Omega

#####################################
#Getting values


def inverse_doppler(w, v):
    b = v/c
    return np.sqrt( (1+b)/(1-b) ) * w

def T_v_laserf():
    T_rng = np.linspace(0,293,num=100)
    avg_v = thermal_motion.avg_vel1D(T_rng)

    laser_w = inverse_doppler(w0, avg_v)
    laser_f = laser_w/(2*np.pi)

    doppler_w = w0

    W     = absorption.rabi_f(Efield, doppler_w)
    rabi_max =(Omega/ W)**2


    fig1 = pyplot.figure()

    ax1 = pyplot.subplot()

    ax1.plot(T_rng, laser_f-f0)

    return pyplot.show()

def T_v_absorption(base_T):

    laser_w = inverse_doppler(w0, thermal_motion.avg_vel1D(base_T))

    T_rng= np.linspace(base_T*0.99, base_T*1.01,num=1000)

    doppler_w = absorption.doppler_shift(laser_w, thermal_motion.avg_vel1D(T_rng))

    W = absorption.rabi_f(Efield, doppler_w)
    rabi_max = (Omega / W) ** 2

    fig2 = pyplot.figure(figsize=(9.5,8))

    ax1 = pyplot.subplot()

    ax1.plot(thermal_motion.avg_vel1D(T_rng)/thermal_motion.avg_vel1D(base_T), rabi_max, label=r'293$K$', color='black')
    ax1.set_xlim([thermal_motion.avg_vel1D(T_rng)[0]/thermal_motion.avg_vel1D(base_T), thermal_motion.avg_vel1D(T_rng)[-1]/thermal_motion.avg_vel1D(base_T)])

    base_T = 100
    laser_w = inverse_doppler(w0, thermal_motion.avg_vel1D(base_T))

    T_rng = np.linspace(base_T * 0.99, base_T * 1.01, num=1000)

    doppler_w = absorption.doppler_shift(laser_w, thermal_motion.avg_vel1D(T_rng))

    W = absorption.rabi_f(Efield, doppler_w)
    rabi_max = (Omega / W) ** 2

    ax1 = pyplot.subplot()

    ax1.plot(thermal_motion.avg_vel1D(T_rng) / thermal_motion.avg_vel1D(base_T), rabi_max, label=r'100$K$')

    base_T = 1
    laser_w = inverse_doppler(w0, thermal_motion.avg_vel1D(base_T))

    T_rng= np.linspace(base_T*0.99, base_T*1.01,num=1000)

    doppler_w = absorption.doppler_shift(laser_w, thermal_motion.avg_vel1D(T_rng))

    W = absorption.rabi_f(Efield, doppler_w)
    rabi_max = (Omega / W) ** 2

    ax1 = pyplot.subplot()

    ax1.plot(thermal_motion.avg_vel1D(T_rng)/thermal_motion.avg_vel1D(base_T), rabi_max, label = r'1$K$')

    base_T = 1e-2
    laser_w = inverse_doppler(w0, thermal_motion.avg_vel1D(base_T))

    T_rng = np.linspace(base_T * 0.99, base_T * 1.01, num=1000)

    doppler_w = absorption.doppler_shift(laser_w, thermal_motion.avg_vel1D(T_rng))

    W = absorption.rabi_f(Efield, doppler_w)
    rabi_max = (Omega / W) ** 2

    ax1 = pyplot.subplot()

    ax1.plot(thermal_motion.avg_vel1D(T_rng) / thermal_motion.avg_vel1D(base_T), rabi_max, label=r'10$mK$')


    #ax1.set_title('Absorption sensitivity of atom velocity \n centered on average velocity at given Temperature', fontsize=26)
    ax1.set_xlabel(r'Ratio of Atom Velocity from $<v>$ at Temperature', fontsize=22)
    ax1.set_ylabel(r'Probability of absorption', fontsize=22)
    ax1.tick_params(axis='both', which='major', labelsize=16)
    ax1.legend(fancybox=True, framealpha=0.7, fontsize=20)

    pyplot.tight_layout()

    return pyplot.show()

#T_v_absorption(293)

def absorption_chance(T):
    inst_vel_data = thermal_motion.MB_dist_retVel1D(T)
    inst_vel       = inst_vel_data[0]

    laser_w = inverse_doppler(w0, thermal_motion.avg_vel1D(T))
    laser_f = laser_w/(2*np.pi)

    doppler_w = absorption.doppler_shift(laser_w, inst_vel)

    W = absorption.rabi_f(Efield, doppler_w)

    absorb = absorption.absorbed(Omega, W)

    return absorb[1]

def T_v_AbC():
    T_rng = np.logspace(-9,2,num=100)
    AbC   = np.zeros(T_rng.shape[0])

    k = 0
    while k < T_rng.shape[0]:
        i = 0
        j = 0
        t = 1000
        while i < t:
            itr = absorption_chance(T_rng[k])
            if itr == 1:
                j = j + 1
            i = i + 1
        AbC[k] = j/t
        k = k + 1

    fig3 = pyplot.figure(figsize=(15,11))

    ax1 = pyplot.subplot()

    ax1.semilogx(T_rng, AbC)
    np.savetxt('D:\y3- laser cooling\data\T_rng.txt', T_rng)
    np.savetxt('D:\y3- laser cooling\data\AbC.txt', AbC)

    ax1.set_title('Atom absorption chance for laser frequency \n set for average thermal velocity', fontsize=26)
    ax1.set_xlabel(r'Temperature/$K$', fontsize=18)
    ax1.set_ylabel('Probability to absorb the photon', fontsize=18)

    pyplot.tight_layout()

    return pyplot.show()


def gaussi(x,a, sig):
    mu =-9
    return a*np.exp(-(x-mu)**2 / (2*sig**2) )

def sigmoid(x, a,b,c,d):
    return (a*np.exp(x*b)) / (np.exp(c*x)+d)

def fit2AbC():
    T_rng = np.loadtxt('D:\y3- laser cooling\data\T_rng.txt')
    AbC = np.loadtxt('D:\y3- laser cooling\data\AbC.txt')

    fit = optimize.curve_fit(sigmoid, np.log(T_rng), AbC,)

    fig4 = pyplot.figure(figsize=(9, 7))

    ax1 = pyplot.subplot()

    ax1.semilogx(T_rng, AbC, color='black')

    ax1.semilogx(T_rng, sigmoid( np.log(T_rng), fit[0][0], fit[0][1], fit[0][2],fit[0][3]), color='blue' )
    #np.savetxt('D:\y3- laser cooling\data\T2absorptionchance_sigmoidfit_natlogofT_values.txt', fit[0])
    #ax1.set_title('Atom absorption chance for laser frequency \n set for average thermal velocity', fontsize=26)

    ax1.set_xlabel(r'Temperature/$K$', fontsize=22)
    ax1.set_ylabel('Probability to absorb the photon', fontsize=22)

    ax1.annotate(r'$\frac{%.1f \times 10^{-3} T^{%.3f}}{T^{%.3f} + %.2f \times 10^{-3}}$' %(fit[0][0]*1e3, fit[0][1],fit[0][2],fit[0][3]*1e3) ,
                 xy=[1e-5,0.2], xytext=[1e-5,0.5], fontsize=40, color='blue')
    ax1.tick_params(axis='both', which='major', labelsize=20)
    ax1.set_ylim([0,1])

    pyplot.tight_layout()

    return pyplot.show()

fit2AbC()
#####################################
#Ideal cooling
#laser frequency perfect
#always spontaneous decay

def iteration(Temp):

    inst_vel_data = thermal_motion.MB_dist_retVel1D(Temp)
    inst_vel       = inst_vel_data[0]

    laser_w = inverse_doppler(w0, thermal_motion.avg_vel1D(Temp))
    laser_f = laser_w/(2*np.pi)

    doppler_w = absorption.doppler_shift(laser_w, inst_vel)
    delta     = np.abs(doppler_w - w0)
    #doppler_w  = w0

    W = absorption.rabi_f(Efield, doppler_w)

    absorb = absorption.absorbed(Omega, W)

    photon_momentum = (hbar * laser_w)/c
    delta_v         = photon_momentum/(m_p + m_e)

    if absorb[1] == 1:
        Temp = thermal_motion.inv_cum_MBdistT(inst_vel_data[0]-delta_v, inst_vel_data[1])
        time = absorb[0] + lifetime
    else:
        time = absorb[0]

    return [ time, Temp ]

def analytical(Temp):
    inst_vel_data = thermal_motion.MB_dist_retVel1D(Temp)
    inst_vel      = inst_vel_data[0]

    laser_w = inverse_doppler(w0, thermal_motion.avg_vel1D(Temp))
    laser_f = laser_w/(2*np.pi)

    doppler_w = absorption.doppler_shift(laser_w, inst_vel)


    photon_momentum = (hbar * laser_w) / c

    a_max = photon_momentum * lifetime / (2*(m_p+ m_e))
    return a_max

def anal_quickplot(Temp):
    '''seems far too small to affect temperature'''
    a_max = analytical(Temp)
    print a_max
    time = np.linspace(0, 1, num=10000)

    v0 = thermal_motion.avg_vel1D(Temp)
    print v0
    temparr = np.zeros(shape=time.shape)
    i = 0
    while i < time.shape[0]:
        temparr[i] = thermal_motion.inv_avg_vel1d(v0- a_max*time[i])
        i = i + 1

    fig1=pyplot.figure()
    ax1=pyplot.subplot()
    ax1.plot(time, temparr)
    return pyplot.show()




def ideal_plot(num=1):
    fig6 = pyplot.figure(figsize=(9,8))
    ax1 = pyplot.subplot()

    k = 0
    while k < num:
        time_axis = np.array([0])
        temp_axis = np.array([Initial_T])

        i = 0
        while temp_axis[i] > 1e-3:
            itr = iteration(temp_axis[i])

            time_axis = np.append(time_axis, time_axis[i] + itr[0])
            temp_axis = np.append(temp_axis, itr[1])
            i = i + 1
        ax1.plot(time_axis*1e6, temp_axis, color='black')
        k = k + 1


    #ax1.set_title('Ideal Laser Cooling of Hydrogen in 1D', fontsize=26)
    ax1.set_xlabel(r'Time/$\mu s$', fontsize=22)
    ax1.set_ylabel(r'Temperature/$K$', fontsize=22)
    ax1.tick_params(axis='both', which='major', labelsize=20)


    pyplot.tight_layout()

    return pyplot.show()


#ideal_plot()


def avg(num=1):
    fig7 = pyplot.figure(figsize=(9,8))
    ax1 = pyplot.subplot()

    iter_dat = np.zeros( (num, 1000) )
    xinter   = np.linspace(0, 120e-6, num=1000)

    k = 0
    while k < num:
        time_axis = np.array([0])
        temp_axis = np.array([Initial_T])

        i = 0
        while temp_axis[i] > 1e-3:
            itr = iteration(temp_axis[i])

            time_axis = np.append(time_axis, time_axis[i] + itr[0])
            temp_axis = np.append(temp_axis, itr[1])
            i = i + 1
        #ax1.plot(time_axis*1e6, temp_axis, color='black')

        temp_inter = np.interp( xinter, time_axis, temp_axis)
        iter_dat[k]= temp_inter

        #ax1.plot(xinter*1e6, temp_inter, color='red')
        k = k + 1

    avg_temp = np.average( iter_dat, axis=0)
    std_temp = np.std( iter_dat, axis=0 )
    ax1.plot( xinter*1e6, avg_temp, color='black')
    np.savetxt('D:\\y3- laser cooling\\data\\avg_T_1000.txt', avg_temp)
    np.savetxt('D:\\y3- laser cooling\\data\\std_T_1000.txt', std_temp)

    return pyplot.show()

#avg(1000)

def cool2_01():
    k = 0
    tot = 100
    cooltime = np.zeros(tot)
    while k < tot:
        time_axis = np.array([0])
        temp_axis = np.array([Initial_T])

        i = 0
        while i < 20000:
            itr = iteration(temp_axis[i])

            time_axis = np.append(time_axis, time_axis[i] + itr[0])
            temp_axis = np.append(temp_axis, itr[1])
            if temp_axis[-1] <=1e-3:
                i = 20000
                cooltime[k] = time_axis[-1]

            i = i + 1
        #ax1.plot(time_axis * 1e-6, temp_axis)
        k = k + 1
    return cooltime

# out = cool2_01()
# print out
# print np.average(out)
# print np.average(out)*1e6
# np.savetxt('D:\y3- laser cooling\data\cooltime_1kto1mk_large.txt', out)

##########################################
#troubleshoot

# t_rng = np.logspace(-6, 2, base=10, num=1000)
#
# b = thermal_motion.avg_vel1D(t_rng)/c
#
# ratio = np.sqrt( (1+b)/(1-b) )
#
#
# print ratio[-1]-ratio[0]
#
# fig = pyplot.figure(figsize=(8,6))
# ax1  = pyplot.subplot()
# ax1.loglog(t_rng, ratio-1)
# ax1.set_xlabel(r'Temperature / $K$', fontsize=18)
# ax1.set_ylabel(r'Doppler shift coefficient - 1', fontsize=18)
# ax1.tick_params(axis='both', which='major', labelsize=17)
# pyplot.tight_layout()
# pyplot.show()