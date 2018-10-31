# Any problem, contact jxli@bao.ac.cn
# Last modified 2018/10/26
import argparse
import time
from sys import stdout as out

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Controller for HP Noise Figure Meter 8970B')
    parser.add_argument('-e', dest='enr', nargs='?', const='agilent', choices=('agilent', 'other'), help='Input ENR parameters; Default ENR: Agilent 346A, "other" is not supported')
    parser.add_argument('-c', dest='calibrate', metavar=('StartFrequency', 'StopFrequency', 'StepSize'), nargs=3, type=int, help='Calibrate with StartFrequency StopFrequency StepSize; Unit: MHz; Default Smoothing: 5, use -s to assign smoothing times.')
    parser.add_argument('-s', dest='smoothing', metavar='Smoothing', choices=range(10), type=int, default=5, help='Set 2**Smoothing; Default: 5')
    parser.add_argument('-m', dest='measure', type=int, metavar=('StartFrequency', 'StopFrequency', 'StepSize'), nargs=3, help='Automatically measure with StartFrequency StopFrequency StepSize and save result to file; Unit: MHz; Default Filename: NF_data_$CurrentDateTime$.txt, use -d to assign datafile name.')
    parser.add_argument('-d', dest='datafile', metavar='DatafileName', default=time.strftime('NF_data_%Y%m%d%H%M%S.txt'), help='Data file name; Default: NF_data_$CurrentDateTime$.txt')
    parser.add_argument('-t', dest='time', metavar='Time', default=6, type=int, help='Set waiting time for smoothing process before reading data; Unit: second; Default: 6; Larger smoothing, longer time.')
    parser.add_argument('-f', dest='frequency', metavar='Frequency', type=int, help='Manually measure at assigned Frequency; Unit: MHz')
    parser.add_argument('-p', dest='plot', metavar='DatafileName', nargs='?', const='NF_data_', help='Plot noise figure data with DatafileName; Default: NF_data_$LatestDateTime$.txt')
    options = parser.parse_args()
    #print options
    
    if options.plot != None:
        if options.plot == 'NF_data_':
            import glob
            txtfiles = glob.glob('NF_data_??????????????.txt')
            if txtfiles == []:
                print 'Error: Can not find data file of format NF_data_$LatestDateTime$.txt .'
                exit()
            txtfile = sorted(txtfiles)[-1]
        else:
            txtfile = options.plot
        print('Loading {0} ...'.format(txtfile))
        import numpy as np
        data = np.loadtxt(txtfile, delimiter = ',')
        datetime_str = txtfile[:-4]
        if datetime_str.startswith('NF_data_'):
            datetime_str = datetime_str[8:]
        import matplotlib.pyplot as plt
        plt.figure(figsize = (12, 8))
        plt.title('Gain')
        plt.plot(data[:, 0] / 1e6, data[:, 1])
        plt.grid()
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Gain (dB)')
        gain_graph = 'Gain_{0}.png'.format(datetime_str)
        plt.savefig(gain_graph)
        print(gain_graph)

        plt.figure(figsize = (12, 8))
        plt.title('Noise Figure')
        plt.plot(data[:, 0] / 1e6, data[:, 2])
        plt.grid()
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Noise Figure (dB)')
        nf_graph = 'NoiseFigure_{0}.png'.format(datetime_str)
        plt.savefig(nf_graph)
        print(nf_graph)
        print('Over.')
        exit()
   
    if options.calibrate == None and options.enr == None and options.frequency == None and options.measure == None:
        parser.print_help()
        exit()

    import pyvisa
    rm = pyvisa.ResourceManager()
    src = rm.list_resources()
    if src == ():
        print('Error: cannot connect to instrument. Check your GPIB connection.')
        exit()
    else:
        # By now, only one GPIB device is supported. If two or more GPIB devices are used, you should manually set it here by:
        # dev = src[index] # where index is the one you wanted. Then comment the for loop below.
        for dev in src:
            if 'GPIB' in dev:
                break
            else:
                print('Error: cannot find GPIB device. Check your GPIB connection.')
                exit()

    if options.enr != None:
        if options.enr.lower() == 'agilent':
            # ENR for Agilent 346A 10MHz-18GHz Noise Source.    
            ENR_str = 'NR10MZ5.47EN100MZ5.56EN1000MZ5.37EN2000MZ5.41EN3000MZ5.42EN4000MZ5.40EN5000MZ5.32EN6000MZ5.39EN7000MZ5.46EN' + \
            '8000MZ5.39EN9000MZ5.53EN10000MZ5.62EN11000MZ5.51EN12000MZ5.64EN13000MZ5.68EN14000MZ5.77EN15000MZ5.79EN16000MZ5.91EN17000MZ5.84EN18000MZ5.40EN'
        elif options.enr.lower() == 'other':
            print('Error: ENR for "other" is unknown.')
            ENR_str = 'NRxx.xxMZx.xxEN'
            exit()
        else:
            print('Error: unsupported ENR.')
            exit()
        inst = rm.open_resource(dev)
        status = inst.write(ENR_str)
        time.sleep(1)
        # Special function sets (Fre, Gain, NF) output.
        status = inst.write('SPH1')

        print 'Set ENR succeeded.'
        try:
            inst.close()
        except:
            print('Warn: disconnect instrument failed.')
    elif options.calibrate != None:
        inst = rm.open_resource(dev)
        status = inst.write('M2FA{0[0]}MZFB{0[1]}MZSS{0[2]}MZF{1}CA'.format(options.calibrate, options.smoothing))
        print('Set calibration succeeded.')
        print('Wait the instrument to finish calibration before carrying on.')
        try:
            inst.close()
        except:
            print('Warn: disconnect instrument failed.')
    elif options.frequency != None:
        inst = rm.open_resource(dev)
        status = inst.write('FR{0}MZEN'.format(options.frequency))
        print('Set frequency succeeded.')
        time.sleep(options.time)
        data = inst.read().strip()
        data_fre, data_gain, data_nf = data.split(',')
        data_fre = float(data_fre)
        try:
            data_gain= float(data_gain)
            data_nf  = float(data_nf)
        except:
            print('Gain = Error dB\tNF = Error dB')
        else:
            print('Gain = {0:>6.3f}dB\tNF = {1:>6.3f}dB'.format(data_gain, data_nf))
        try:
            inst.close()
        except:
            print('Warn: disconnect instrument failed.')
    elif options.measure != None:
        inst = rm.open_resource(dev)
        # Confirm Corrected NF and Gain.
        status = inst.write('M2EN') 
        print('Start measuring ...') 
        time.sleep(1)      
        fstart, fstop, fstep = options.measure
        with open(options.datafile, 'w') as df:
            for fre in xrange(fstart, fstop+1, fstep):
                out.write('Freq = {0:>4d}MHz\t'.format(fre))
                out.flush()
                status = inst.write('FR{0}MZM2'.format(fre))
                time.sleep(options.time)
                data = inst.read().strip()
                df.write(data + '\n')
                data_fre, data_gain, data_nf = data.split(',')
                data_fre = float(data_fre)
                try:
                    data_gain= float(data_gain)
                    data_nf  = float(data_nf)
                except:
                    print('Gain = Error dB\tNF = Error dB')
                else:
                    print('Gain = {0:>6.3f}dB\tNF = {1:>6.3f}dB'.format(data_gain, data_nf))
        print('\nOver. Data has been saved to {0}'.format(options.datafile))
        try:
            inst.close()
        except:
            print('Warn: disconnect instrument failed.')
            exit()
    else:
        exit()
