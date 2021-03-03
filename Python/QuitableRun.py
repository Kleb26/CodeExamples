from LockInMaster import *
import multiprocessing as mp
import time

def mainTasks(alive):
    saveloc = r'C:\Python\Experiment control and DAQ\export'
    lockIn = lockInAmp()
    lockIn.saveLoc = saveloc

    miscc = misc()
    miscc.dodgy_printToLog(saveloc)


    lockIn.scope_configure_mainInput(sample_rate=7.5e6, sample_length=2 ** 14)
    lockIn.initialise_scopeModule(1)
    lockIn.takeScopeMemory(3500.0, flag=alive , RAMlimitGB=1, designator='waveLunchTest1') #need to add flag into code
    miscc.undo_dodgy_printToLog()
    print('SubProcess Finished. User must exit main process.')

if __name__ == '__main__':
    #q = mp.Queue()    #passing variables option 1
    manager = mp.Manager()  #allows shared variables via a server manager
    live = manager.Value('flag', True)

    subprocess = mp.Process(target=mainTasks, args=(live,))
    subprocess.daemon = False
    subprocess.start()
    print('SubProcess mainTasks started, type \'die\' to kill the subprocess.')
    time.sleep(1)
    while True:
        check = input() #this is very hard to poll if print not going to log
        if check == 'die':
            live.value = False
            time.sleep(1) #Require sleep otherwise there's a 'BrokenPipeError
            #Believe this is a result of the next 2 lines running too quick and closing main thread before
            #live.value is correctly updated
            #Further the issue is the manager dies with the main thread so the flag varibale cannot be read by subthread.
            print('Kill command sent, main process will end. Subprocess should save then end.')
            break