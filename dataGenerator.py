import numpy as np
import h5py
from api import FULL_FREQS, NBINS, FS


## Simulation paramters
fcs = [25e6, 85e6, 41e6, 900e6, -400e6, -401e6, -402e6]
phase_incrs = [0]*len(fcs)

sweeps = [(92e6,94e6,0.1), (-350e6,-15e6, 0.3)] #f1,f2,T
t_int = NBINS/FS # so that each fft is one integration




def integrated_spec_gen(noise_pwr, time):
    t_incr = 0
    t_arr = np.linspace(0, t_int, NBINS)

    while t_incr <= time:
        output = np.random.normal(0,np.sqrt(noise_pwr), NBINS) + 1j*np.random.normal(0,np.sqrt(noise_pwr), NBINS)
        for i, fc in enumerate(fcs):
            output += np.exp(2j*np.pi*fc*t_arr+phase_incrs[i])
            phase_incrs[i] = (phase_incrs[i] +  t_int*(2*np.pi)*fc) % (2*np.pi) #TODO check this I'm not thinking straight rn
        for f1,f2,T in sweeps:
            sweep_t_portion = np.linspace(t_incr, t_incr*2, NBINS)
            sweep_portion = np.exp(1j*(np.pi*((f2-f1)/T)*np.square(sweep_t_portion)))
            output += sweep_portion
        output = 10.*np.log10(np.abs(np.fft.fftshift(np.fft.fft(output))))

        yield (output, t_incr)
        t_incr += t_int
    return

'''
Time is in seconds
'''
def write_to_h5(noise_pwr, time):

    with h5py.File('data.h5','w') as h5f:
        h5f.attrs['fs'] = FS
        h5f.attrs['NFFT'] = NBINS
        h5f.attrs['noise_var'] = noise_pwr
        h5f.attrs['duration'] = time

        n_integrations = np.ceil(time/t_int)

        h5f.create_dataset('spec', (n_integrations, NBINS))
        h5f.create_dataset('freqs',data=FULL_FREQS)
        h5f.create_dataset('times', (n_integrations,))

        for i, (output, t) in enumerate(integrated_spec_gen(noise_pwr, time)):
            print(f"{i}/{n_integrations}")
            h5f['spec'][i]=output
            h5f['times'][i]=t



write_to_h5(1, 0.1)

