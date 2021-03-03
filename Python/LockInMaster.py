import numpy as np
import matplotlib.pyplot as pyplot
import zhinst.utils
import warnings
import time
import datetime
import os
import matplotlib.gridspec as gridspec
import scipy
import sys
import scipy.signal

class misc:
    overhead_lin_m = 2.8770
    overhead_lin_c = 1.9
    #data above from investigation into file size, onenote: control-lockin\Streaming RAM limits.
    #fitted using scipy, can be refound with the various files with same sample size but varying record numbers
    #plot of records vs file size shows linear fit:
    # m = 2.8870(2)  ; c = 1.9(2)  : overhead = m * records + c

    def __init__(self):
        pass

    def filesizeCalc(self, n_records, n_samples, fft=True):
        '''
        Calculates filesize of storing scopeGrab like data in a .npy.
        Calculation is based off 2B per data point of scopeGrab like data and an overhead (assumed from
        numpy but probably also includes the dictionary structure). The overhead was formualted empirically
        and found to be linear scaling with the number of records.

        :param n_records: Number of records stored.
        :param n_samples: Number of samples/points per record. Can be expressed as, e.g. 2**14 or 14.
        :param fft: Bool, ffts have half the data points, but same dictionary/overhead file structure. This
                is taken into account when calculating the size.
        :return: Filesize in KB
        '''
        overhead = self.overhead_lin_m * n_records + self.overhead_lin_c
        if n_samples > 100:
            info = 2 * n_samples * n_records / 2**10
        else:
            info = 2 * 2**(n_samples - 10) * n_records
        if fft:
            return info + overhead
        else:
            return 2*info + overhead

    def recordsSizeCalc(self, filesizeKB, n_samples, fft=True):
        if n_samples > 100:
            n_samples = np.log2(n_samples)

        if fft:
            return (filesizeKB - self.overhead_lin_c) / (2*2**(n_samples-10) + self.overhead_lin_m)
        else:
            return (filesizeKB - self.overhead_lin_c) / (2*2*2**(n_samples-10) + self.overhead_lin_m)

    @staticmethod
    def dodgy_printToLog(saveloc, logfilename='logfile.txt'):
        sys.stdout = open(saveloc + os.sep + logfilename, 'w')
        pass

    @staticmethod
    def undo_dodgy_printToLog():
        sys.stdout = sys.__stdout__

class dummyFlag: #class with value type for compatibility with multiprocessing.
    value = True

class lockInAmp:
    device_id = 'dev5070'
    device: str
    daq: zhinst.ziPython.ziDAQServer
    settings_list: list
    scopemodule: zhinst.ziPython.ziDAQServer.scopeModule
    scopeGrab: dict
    wave_nodepath: str
    misc_instance: misc
    saveLoc: str
    dummyflag: dummyFlag
    grabFFT_flag: bool

    def __init__(self, apilevel=6):
        '''
        Class initialisation connects to scope and cleans it up by disabling everything on it.
        Grabs an instance of misc class and the dummyFlag for use with multiprocessing.

        :param apilevel: apiLevel of device, dunno function.
        '''
        self.connect(apilevel)
        zhinst.utils.disable_everything(self.daq, self.device)
        self.misc_instance = misc()
        self.dummyflag = dummyFlag()


    def connect(self, apiLevel=6):
        '''
        Connects to the device with the device_id hard coded into class memory at the top.

        :param apiLevel: api level of device, dunno.
        :return: None
        '''
        (self.daq, self.device, self.props) = zhinst.utils.create_api_session(self.device_id, apiLevel)
        print(f'Connected device ID: {self.device}')
        pass

    def scope_configure_mainInput(self, sample_rate=12,
                                  sample_length = 2**14,
                                  triggered = False,
                                  single = False,
                                  rangee=None,
                                  scaling = 1,
                                  inputt=0,
                                  trigSettings = None,
                                  misc_settings_list=None):
        '''
        Configures the settings on the device reading for scope initialisation and usage.
        To clarify changes settings of the device only. Doesn't create scopeModule interface,
        this is done in iniialise.
        This function does enable input 1 (main, +/- V input on front).

        :param sample_rate: Smart input for the rate samples should be taken each record.
                        If a float is given it reads as the frequency in Hz (samples/s). The code converts this
                        into the diviser for the device.
                        If an integer is given it directly sends as the diviser to the device.
                        The diviser relation is sample frequency = master_freq (60MHz) / 2 ** diviser.
                        :type sample_rate: int or float
        :param sample_length: Samples to be taken per record, this can range from 2**12 to 2**14.
                        Smart imput, can give as, e.g. 2**14 or 14.
                        :type sample_length: float
        :param triggered: Expressing whether data input should be triggered. If desire triggered data
                    user should specify the 4 settings in trigSettings, but failing that gives defaults:
                    rising edge, slight hysteresis triggering on input (same signal), threshold 0V.
                    :type triggered: Bool
        :param single: If true scope will only grab one record on exectute(), this is not useful most of the time.
                    Default is false, enables continuous capture.
                    :type single: Bool
        :param rangee: Voltage input range for input. Runs from plus to minus rangee If None runs autorange on device (via zhinst script).
                    :type rangee: float
        :param scaling: Scaling of input signal voltage. Recommend leave as 1.
                    :type scaling: float
        :param inputt: Device input to use, default 0 for main +/-V input on front.
                    Other inputs (no DIG):
                        1 - Current input, 2/3 - trigger 1/2 (front) , 8/9 - aux Input 1/2
                    :type inputt: int
        :param trigSettings: List of 6 settings. The settings are (any order):
                            -int: trigger input /dev5070/scopes/0/trigchannel
                            -bool: trigger rising? /dev5070/scopes/0/trigrising
                            -bool: trigger falling? /dev5070/scopes/0/trigfalling
                            -float: trigger threshold voltage /dev5070/scopes/0/triglevel
                            -bool: trigger hysteresis enable /dev5070/scopes/0/trighysteresis/mode
                            -float: trigger relative level /dev5070/scopes/0/trighysteresis/relative
                        All settings must be given. Each setting is a list with the setting location, as str
                        (above), as element 0, setting value as element 1.
                        :type trigSettings: list[list[str,Any]]
        :param misc_settings_list: List of any miscellaneous settings to be applied to device. Settings should
                                themselves be in a list (even if 1 setting). Settings of form above, i.e. str
                                for setting path as element 0, setting value as element 1.
                                :type misc_settings_list: list[list[str,Any]]
        :return: None
        '''
        #Smart input handling:
        if sample_length > 2**14:
            sample_length = 2 ** 14
            warnings.warn(
                'Device only capable of maximum of 2**14 samples (memory), sample-Length has been clipped'
            )
        elif sample_length < 2**12:
            sample_length = 2 ** 12
            warnings.warn(
                'Device only capable of minimum of 2**12 samples (memory), sample-Length has been clipped'
            )

        if type(sample_rate) == float:
            sample_rate = int(np.round(np.log2(60e6/sample_rate))) #samplerate is integer for power of 2 divisor of master

        #Initial settings list
        self.settings_list = [ #misc list like this
            ['/%s/sigins/0/imp50' %self.device, 1],
            ['/%s/sigins/0/ac' %self.device, 1],
            ['/%s/SIGINS/0/ON' %self.device, 1],

            ['/%s/scopes/0/channels/0/inputselect' %self.device, inputt],
            ['/%s/scopes/0/length' % self.device, sample_length],
            ["/%s/scopes/0/channel" % self.device, 1], #enable channel 0, only option
            ["/%s/scopes/0/time" %self.device, sample_rate],
            ["/%s/scopes/0/trigenable" % self.device, triggered],
            ["/%s/scopes/0/single" %self.device, single]

        ]
        #Flag for autorange runs autorange script at end.
        if rangee is not None:
            self.settings_list.append(['/%s/SIGINS/0/range' %self.device, rangee])
            flag = False
        else:
            flag = True
        if scaling != 1:
            self.settings_list.append(['/%s/SIGINS/0/scaling' % self.device, scaling])

        #trigger setting handling
        std_trigSettings = [
            ["/%s/scopes/0/trigchannel" % self.device, inputt],
            ["/%s/scopes/0/trigrising" % self.device, 1],
            ["/%s/scopes/0/trigfalling" % self.device, 0],
            ["/%s/scopes/0/triglevel" % self.device, 0.00],
            ["/%s/scopes/0/trighysteresis/mode" % self.device, 1],
            ["/%s/scopes/0/trighysteresis/relative" % self.device, 0.1]
        ]

        if triggered:
            try:
                len(trigSettings)
                if len(trigSettings) != 6:
                    warnings.warn(
                        'Invalid number of trigger settings (6: channel, rising bool, falling bool, level, hysteresis bool, hysteresis lvl), default inferred: self triggered, rising edge, threshold 0V, threshold 0V, hysteresis, 0.1 (relative).'
                    )
                    self.settings_list.extend(std_trigSettings)
                else:
                    self.settings_list.extend(trigSettings)
            except:
                warnings.warn(
                    'No trigger settings (6: channel, rising bool, falling bool, level, hysteresis bool, hysteresis lvl), default inferred: self triggered, rising edge, threshold 0V, hysteresis, 0.1 (relative).'
                )
                self.settings_list.extend(std_trigSettings)

        if misc_settings_list is not None:
            self.settings_list.extend(misc_settings_list)

        #Sends settings list to device then syncs to ensure change.
        self.daq.set(self.settings_list)
        self.daq.sync()
        if flag:
            #sets autorange, and waits to be executed. function stolen
            zhinst.utils.sigin_autorange(self.daq, self.device, inputt)
        pass

    def initialise_scopeModule(self, mode, fftMode = 1, averaging=1, scopeMemory = 100 ):
        '''
        Initialises the scopeModule classfor script usage, also sets scopeModule settings. Unsure distinction
        between a scopeModule setting and a setting at '/dev5070/scopes/0/'.
        Subscribes this class to the device scope ready for data reading.
        This should be called after scope_configure_mainInput, however failure to do so just results in current
        settings on device being used.

        :param mode: Operation mode of the scope.
                        0 - unprocssed (no averaging, scaling etc.)
                        1 - processed (averging, scaling etc. if specified)
                        3 - FFT
                :type mode: int
        :param fftMode: FFT window type, default Hann - 1; other options:
                            0 - Rectangular, 1 - Hann, 2 - Hamming, 3 - Blackman Harris,
                            4 - Exponential (ring down),  5 - cosine (ring down),
        :param averaging:
        :param scopeMemory:
        :return:
        '''
        #Modes:
        #0 - unprocessed
        #1 - processed: if applied: scaling, averaging
        #3 - fft
        self.scopemodule = self.daq.scopeModule()

        if  mode in [0,1]:
            self.grabFFT_flag = False
            self.scopemodule.set('mode', mode)
        elif mode == 3:
            self.scopemodule.set('mode', mode)
            self.grabFFT_flag = True
            self.scopemodule.set('fft/window', fftMode)
        else:
            warnings.warn('Mode is not valid, usual modes: 1 for standard, 3 for FFT. Defaulting to 1.')
            self.scopemodule.set('mode', 1)
        self.scopemodule.set('averager/weight', averaging)
        if scopeMemory > 100:
            warnings.warn('Scope memory is limited to 100 data sets. Clipping')
            self.scopemodule.set('historylength', 100)
        else:
            self.scopemodule.set('historylength', scopeMemory)

        self.daq.sync()

        self.wave_nodepath = f'/{self.device}/scopes/0/wave'
        self.scopemodule.subscribe(self.wave_nodepath)
        pass


    def unsubscribe(self):
        self.daq.unsubscribe('*')
        self.scopemodule.unsubscribe('*')
        pass

    def clear(self):
        zhinst.utils.disable_everything(self.daq, self.device)

    def takeScopeMemory(self, requestedMemory, RAMlimitGB = 6, designator=None, flag = None):
        if flag is None:
            flag = self.dummyflag

        #if requestedMemory is int then takes that many data sets,
        #if float it takes number of data sets to encompass at least that much time
        try:
            self.settings_list
            try:
                self.wave_nodepath
            except:
                warnings.warn('BREAK: scope not initialised, this function will not run.')
                return
        except:
            warnings.warn('Scope Settings not setup, values from previous setup will be used.')

        points_perMemory = self.daq.get('/%s/scopes/0/length' % self.device)[f'{self.device}'][
            'scopes']['0']['length']['value'][0]

        if type(requestedMemory) == float:
            diviser_power = self.daq.get('/%s/scopes/0/time' %self.device)[f'{self.device}'][
                'scopes']['0']['time']['value'][0]
            frequency = 60e6/2**diviser_power
            time_period = 1/frequency

            time_perMemory = time_period * points_perMemory

            requestedMemory = int(np.ceil(requestedMemory / time_perMemory))
            print(f'Time requested converted to number of records required: {requestedMemory}')

        currentMemory = self.scopemodule.get('historylength')['historylength'][0]
        if requestedMemory <= 100:
            self.scopemodule.set('historylength', requestedMemory)
            streaming = False
        else:
            warnings.warn(f'Requested memory is higher than the storage capacity of the device. \n As such the data will be streamed via \'polling\'. \n This may crash, as the device has no dedicated streaming mode, so only safeguards I have instigated exist. \n'
                          f'Also be aware, due to processing time the actual time to take the date is always higher than requested. \n This is especially bad at high sampling rates. \n'
                          f'The time for the read command to run implies a maximum stream rate diviser of 2**7. \n'
                          f'Further at high rates it appears the device does not keep up between records (i.e. unknown delay between each record) <= since at high speeds the PC still has to wait for records to fill the memory even though they should be faster than PC')
            streaming = True
            self.scopemodule.set('historylength', 100)

        try:
            self.grabFFT_flag
        except:
            warnings.warn('Please initialise the scope at least once before running this function. This function won\'t run')
            return
        RAMlimited_memory = self.misc_instance.recordsSizeCalc(RAMlimitGB * 2 **20, points_perMemory, fft=self.grabFFT_flag)
        if requestedMemory > RAMlimited_memory:
            RAMOverflow = RAMlimited_memory
            warnings.warn(f'The requested amount of Records exceeds the RAMlimit set (default 6GB). \n'
                          'Once the grabbed records exceeds this limit the data will be dump the main storage and erased. This continues until all records captured. \n')
        else:
            RAMOverflow = False
        self.get_scopeMemory(requestedMemory, streaming, RAMOverflow, designator=designator, flag = flag)
        return self.scopeGrab

    def get_scopeMemory(self, requestedMemory, streaming = False, RAMOverflow = False, designator=None, flag = None):
        if flag is None:
            flag = self.dummyflag
        self.daq.setInt("/%s/scopes/0/enable" % self.device, 1)
        self.daq.sync()

        flag_skip = False
        records = 0
        progress = 0  # checks current data set is complete
        dump = 0

        fails = 0
        if streaming:
            start = time.time()
            self.scopemodule.execute()
            while (records < 1) or (progress < 1):
                time.sleep(0.1)
                records = self.scopemodule.getInt('records')
                progress = self.scopemodule.progress()[0]
            self.scopeGrab = self.scopemodule.read()
            old_records = records
            while records < requestedMemory:
                while (progress < 1) or (records - old_records < 1):
                    time.sleep(0.01)
                    records = self.scopemodule.getInt('records')
                    print(f'Current Records taken: {records} / {requestedMemory}')
                    progress = self.scopemodule.progress()[0]
                    #print(records - old_records)
                    #print(progress)
                old_records = int(records)
                buffer = self.scopemodule.read()
                try:
                    self.scopeGrab[f'{self.device}']['scopes']['0']['wave'].extend(
                        buffer[f'{self.device}']['scopes']['0']['wave']
                    )
                except:
                    warnings.warn('Failed to read one record. Continuing loop (will attempt another read).')
                    fails += 1
                if RAMOverflow:
                    sys.stdout.flush()
                    if designator is None:
                        designator = datetime.datetime.now().strftime(
                                '%d-%m-%y')
                    if len(self.scopeGrab['dev5070']['scopes']['0']['wave']) > RAMOverflow:
                        try:
                            np.save(self.saveLoc + os.sep + f'RAMdump{dump}_' + f'{designator}', self.scopeGrab)
                            dump += 1
                        except:
                            np.save(os.path.abspath(os.getcwd()) + os.sep + f'RAMdump{dump}_' + f'{designator}', self.scopeGrab)
                            dump += 1
                            warnings.warn(f'No save location specified. RAM dumps going to current directory.')
                        if records < requestedMemory:
                            while (progress < 1) or (records - old_records < 1):
                                time.sleep(0.01)
                                records = self.scopemodule.getInt('records')
                                print(f'Current Records taken: {records} / {requestedMemory}')
                                progress = self.scopemodule.progress()[0]
                        else:
                            flag_skip = True # prevents capture of extra data and attempt to write blank variable if requestedMemory is multiple of RAMmemory
                        old_records = int(records)
                        self.scopeGrab = self.scopemodule.read()
                if not flag.value: #allows manual exit using multiprocessing scheme.
                    RAMOverflow = True
                    print(f'Exiting capture. Current number of records (ignore later msg): {records}')
                    self.misc_instance.undo_dodgy_printToLog()
                    print(f'Exiting capture. Current number of records (ignore later msg): {records}')
                    print(f'Excess data saved to RAMdump{dump}_' + f'{designator}')
                    records = requestedMemory
                    flag_skip = False

            if RAMOverflow and not flag_skip:
                try:
                    np.save(self.saveLoc + os.sep + f'RAMdump{dump}_' + f'{designator}', self.scopeGrab)
                    dump += 1
                except:
                    np.save(
                        os.path.abspath(os.getcwd()) + os.sep + f'RAMdump{dump}_' + f'{designator}', self.scopeGrab)
            print(f'Actual time taken: {time.time() - start}s')

            if RAMOverflow:
                print(f'Number of Records according to device: {records}')
            else:
                print('Actual number of Records taken verification: %i' %len(self.scopeGrab['dev5070']['scopes']['0']['wave']))
            print(f'Number of times a record failed to Read: {fails}')
        else:
            self.scopemodule.execute()
            while (records < requestedMemory) or (progress < 1.0):
                time.sleep(0.1)
                records = self.scopemodule.getInt('records')
                print(f'Current Records in Memory: {records} / {requestedMemory}')
                progress = self.scopemodule.progress()[0]
            self.scopeGrab = self.scopemodule.read()

        self.scopemodule.finish()
        return self.scopeGrab

class LockInPlotter:
    controller: lockInAmp
    longData: list
    neat_longData: np.array
    longFFT: bool
    longDt: float

    def __init__(self, controllerClass):
        '''
        Class governing plotting of scopeGrab like data.

        :param controllerClass: instance of active lockInAmp class controller.
        '''
        self.controller = controllerClass

    def singlePlot(self, saveLoc = None):
        '''
        Takes the scopeGrab like data from the active lockInAmp class provided in initialisation.
        Smart plots the first record in the data: figures out if graph is FFT or not then extracts all relevant data and plots.
        If saveloc is given it saves the figure there using the date and time as its name, else it shows in a new window.

        :param saveLoc: Location to save figure to. If none it shows the figure.
        :return: None
        '''
        scopeGrab = self.controller.scopeGrab
        fig1 = pyplot.figure(figsize=(20,10))
        ax1  = fig1.add_subplot(111)

        data0   = scopeGrab[f'{self.controller.device}']['scopes']['0']['wave'][0][0] #[i][0] at end, i for record i

        fft = data0['channelmath'][0] == 2

        dt      = data0['dt']
        y_data  = data0['wave'][0]

        if fft:
            x_space = np.linspace(0, 0.5/dt, y_data.shape[0])
            ax1.semilogy(x_space, y_data, color='black', lw=0.8, marker='')

        else:
            x_space = np.linspace(0, y_data.shape[0]*dt, y_data.shape[0])
            ax1.plot(x_space, y_data, color='black', lw=0.8, marker='')

        ax1.set_xlim([x_space[0], x_space[-1]])
        ax1.axhline(y=0, color='grey', alpha=0.5, lw=1)

        if fft:
            ax1.set_xlabel('Frequency  [Hz]')
            ax1.set_ylabel('Amplitude Voltage  [V]')
        else:
            ax1.set_xlabel('time  [s]')
            ax1.set_ylabel('Scope Voltage  [V]')
        fig1.tight_layout()

        if saveLoc is not None:
            fig1.savefig(saveLoc + os.sep + datetime.datetime.now().strftime('%d-%m-%y_%H,%M,%S'))
            return
        else:
            pyplot.show()
            return

    def single_pythonFFT(self, saveLoc=None):
        '''
        Takes the scopeGrab like data from the active lockInAmp class provided in initialisation.
        Given the first recond in the  data is a wave (time basis) not an FFT (frequency basis)
        it uses scipy to perform an FFT.
        It automatically extracts all the data it needs and plots the calculated FFT. If a save location is given
        it saves the figure there using the date and time pre-empted by 'FFT' as its name, else it shows the figure.
        Safeties for data already FFT.

        Please note it has been seen that Python/scipy FFT is far less accurate than the device one.
        I wonder if this is because the device uses a demoulator to make its FFT, though this would seem slow
        and would have to be a demodulator not accessible in the software.

        :param saveLoc: Location to save figure to. If none it shows the figure.
        :return: None
        '''
        warnings.warn('This method is far less precise than using the fft within the lock-in amplifier (which I assume uses the demodulators)')

        scopeGrab = self.controller.scopeGrab
        fig1 = pyplot.figure(figsize=(20,10))
        gs   = gridspec.GridSpec(2,1)
        ax1  = fig1.add_subplot(gs[0])
        axf  = fig1.add_subplot(gs[1])

        data0   = scopeGrab[f'{self.controller.device}']['scopes']['0']['wave'][0][0] #[i][0] at end, i for record i

        if data0['channelmath'][0] == 2:
            warnings.warn('The data currently in scope Grab is not a wave, it is already an FFT. This function will not run.')#
            return

        dt      = data0['dt']
        y_data  = data0['wave'][0]
        n       = y_data.shape[0]

        window = scipy.signal.windows.hann(n) #hanning window improves fft performance for noise (bins leak less),
                                        #default for device, maybe why it seems better?
        fft     = scipy.fft.fft(y_data*window)
        f_space = np.linspace(0, 0.5/dt, n//2)
        x_space = np.linspace(0, n * dt, n)

        ax1.plot(    x_space, y_data, color='black', lw=0.8, marker='')
        axf.semilogy(f_space, 2/n * np.abs(fft[0:n//2]),    color='black', lw=0.8, marker='')

        ax1.set_xlim([x_space[0], x_space[-1]])
        ax1.axhline(y=0, color='grey', alpha=0.5, lw=1)
        ax1.set_ylabel('Scope Voltage  [V]')
        ax1.set_xlabel('time  [s]')

        axf.set_xlim([f_space[0], f_space[-1]])
        axf.set_ylabel('Amplitude Voltage  [V]')
        axf.set_xlabel('Frequency  [Hz]')

        fig1.tight_layout()

        if saveLoc is not None:
            fig1.savefig(saveLoc + os.sep + 'FFT ' +datetime.datetime.now().strftime('%d-%m-%y_%H,%M,%S'))
            return
        else:
            pyplot.show()
            return

    def processed_FFT(self, loadloc, useRAMdump = False, designator = datetime.datetime.now().strftime(
                                '%d-%m-%y'), saveloc=None, partial = False, devicename='dev5070'):
        '''
        Plots the processed FFT output from large file processing using DataProcesser.RAMDumpLargeFileProcess_FFT .
        Either uses the dt file extracted by the DataProcesser (faster) or the first RAMdump file if not
        available for some reason.
        Extracts data from these files then sends to generic_singlePlot.

        :param loadloc: Location to load the processed data from.
        :param useRAMdump: Bool, if true uses lowest RAMdump to get dt, if false uses extracted dt file (faster).
        :param designator: designator for RAMdump and processed like file format (see DataProcesser).
        :param saveloc: Passed to generic_singlePlot; savelocation for figure, shows figure if None.
        :param partial: Checks if processed file is parital or not. If false looks for non-partial file.
                    If non-false must provide the integer value of RAMdumps completed in the partial file,
                    which is seen in the file name: ...'PartialProcessed_n_designator'
        :param devicename: devicename needed if extracting from RAMdump. Defaults to current device name.
        :return:
        '''
        if useRAMdump:
            # noinspection PyTypeChecker
            dt = np.load(loadloc + os.sep + f'RAMdump0_{designator}.npy', allow_pickle=True)[()][
                f'{devicename}']['scopes']['0']['wave'][0][0]['dt']
        else:
            dt = np.load(loadloc + os.sep + f'dt_RAMdumpProcessed_{designator}.npy')[0]
        if partial:
            y_data = np.load(loadloc + os.sep + f'FFT_RAMdumpPartialProcessed_{partial}_{designator}.npy')
        else:
            y_data = np.load(loadloc + os.sep + f'FFT_RAMdumpProcessed__{designator}.npy')

        self.generic_singlePlot(y_data, dt, fft=True, saveLoc=saveloc)

    @staticmethod
    def generic_singlePlot(y_data, dt, fft=False, saveLoc=None):
        '''
        Plots data given to it rather than taking the scopeGrab from the active lockInAmp controller.
        The data still needs to be of a form like extracted scopeGrab like data, i.e. y_data array and dt float.
        Since the data is given manually the user must specify if it is an FFT or not. This code will NOT use
        scipy to make an FFT if a wave/non-FFT is given.

        :param y_data: array of y_data, form compatible with extracted scopeGrab like data.
        :param dt: float giving the time separation of y_data.
        :param fft: Bool for if the y_data represents an FFT or wave data. Default non-FFT.
        :param saveLoc: Location to save figure to. If none it shows the figure.
        :return: None
        '''
        fig1 = pyplot.figure(figsize=(20,10))
        ax1  = fig1.add_subplot(111)

        if type(y_data) == list:
            n = len(y_data)
        else:
            n = y_data.shape[0]

        if fft:
            x_space = np.linspace(0, 0.5/dt, n)
            ax1.semilogy(x_space, y_data, color='black', lw=0.8, marker='')

        else:
            x_space = np.linspace(0, n*dt, n)
            ax1.plot(x_space, y_data, color='black', lw=0.8, marker='')

        ax1.set_xlim([x_space[0], x_space[-1]])
        ax1.axhline(y=0, color='grey', alpha=0.5, lw=1)

        if fft:
            ax1.set_xlabel('Frequency  [Hz]')
            ax1.set_ylabel('Amplitude Voltage  [V]')
        else:
            ax1.set_xlabel('time  [s]')
            ax1.set_ylabel('Scope Voltage  [V]')
        fig1.tight_layout()

        if saveLoc is not None:
            fig1.savefig(saveLoc + os.sep + 'generic_' + datetime.datetime.now().strftime('%d-%m-%y_%H,%M,%S'))
            return
        else:
            pyplot.show()
            return


    def longGenerator(self):
        '''
        Takes the scopeGrab like data from the active lockInAmp class provided in initialisation.
        Extracts all records from the data. Determines if FFT and dt from first record.
        Puts each extracted record into an element in the list 'longData' then reshapes into an array 'neat_longData'


        :return: None
        '''
        scopeGrab = self.controller.scopeGrab

        self.longFFT = scopeGrab[f'{self.controller.device}']['scopes']['0']['wave'][0][0]['channelmath'][0] == 2
        self.longDt  = scopeGrab[f'{self.controller.device}']['scopes']['0']['wave'][0][0]['dt']

        self.longData = []
        for record in scopeGrab[f'{self.controller.device}']['scopes']['0']['wave']:
            self.longData.extend( record[0]['wave'][0] )

        self.neat_longData = np.array(self.longData)
        n = len(scopeGrab[f'{self.controller.device}']['scopes']['0']['wave'])
        l = scopeGrab[f'{self.controller.device}']['scopes']['0']['wave'][0][0]['wave'][0].shape[0]
        self.neat_longData = self.neat_longData.reshape( (n, l) )
        pass

    def longPlot(self, saveLoc=None):
        '''
        Takes data processed using 'longGenerator' and plots using 'generic_singlePlot'. FFT and dt
        determined using stored bool and float generated in 'longGenerator'.
        Passes saveLoc to plotting function.

        :param saveLoc: Location to save figure to. If none it shows the figure.
        :return: None
        '''
        try:
            self.longFFT
            warnings.warn('Be aware, this uses the last geneated longData not the current grabbed data.')
        except:
            warnings.warn('longData set not generated, doing now for current grabbed set.')
            self.longGenerator()

        if self.longFFT:
            fft_avg = np.average(self.neat_longData, axis=0)
            self.generic_singlePlot(fft_avg, self.longDt, fft=True, saveLoc=saveLoc)
        else:
            self.generic_singlePlot(self.longData, self.longDt, fft=False, saveLoc=saveLoc)

        pass

class DataProcesser:
    saveloc: str
    working_scopeGrabLike: dict
    working_output = None
    memory_scopeGrabLike: dict
    reserved_memory = None
    working_longArrayData: np.array
    dummyflag: dummyFlag


    def __init__(self, saveloc = None):
        '''
        Memory managed Large data processor. This class is for processing single or multiple GB files containing
        scopeGrab like data. Ultimately it can average the FFT data from several multiple GB files into a single
        FFT output.
        The class is memory managed due to the large file sizes. The memory storing variables are annotated at the
        start of the class and new variables should not be implemented. It is recommended that the file size being
        processed by less than a third of your PC RAM to prevent using all the PC RAM.

        :param saveloc: Location files to be loaded are saved in. Don't end in \
        '''
        self.saveloc = saveloc

    def loadToWorkingSingle(self, filename, saveloc = None):
        '''
        Loads designated file, on assumption its scopeGrab like data (see scope grabbing in LockInAmp class).
        It unpacks the 0D array to give back the scopeGrab like data (dict) and save it under the class memory
        'working_scopeGrabLike'.
        Contains safeties for save location not being specified.

        :param filename: name of file to load, include file type but not the \.
        :param saveloc: save location the file is located in, defaults to initialised savelocation in class. Don't include end \.
        :return: None
        '''
        try:
            if saveloc is None:
                saveloctemp = self.saveloc
            else:
                saveloctemp = saveloc
        except:
            warnings.warn('Please give a file path location, either in this function or as the variable \'saveloc\' within this class. This function will not run')
            return
        self.working_scopeGrabLike = np.load(
            saveloctemp + os.sep + filename, allow_pickle=True
        )[()]

    def commitToMemory(self):
        '''
        Commits working memory to 'permanent' memory.
        Saves a copy of class memory 'working_scopeGrabLike' to class memory 'memory_scopeGrabLike'.
        Warns about possible memory problems.
        :return: None
        '''
        warnings.warn('Please be aware of your PC RAM limits and that this commit doesn\'t cause these too be exceeded now or at a later date. \n'
                      'For your information. Large file processing duplicates the data size by extracting the data into an array \'working_longArrayData\'.')
        self.memory_scopeGrabLike = self.working_scopeGrabLike

    def clearMemory(self, outputs=False, memory=False, full=False):
        '''
        Clears class memory to free up RAM. Parameters define different levels of clearing.
        Always clears the working memories (not output): 'working_scopeGrabLike', 'working_longArrayData'
        To clear individual class memory please set it manually to a null value (None or blank dictionary).

        :param outputs: Clears the working output, 'working_output'
        :param memory: Clears the committed memory, 'memory_scopeGrabLike'
        :param full: Clears everything. Including those under 'outputs' and 'memory' it clears the 'reserved_memory'
        :return: None
        '''
        self.working_scopeGrabLike = {'blank': 1}
        self.working_longArrayData = {'blank': 1}

        if full:
            outputs = True
            memory  = True

        if outputs:
            self.working_output = None
        if memory:
            self.memory_scopeGrabLike = {'blank': 1}
        if full:
            self.reserved_memory = None


    def singleLargeFileProcess(self, devicename='dev5070'):
        '''
        Extracts all the individual records from a scopeGrab like and packs them into a single array.
        Extracts data from 'working_scopeGrabLike' and packs into 'working_longArrayData' in array form.
        Contains safeties for no working scopeGrab like data.

        :param devicename: Name of device used for unpacking the data. Defaults to current device name.
        :return: 'working_longArrayData'
        '''
        try:
            self.working_scopeGrabLike
        except:
            warnings.warn('No data loaded into class. Please load a \'scopeGrab\'-like data in using loadToWorkingSingle.')


        n = len(self.working_scopeGrabLike[f'{devicename}']['scopes']['0']['wave'])
        l = self.working_scopeGrabLike[f'{devicename}']['scopes']['0']['wave'][0][0]['wave'][0].shape[0]
        self.working_longArrayData = np.zeros(shape= (n, l) )
        i = 0
        while i < n:
            self.working_longArrayData[i] = self.working_scopeGrabLike[f'{devicename}']['scopes']['0'][
                'wave'][i][0]['wave'][0]
            i += 1

        return self.working_longArrayData

    def RAMDumpLargeFileProcess_FFT(self, totalNumber=None, designator = datetime.datetime.now().strftime(
                                '%d-%m-%y'), saveloc=None, devicename='dev5070', paused = None):
        '''
        Automates processing of many RAMdump type files containing FFT data. Produces average of all the FFT data.
        For RAMdump type files with name of form: 'RAMdumpi_designator.npy' where i the iterator and designator is as defined in params.
        Starting with iterator, i=0 until totalNumber.
        For each file it loads it into class working memory via 'loadToWorkingSingle' then prints confirmation.
        It checks for FFT data otherwise prints a warning and exits the function (without code crash).
        It extracts the data in the scopeGrab like into an array using 'singleLargeFileProcess'.
        Takes the average of all the extracted record FFTs then appends this average FFT onto the 'reserved_memory'
        list, which is set to a blank list when this function is initialised.
        After all files processed averages over the list of averaged FFTs to perform the combination of data from
        multiple files. Saves result to class memory 'working_output' and returns it.

        Safeties for no savelocation. Safeties for non FFT data.

        :param totalNumber: the total number of RAMdump files to use, starting at file 0. Safety for None
                            uses all 'RAM' named files in the directory.
        :param designator: RAMdump type files have a designator when saving (defaults to date of initial capture),
                        see RAMOverflow features in DAQ in lockInAmp class.
        :param saveloc: The location the RAMdump type files are saved. Don't end in \
        :param devicename: The device name used to capture the data. Defaults to current device name.
        :param paused: class with value variable containing a bool as to whether to pause or not, or a keyword
                    to terminate.
        :return: 'working_output', the FFT from averaging over all records in all RAMdumps
        '''
        if paused is None: #for pausing in mulitprocess, dummy flag if not
            paused = self.dummyflag
            paused.value = False

        try:
            if saveloc is None:
                saveloc = self.saveloc
        except:
            warnings.warn('Please give a file path location, either in this function or as the variable \'saveloc\' within this class. This function will not run')
            return

        partial = ''
        n_str   = ''

        self.reserved_memory = []
        if totalNumber is None:
            warnings.warn('Using total number of RAM dumps in directory.')
            check = []
            for s in os.listdir(saveloc):
                check.append('RAM' in s)
            totalNumber = np.count_nonzero(check)


        n = 0
        while n < totalNumber:
            start = time.time()
            filename = 'RAMdump%i_%s.npy' %(n, designator)
            self.loadToWorkingSingle(filename, saveloc)
            #print(f'Load time: {time.time() - start}')
            print(f'Loaded {filename}.')

            if n == 0:
                if not self.working_scopeGrabLike[f'{devicename}']['scopes']['0']['wave'][0][0]['channelmath'][0] == 2:
                    warnings.warn('The input scope data is not an FFT. If the data is a python processed FFT this check will not allow the input, in which case, disable this check to proceed. This function will not run.')
                    return

            self.singleLargeFileProcess(devicename)
            self.reserved_memory.append(
                np.average( self.working_longArrayData, axis=0 )
            )
            #print(f'Load and process time: {time.time() - start}')
            print(f'Processed and averaged {filename}.')
            #print(paused)
            while paused.value:
                if paused.value == 'die':
                    paused.value = 'dead'
                    partial = 'Partial'
                    n_str   = f'{n}'
                    n = totalNumber
                    break
                self.clearMemory()
                time.sleep(1)

            n += 1

        self.working_output = np.average(self.reserved_memory, axis=0)
        np.save(saveloc + os.sep + f'FFT_RAMdump{partial}Processed_{n_str}_{designator}', self.working_output)

        dt = self.working_scopeGrabLike[f'{devicename}']['scopes']['0']['wave'][0][0]['dt']
        np.save(saveloc + os.sep + f'dt_RAMdumpProcessed_{designator}', np.array([dt]))

        return self.working_output

    def RAMDumpLargeFileProcess_wave(self, totalNumber=None, designator = datetime.datetime.now().strftime(
                                '%d-%m-%y'), saveloc=None, devicename='dev5070', paused = None):
        '''


        :param totalNumber: the total number of RAMdump files to use, starting at file 0. Safety for None
                            uses all 'RAM' named files in the directory.
        :param designator: RAMdump type files have a designator when saving (defaults to date of initial capture),
                        see RAMOverflow features in DAQ in lockInAmp class.
        :param saveloc: The location the RAMdump type files are saved. Don't end in \
        :param devicename: The device name used to capture the data. Defaults to current device name.
        :param paused: class with value variable containing a bool as to whether to pause or not, or a keyword
                    to terminate.
        :return: 'working_output', the FFT from averaging over all records in all RAMdumps
        '''
        if paused is None: #for pausing in mulitprocess, dummy flag if not
            paused = self.dummyflag
            paused.value = False

        try:
            if saveloc is None:
                saveloc = self.saveloc
        except:
            warnings.warn('Please give a file path location, either in this function or as the variable \'saveloc\' within this class. This function will not run')
            return

        partial = ''
        n_str   = ''

        self.reserved_memory = []
        if totalNumber is None:
            warnings.warn('Using total number of RAM dumps in directory.')
            check = []
            for s in os.listdir(saveloc):
                check.append('RAM' in s)
            totalNumber = np.count_nonzero(check)


        n = 0
        while n < totalNumber:
            start = time.time()
            filename = 'RAMdump%i_%s.npy' %(n, designator)
            self.loadToWorkingSingle(filename, saveloc)
            #print(f'Load time: {time.time() - start}')
            print(f'Loaded {filename}.')

            if n == 0:
                if self.working_scopeGrabLike[f'{devicename}']['scopes']['0']['wave'][0][0]['channelmath'][0] == 2:
                    warnings.warn('The input scope data is an FFT. This function takes wave input and uses scipy to FFT. This function will not run.')
                    return

            self.singleLargeFileProcess(devicename)
            self.working_longArrayData = self.working_longArrayData.flatten(order='C')
            number = self.working_longArrayData.shape[0]
            self.reserved_memory.append(
                2 / number * np.abs( scipy.fft(scipy.signal.windows.hann(number)
                                               * self.working_longArrayData)[0:number // 2])
            )
            #print(f'Load and process time: {time.time() - start}')
            print(f'Processed and FFT taken: {filename}.')
            #print(paused)
            while paused.value:
                if paused.value == 'die':
                    paused.value = 'dead'
                    partial = 'Partial'
                    n_str   = f'{n}'
                    n = totalNumber
                    break
                self.clearMemory()
                time.sleep(1)

            n += 1

        self.working_output = np.average(self.reserved_memory, axis=0)
        np.save(saveloc + os.sep + f'FFT_RAMdump{partial}ProcessedFFT_{n_str}_{designator}', self.working_output)

        dt = self.working_scopeGrabLike[f'{devicename}']['scopes']['0']['wave'][0][0]['dt']
        np.save(saveloc + os.sep + f'dt_RAMdumpProcessedFFT_{designator}', np.array([dt]))

        return self.working_output

