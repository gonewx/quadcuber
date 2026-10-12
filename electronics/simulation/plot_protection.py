#!/usr/bin/env python3
"""Plot saved ngspice data; does not run a circuit or infer hardware qualification."""
import os,csv,gzip
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/quadcuber-matplotlib');os.environ.setdefault('XDG_CACHE_HOME','/tmp/quadcuber-cache')
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parents[2]/'generated/electronics/protection-analysis'
def read(case):
 with gzip.open(P/case/'waveform.txt.gz','rt') as f:return np.loadtxt(f,skiprows=1)
r=list(csv.DictReader((P/'regenerative_energy.csv').open()))
fig,axes=plt.subplots(2,1,figsize=(10,7),layout='constrained')
for row in r:
 if row['energy_per_event_J']=='0.05' and row['pulse_s']=='0.02' and row['repetition_Hz']=='5':
  d=read(row['case']);axes[0].plot(d[:,0],d[:,1],label='150 ohm +1% bleed' if float(row['bleed_ohm'])<200 else 'No guaranteed minimum load')
axes[0].axhline(12,c='red',ls='--',label='12 V screening boundary');axes[0].legend();axes[0].set(xlabel='Time (s)',ylabel='VM (V)',title='Five 0.05 J pulses, 20 ms, 5 Hz; C=2256 uF, supply=9.18 V')
r=list(csv.DictReader((P/'input_rlc.csv').open()));row=max(r,key=lambda x:float(x['startup_I2t_A2s']));d=read(row['case']);take=(d[:,0]>=.00009)&(d[:,0]<=.0005)
axes[1].plot(d[take,0]*1e6,d[take,2]);axes[1].set(xlabel='Time (us)',ylabel='Input current (A)',title=f"Worst startup integral: {float(row['startup_I2t_A2s']):.3f} A^2s; PSU reservoir releases short surge")
fig.suptitle('Boundary models only — no vendor protection timing or thermal qualification')
fig.savefig(P/'protection-boundaries.png',dpi=160)
