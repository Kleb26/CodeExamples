import numpy as np
import inspect
import math
import types

#file = open('Violet_save.pkl', 'wb')

class Feat:
    name: str
    description: str
    special: str
    instances: int

    def __init__(self, name, descrip, instances = 1):
        self.name = name
        self.description = descrip
        self.instances = instances

    def printout(self):
        print(f'{self.name}:')
        print(f'{self.description}')
        try:
            print(f'Special:  {self.special}')
        except:
            pass
        print(f'Instances: {self.instances}')

class Talent:
    name: str
    description: str
    uses: float
    current_uses: int

    def __init__(self, name, descrip, uses = 0):
        self.name = name
        self.description = descrip
        if uses > 0:
            self.current_uses = uses
            self.uses = uses
        else:
            self.uses = math.inf

    def use(self):
        if self.uses != math.inf:
            if self.current_uses > 0:
                self.current_uses -= 1
            else:
                print(f'No uses left of {self.name}')

    def printout(self):
        print(f'{self.name}:')
        print(f'{self.description}')
        print(f'UsesPerEncounter: {self.uses}')
        try:
            print(f'UsesLeft: {self.current_uses}')
        except:
            pass

    def resetUse(self):
        self.current_uses = self.uses

class ForcePower:
    name: str
    description: str
    special: str
    target: str
    time: str
    type: str
    DC_table: np.array
    instances: int
    current_uses: int

    type_list = ['', 'Light', 'Dark', 'Telekinetic', 'MindAffecting']

    def __init__(self, name, desc, target, time, typeIndex=0):
        self.name = name
        self.instances = 1
        self.current_uses = 1
        self.type = self.type_list[typeIndex]
        self.description = desc
        self.target = target
        self.time = time

    def use(self):
        if self.current_uses > 0:
            self.current_uses -= 1
        else:
            print(f'No uses left of {self.name}')

    def increase_instance(self, new_copies=1):
        self.instances += new_copies
        self.current_uses = self.instances

    def resetUse(self):
        self.current_uses = self.instances

    def printout(self):
        print(f'{self.name}:')
        print(f'{self.description}')
        print(f'Target: {self.target}')
        print(f'Action Cost: {self.time}')
        try:
            print(f'Special: {self.special}')
        except:
            pass
        print(f'Uses Remaining: {self.current_uses} /{self.instances}')
        try:
            self.DC_table
            print('DC Table Exists')
        except:
            pass

class MiscQuality:
    name: str
    description: str
    special: str
    uses: int
    current_uses: int
    source: str

    def __init__(self, name, descr):
        self.name = name
        self.description = descr

    def printout(self):
        print(f'{self.name}:')
        print(f'{self.description}')
        try:
            print(f'Special:  {self.special}')
        except:
            pass
        try:
            print(f'Source:  {self.source}')
        except:
            pass
        try:
            print(f'Current Uses:  {self.current_uses} /{self.uses}')
        except:
            pass

#import from * to console then:
#Violet = LoadViolet()


class LoadViolet:
    def __new__(cls):
        import pickle
        file = open('Violet_save.pkl', 'rb')
        inst = pickle.load(file)
        return inst

class LoadBackup:
    def __new__(cls):
        import pickle
        file = open('Violet_backup.pkl', 'rb')
        inst = pickle.load(file)
        return inst

#TO ADD NEW METHOD TO CLASS INSTANCE:
# class.newMethod = types.MethodType(DefinedFunction, class instance)
#where DefinedFunction is the name of a previously defined function, including self input;
#class instance is the name of the class instance to attach too.
#This will not update Violet template below unless manually add

#TO ADD TO CLASS:
#class.newMethod = DefinedFunction

#DIFFERENCE:
#For 'Violet' this could refer to the instance or the class (same name, mb).
#Hence second method doesnt work as it reads Violet as the instance not class.
#Hence use option one to append to Violet, at instance level (only one anyway) and
#use option two for classes like Feat, Talent etc. as this updates all instances

class Violet:
    featsList: list #Feat (cap) reserved for class instance in naming
    talentList: list #Talent (cap) reserved for class instance in naming
    forcePowersList: list #ForcePower (cap) reserved for class instance in naming
    miscList: list #Misc (cap) reserved for class instance in naming
    useable_forcePowersList: list
    forcePowerTypeList: list


    type_list = ['', 'Light', 'Dark', 'Telekinetic', 'MindAffecting']

    def howToAddNewMethod(self):
        print('Violet.newMethod = types.MethodType(DefinedFunction, Violet)')
        print('Where the function is defined previously and has self input,')
        print('and the instance of Violet is called Violet.')

    def saveViolet(self):
        import pickle
        file = open('Violet_save.pkl', 'wb')
        pickle.dump(self, file)

    def backup(self):
        import pickle
        file = open('Violet_backup.pkl', 'wb')
        pickle.dump(self, file)

    #FEAT LISTING
    def generate_featsList(self):
        self.featsList = []
        allmembers = np.array( inspect.getmembers(self)[27:] ) #27 members deafult to classe like __init__
        self.featsList = [entry for entry in allmembers[:,1] if 'Feat' in str(entry)]

    def print_feats(self):
        self.generate_featsList()
        for feats in self.featsList:
            print('')
            feats.printout()

    #TALENT LISTING
    def generate_talentsList(self):
        self.talentList = []
        allmembers = np.array( inspect.getmembers(self)[27:] )
        self.talentList = [entry for entry in allmembers[:,1] if 'Talent' in str(entry)]

    def print_talents(self):
        self.generate_talentsList()
        for feats in self.talentList:
            print('')
            feats.printout()

    #FORCE POWER LISTING
    def generate_forcePowerList(self):
        self.forcePowersList = []
        allmembers = np.array( inspect.getmembers(self)[27:] )
        self.forcePowersList = [entry for entry in allmembers[:,1] if 'ForcePower' in str(entry)]

    def generate_useable_forcePowerList(self):
        self.generate_forcePowerList()
        self.useable_forcePowersList = [powers for powers in self.forcePowersList if powers.current_uses > 0]

    def print_forcePowers(self):
        self.generate_forcePowerList()
        for feats in self.forcePowersList:
            print('')
            feats.printout()

    def print_useable_forcePowers(self):
        self.generate_useable_forcePowerList()
        for feats in self.useable_forcePowersList:
            print('')
            feats.printout()

    def print_short_forcePowers(self):
        self.generate_forcePowerList()
        for powers in self.forcePowersList:
            print('')
            print(f'{powers.name}')
            print(f'Uses: {powers.current_uses} /{powers.instances}')

    def generate_type_forcePowerList(self, typeIndex, useable=False):
        self.generate_forcePowerList()
        if useable:
            min = 1
        else:
            min = 0
        self.forcePowerTypeList = [powers for powers in self.forcePowersList if (
            powers.type == self.type_list[typeIndex] and  powers.current_uses >= min ) ]

    def print_type_forcePowers(self):
        try:
            for feats in self.forcePowerTypeList:
                print('')
                feats.printout()
        except:
            print('Generate type list first. Due to input this isn\'t handled here')

    #MISC LISTING

    def generate_miscList(self):
        self.miscList = []
        allmembers = np.array(inspect.getmembers(self)[27:])
        self.miscList = [entry for entry in allmembers[:, 1] if 'MiscQuality' in str(entry)]

    def print_misc(self):
        self.generate_miscList()
        for feats in self.miscList:
            print('')
            feats.printout()


    #RESET USES

    def reset_talents(self):
        self.generate_talentsList()
        for talents in self.talentList:
            if talents.uses != math.inf:
                talents.current_uses = talents.uses

    def reset_forcePowers(self):
        self.generate_forcePowerList()
        for powers in self.forcePowersList:
            powers.current_uses = powers.instances
