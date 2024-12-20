from buildpathways import *
from SALib.sample import saltelli
from SALib.analyze import sobol
from SALib import ProblemSpec
import numpy as np

cwd = os.getcwd()

#concat all dfs
conversions_df = pd.read_excel(file_io_obj,'Conversions')
transmissioninfra_df = pd.read_excel(file_io_obj,'TransmissionInfra')
locations_df = pd.read_excel(file_io_obj,'Locations')     
production_df = pd.read_excel(file_io_obj,'ProductionMethods')
energysources_df = pd.read_excel(file_io_obj,'EnergySources')
uses_df = pd.read_excel(file_io_obj,'Uses')
storage_df = pd.read_excel(file_io_obj,'Storage')
allinputs = pd.concat([storage_df,energysources_df,conversions_df,transmissioninfra_df,production_df])
allinputs = allinputs.replace('NAN', np.nan)

#select the supply chains based on which could meet low carbon targets?
supplychains = create_options()

H2_supply_chain.instances = supplychains

def get_dict_stages(instance):
    if instance.pathwaytype == 'Simple':
        dict_stages = {'S0':instance.energysource,
                    'S1':instance.tinfra[0],
                    'S2':instance.productionmeth,
                    'S3':instance.conversions[0],
                    'S4':instance.storage_method[0],
                    'S5':instance.tinfra[1]}
       
    elif instance.pathwaytype == 'Energy to Prod':
        dict_stages = {'S0':instance.energysource,
                    'S1':instance.tinfra[0],
                    'S2':instance.productionmeth,
                    'S3':instance.conversions[0],
                    'S4':instance.tinfra[1],
                    'S5':instance.conversions[1],
                    'S6':instance.storage_method[0],
                    'S7':instance.tinfra[2],
                    'S8':instance.conversions[2],
                    'S9':instance.storage_method[1],
                    'S10':instance.tinfra[3]}
    
    return dict_stages

#get the sobol variables, each stage is a group
def getvalues(instance):
    stagedict = get_dict_stages(instance)
    inputrows={}
    if len(stagedict) == 6:
        s0row=allinputs[allinputs['ID'] ==stagedict['S0'].ID].iloc[0]
        inputrows['S0'] = [s0row['Emissions (gCO2e/kWh)'],
                        s0row['Utilisation Factor']]
        s1row=allinputs[allinputs['ID'] ==stagedict['S1'].ID].iloc[0]
        inputrows['S1'] = [s1row['Yield'],
                        s1row['Capacity Factor'],
                        s1row['_loss_km'],
                        s1row['Lifetime'],
                        s1row['Speed'],
                        s1row['Emissions_embodied'],
                        s1row['Emissions_embodiedkm'],
                        s1row['Emissions_process'],
                        s1row['Emissions_processkm'],
                        s1row['Emissions_OM'],
                        s1row['Emissions_OMkm'],
                        s1row['Energy_embodied'],
                        s1row['Energy_embodiedkm'],
                        s1row['Energy_process'],
                        s1row['Energy_processkm'],
                        s1row['Energy_OM'],
                        s1row['Energy_OMkm'],
                        s1row['H2emissions'],
                        s1row['H2emissionskm']]
        s2row=allinputs[allinputs['ID'] ==stagedict['S2'].ID].iloc[0]
        inputrows['S2'] = [s2row['_yield'],
                        s2row['Capacity Factor'],
                        s2row['Lifetime'],
                        s2row['Emissions_embodied'],
                        s2row['Emissions_process'],
                        s2row['Emissions_OM'],
                        s2row['Energy_embodied'],
                        s2row['Energy_process'],
                        s2row['Energy_OM'],
                        s2row['H2emissions']]
        s3row=allinputs[allinputs['ID'] ==stagedict['S3'].ID].iloc[0]
        inputrows['S3'] = [s3row['Yield'],
                        s3row['Capacity Factor'],
                        s3row['Lifetime'],
                        s3row['Emissions_embodied'],
                        s3row['Emissions_process'],
                        s3row['Emissions_OM'],
                        s3row['Energy_embodied'],
                        s3row['Energy_process'],
                        s3row['Energy_OM'],
                        s3row['H2emissions']]
        s4row=allinputs[allinputs['ID'] ==stagedict['S4'].ID].iloc[0]
        inputrows['S4'] = [s4row['Yield'],
                        s4row['Capacity Factor'],
                        s4row['Lifetime'],
                        s4row['_loss_day'],
                        s4row['Emissions_embodied'],
                        s4row['Emissions_process'],
                        s4row['Emissions_OM'],
                        s4row['Energy_embodied'],
                        s4row['Energy_process'],
                        s4row['Energy_OM'],
                        s4row['H2emissions']]
        s5row=allinputs[allinputs['ID'] ==stagedict['S5'].ID].iloc[0]
        inputrows['S5'] = [s5row['Yield'],
                        s5row['Capacity Factor'],
                        s5row['_loss_km'],
                        s5row['Lifetime'],
                        s5row['Speed'],
                        s5row['Emissions_embodied'],
                        s5row['Emissions_embodiedkm'],
                        s5row['Emissions_process'],
                        s5row['Emissions_processkm'],
                        s5row['Emissions_OM'],
                        s5row['Emissions_OMkm'],
                        s5row['Energy_embodied'],
                        s5row['Energy_embodiedkm'],
                        s5row['Energy_process'],
                        s5row['Energy_processkm'],
                        s5row['Energy_OM'],
                        s5row['Energy_OMkm'],
                        s5row['H2emissions'],
                        s5row['H2emissionskm']]
        variablenames = ['S0 Emissions (gCO2e/kWh)','S0 Utilisation Factor','S1 Yield','S1 Capacity Factor','S1 Loss km','S1 Lifetime','S1 Speed','S1 Emissions Embodied',
                         'S1 Emissions Embodied km','S1 Emissions Process','S1 Emissions Process km','S1 Emissions OM','S1 Emissions OM km','S1 Energy Embodied',
                         'S1 Energy Embodied km','S1 Energy Process','S1 Energy Process km','S1 Energy OM','S1 Energy OM km','S1 H2 Emissions','S1 H2 Emissions km',
                         'S2 Yield','S2 Capacity Factor','S2 Lifetime','S2 Emissions Embodied','S2 Emissions Process','S2 Emissions OM','S2 Energy Embodied',
                         'S2 Energy Process','S2 Energy OM','S2 H2 Emissions','S3 Yield','S3 Capacity Factor','S3 Lifetime','S3 Emissions Embodied','S3 Emissions Process',
                         'S3 Emissions OM','S3 Energy Embodied','S3 Energy Process','S3 Energy OM','S3 H2 Emissions',
                         'S4 Yield','S4 Capacity Factor','S4 Lifetime','S4 Loss day','S4 Emissions Embodied','S4 Emissions Process','S4 Emissions OM',
                         'S4 Energy Embodied','S4 Energy Process','S4 Energy OM','S4 H2 Emissions',
                         'S5 Yield','S5 Capacity Factor','S5 Loss km','S5 Lifetime','S5 Speed','S5 Emissions Embodied','S5 Emissions Embodied km','S5 Emissions Process',
                         'S5 Emissions Process km','S5 Emissions OM','S5 Emissions OM km','S5 Energy Embodied','S5 Energy Embodied km','S5 Energy Process',
                         'S5 Energy Process km','S5 Energy OM','S5 Energy OM km','S5 H2 Emissions','S5 H2 Emissions km']
        
    elif len(stagedict) == 11:  
        s0row=allinputs[allinputs['ID'] ==stagedict['S0'].ID].iloc[0]
        inputrows['S0'] = [s0row['Emissions (gCO2e/kWh)'],
                        s0row['Utilisation Factor']]
        s1row=allinputs[allinputs['ID'] ==stagedict['S1'].ID].iloc[0]
        inputrows['S1'] = [s1row['Yield'],
                        s1row['Capacity Factor'],
                        s1row['_loss_km'],
                        s1row['Lifetime'],
                        s1row['Speed'],
                        s1row['Emissions_embodied'],
                        s1row['Emissions_embodiedkm'],
                        s1row['Emissions_process'],
                        s1row['Emissions_processkm'],
                        s1row['Emissions_OM'],
                        s1row['Emissions_OMkm'],
                        s1row['Energy_embodied'],
                        s1row['Energy_embodiedkm'],
                        s1row['Energy_process'],
                        s1row['Energy_processkm'],
                        s1row['Energy_OM'],
                        s1row['Energy_OMkm'],
                        s1row['H2emissions'],
                        s1row['H2emissionskm']]
        s2row=allinputs[allinputs['ID'] ==stagedict['S2'].ID].iloc[0]
        inputrows['S2'] = [s2row['_yield'],
                        s2row['Capacity Factor'],
                        s2row['Lifetime'],
                        s2row['Emissions_embodied'],
                        s2row['Emissions_process'],
                        s2row['Emissions_OM'],
                        s2row['Energy_embodied'],
                        s2row['Energy_process'],
                        s2row['Energy_OM'],
                        s2row['H2emissions']]
        s3row=allinputs[allinputs['ID'] ==stagedict['S3'].ID].iloc[0]  
        inputrows['S3'] = [s3row['Yield'],
                        s3row['Capacity Factor'],
                        s3row['Lifetime'],
                        s3row['Emissions_embodied'],
                        s3row['Emissions_process'],
                        s3row['Emissions_OM'],
                        s3row['Energy_embodied'],
                        s3row['Energy_process'],
                        s3row['Energy_OM'],
                        s3row['H2emissions']]
        s4row=allinputs[allinputs['ID'] ==stagedict['S4'].ID].iloc[0]
        inputrows['S4'] = [s4row['Yield'],
                        s4row['Capacity Factor'],
                        s4row['_loss_km'],
                        s4row['Lifetime'],
                        s4row['Speed'],
                        s4row['Emissions_embodied'],
                        s4row['Emissions_embodiedkm'],
                        s4row['Emissions_process'],
                        s4row['Emissions_processkm'],
                        s4row['Emissions_OM'],
                        s4row['Emissions_OMkm'],
                        s4row['Energy_embodied'],
                        s4row['Energy_embodiedkm'],
                        s4row['Energy_process'],
                        s4row['Energy_processkm'],
                        s4row['Energy_OM'],
                        s4row['Energy_OMkm'],
                        s4row['H2emissions'],
                        s4row['H2emissionskm']]
        s5row=allinputs[allinputs['ID'] ==stagedict['S5'].ID].iloc[0]
        inputrows['S5'] = [s5row['Yield'],
                        s5row['Capacity Factor'],
                        s5row['Lifetime'],
                        s5row['Emissions_embodied'],
                        s5row['Emissions_process'],
                        s5row['Emissions_OM'],
                        s5row['Energy_embodied'],
                        s5row['Energy_process'],
                        s5row['Energy_OM'],
                        s5row['H2emissions']]
        s6row=allinputs[allinputs['ID'] ==stagedict['S6'].ID].iloc[0]
        inputrows['S6'] = [s6row['Yield'],
                        s6row['Capacity Factor'],
                        s6row['Lifetime'],
                        s6row['_loss_day'],
                        s6row['Emissions_embodied'],
                        s6row['Emissions_process'],
                        s6row['Emissions_OM'],
                        s6row['Energy_embodied'],
                        s6row['Energy_process'],
                        s6row['Energy_OM'],
                        s6row['H2emissions']]
        s7row=allinputs[allinputs['ID'] ==stagedict['S7'].ID].iloc[0]
        inputrows['S7'] = [s7row['Yield'],
                        s7row['Capacity Factor'],
                        s7row['_loss_km'],
                        s7row['Lifetime'],
                        s7row['Speed'],
                        s7row['Emissions_embodied'],
                        s7row['Emissions_embodiedkm'],
                        s7row['Emissions_process'],
                        s7row['Emissions_processkm'],
                        s7row['Emissions_OM'],
                        s7row['Emissions_OMkm'],
                        s7row['Energy_embodied'],
                        s7row['Energy_embodiedkm'],
                        s7row['Energy_process'],
                        s7row['Energy_processkm'],
                        s7row['Energy_OM'],
                        s7row['Energy_OMkm'],
                        s7row['H2emissions'],
                        s7row['H2emissionskm']]
        s8row=allinputs[allinputs['ID'] ==stagedict['S8'].ID].iloc[0]
        inputrows['S8'] = [s8row['Yield'],
                        s8row['Capacity Factor'],
                        s8row['Lifetime'],
                        s8row['Emissions_embodied'],
                        s8row['Emissions_process'],
                        s8row['Emissions_OM'],
                        s8row['Energy_embodied'],
                        s8row['Energy_process'],
                        s8row['Energy_OM'],
                        s8row['H2emissions']]
        s9row=allinputs[allinputs['ID'] ==stagedict['S9'].ID].iloc[0]
        inputrows['S9'] = [s9row['Yield'],
                        s9row['Capacity Factor'],
                        s9row['Lifetime'],
                        s9row['_loss_day'],
                        s9row['Emissions_embodied'],
                        s9row['Emissions_process'],
                        s9row['Emissions_OM'],
                        s9row['Energy_embodied'],
                        s9row['Energy_process'],
                        s9row['Energy_OM'],
                        s9row['H2emissions']]
        s10row=allinputs[allinputs['ID'] ==stagedict['S10'].ID].iloc[0]
        inputrows['S10'] = [s10row['Yield'],
                        s10row['Capacity Factor'],
                        s10row['_loss_km'],
                        s10row['Lifetime'],
                        s10row['Speed'],
                        s10row['Emissions_embodied'],
                        s10row['Emissions_embodiedkm'],
                        s10row['Emissions_process'],
                        s10row['Emissions_processkm'],
                        s10row['Emissions_OM'],
                        s10row['Emissions_OMkm'],
                        s10row['Energy_embodied'],
                        s10row['Energy_embodiedkm'],
                        s10row['Energy_process'],
                        s10row['Energy_processkm'],
                        s10row['Energy_OM'],
                        s10row['Energy_OMkm'],
                        s10row['H2emissions'],
                        s10row['H2emissionskm']]
        variablenames = ['S0 Emissions (gCO2e/kWh)','S0 Utilisation Factor','S1 Yield','S1 Capacity Factor','S1 Loss km','S1 Lifetime','S1 Speed','S1 Emissions Embodied',
                         'S1 Emissions Embodied km','S1 Emissions Process','S1 Emissions Process km','S1 Emissions OM','S1 Emissions OM km','S1 Energy Embodied',
                         'S1 Energy Embodied km','S1 Energy Process','S1 Energy Process km','S1 Energy OM','S1 Energy OM km','S1 H2 Emissions','S1 H2 Emissions km',
                         'S2 Yield','S2 Capacity Factor','S2 Lifetime','S2 Emissions Embodied','S2 Emissions Process','S2 Emissions OM','S2 Energy Embodied',
                         'S2 Energy Process','S2 Energy OM','S2 H2 Emissions',
                         'S3 Yield','S3 Capacity Factor','S3 Lifetime','S3 Emissions Embodied','S3 Emissions Process','S3 Emissions OM','S3 Energy Embodied',
                         'S3 Energy Process','S3 Energy OM','S3 H2 Emissions',
                         'S4 Yield','S4 Capacity Factor','S4 Loss km','S4 Lifetime','S4 Speed','S4 Emissions Embodied','S4 Emissions Embodied km',
                         'S4 Emissions Process','S4 Emissions Process km','S4 Emissions OM','S4 Emissions OM km','S4 Energy Embodied','S4 Energy Embodied km',
                         'S4 Energy Process','S4 Energy Process km','S4 Energy OM','S4 Energy OM km','S4 H2 Emissions','S4 H2 Emissions km',
                         'S5 Yield','S5 Capacity Factor','S5 Lifetime','S5 Emissions Embodied','S5 Emissions Process','S5 Emissions OM','S5 Energy Embodied',
                         'S5 Energy Process','S5 Energy OM','S5 H2 Emissions',
                         'S6 Yield','S6 Capacity Factor','S6 Lifetime','S6 Loss day','S6 Emissions Embodied','S6 Emissions Process','S6 Emissions OM',
                         'S6 Energy Embodied','S6 Energy Process','S6 Energy OM','S6 H2 Emissions',
                         'S7 Yield','S7 Capacity Factor','S7 Loss km','S7 Lifetime','S7 Speed','S7 Emissions Embodied','S7 Emissions Embodied km','S7 Emissions Process',
                         'S7 Emissions Process km','S7 Emissions OM','S7 Emissions OM km','S7 Energy Embodied','S7 Energy Embodied km','S7 Energy Process',
                         'S7 Energy Process km','S7 Energy OM','S7 Energy OM km','S7 H2 Emissions','S7 H2 Emissions km',
                         'S8 Yield','S8 Capacity Factor','S8 Lifetime','S8 Emissions Embodied','S8 Emissions Process','S8 Emissions OM','S8 Energy Embodied',
                         'S8 Energy Process','S8 Energy OM','S8 H2 Emissions',
                         'S9 Yield','S9 Capacity Factor','S9 Lifetime','S9 Loss day','S9 Emissions Embodied','S9 Emissions Process','S9 Emissions OM',
                         'S9 Energy Embodied','S9 Energy Process','S9 Energy OM','S9 H2 Emissions',
                         'S10 Yield','S10 Capacity Factor','S10 Loss km','S10 Lifetime','S10 Speed','S10 Emissions Embodied','S10 Emissions Embodied km','S10 Emissions Process',
                         'S10 Emissions Process km','S10 Emissions OM','S10 Emissions OM km','S10 Energy Embodied','S10 Energy Embodied km','S10 Energy Process',
                         'S10 Energy Process km','S10 Energy OM','S10 Energy OM km','S10 H2 Emissions','S10 H2 Emissions km',]                         
                   
    return inputrows,variablenames

#process values in input rows, remove nan, if no bound convert to a bound, make sure lower then higher
def processvalues(inputrows,namesoriginal):
    newvalues = []
    namesnew = []
    #return all values as list of dicts for each stage in from stage:[num:num,num2:num2]
    y=0
    for key,value in inputrows.items():
        for x in range(len(value)):
            #adjust variable name list to account for multiple energy variables
            if ':' in str(value[x]):
                a = value[x].split(",")
                for b in a:
                    c = b.split(":")
                    name = namesoriginal[y]+'*'+c[0]
                    namesnew.append(name)

            else:
                namesnew.append(namesoriginal[y])
            y+=1
            #if nan convert to 0
            if str(value[x]) == 'nan':
                newvalues.append('0;0.000001')
            
            #if dictvalue convert to a bound
            elif ':' in str(value[x]) and ',' not in str(value[x]):
                if ';' in str(value[x]):
                    a = value[x].split(":")
                    newvalues.append(a[1])
                elif ';' not in str(value[x]):
                    a =value[x].split(":")
                    a1 = float(a[1])
                    b = a1+0.000001
                    newvalues.append(str(a1)+';'+str(b))

            #if no bound convert to a bound
            elif ',' not in str(value[x]) and ':' not in str(value[x]) and ';' not in str(value[x]):
                if value[x]==1:
                    b = value[x]-0.000001
                else:
                    b = value[x]+0.000001
                newvalues.append(str(value[x])+';'+str(b))
            
            #if bound and no string leave as is
            elif ';' in str(value[x]) and ',' not in str(value[x]) and ':' not in str(value[x]):
                newvalues.append(value[x])
            
            #if multiple variables convert to a list of bounds     
            elif ',' in str(value[x]):
                listvalues = str(value[x]).split(",")
                valuetemp=[]
                for listval in listvalues:
                    if ':' in str(listval):
                        if ';' in str(listval):
                            a =listval.split(":")
                            a1 = a[1]
                            newvalues.append(a1)
                        elif ';' not in str(listval):
                            a =listval.split(":")
                            a1 = float(a[1])
                            b = a1+0.000001
                            newvalues.append(str(a1)+';'+str(b))
                    elif ';' in str(listval):
                        newvalues.append(listval)
                    else:
                        a1 = float(listval)
                        if a1==1:
                            b = a1-0.000001
                        else:
                            b = a1+0.000001
                        newvalues.append(str(a1)+';'+str(b))

                     
            else:
                if ':' in str(value[x]):
                    a =value[x].split(":")
                    a1 = float(a[1])
                    b = a1+0.000001
                    newvalues.append(str(a1)+';'+str(b))
    
    if len(newvalues) != len(namesnew):
        print('Error, values and names not the same length')
        exit()
    
    #check that the first value is lower than the second and put in form needed for sobol
    finallist = []
    for i in range(len(newvalues)):
        newval = newvalues[i]
        if type(newval) is list:
            pass
        else:
            newval = newval.split(";")
            newvalues[i] = [float(newval[0]),float(newval[1])]

        newval = [float(newval[0]),float(newval[1])]

        if newval[0] > newval[1]:
            finallist.append([newval[1],newval[0]])
        elif newval[0] == newval[1]:
            finallist.append([newval[0],newval[0]+0.000001])
        else:
            finallist.append([newval[0],newval[1]])

    return finallist,namesnew

#define function to be used in sobol analysis
def func(samplevalues,names,instance):
    
    dict_values = {}
    for variable,name in zip(samplevalues,names):
        if '*' in name:
            variable_name = name.split("*")[0]
            energy_name = name.split("*")[1]
            if variable_name in dict_values:
                dict_values[variable_name][energy_name] = variable
            else:
                dict_values[variable_name] = {energy_name:variable}
        else:
            dict_values[name] = [variable]

    #update the variables using the samplevalues
    if len(names) < 100:
        instance.energysource.sobol_update(dict_values['S0 Emissions (gCO2e/kWh)'],dict_values['S0 Utilisation Factor'])
        instance.tinfra[0].sobol_update(dict_values['S1 Yield'],dict_values['S1 Capacity Factor'],dict_values['S1 Loss km'],dict_values['S1 Lifetime'],
                                        dict_values['S1 Speed'],dict_values['S1 Emissions Embodied'],dict_values['S1 Emissions Embodied km'],
                                        dict_values['S1 Emissions Process'],dict_values['S1 Emissions Process km'],dict_values['S1 Emissions OM'],
                                        dict_values['S1 Emissions OM km'],dict_values['S1 Energy Embodied'],dict_values['S1 Energy Embodied km'],
                                        dict_values['S1 Energy Process'],dict_values['S1 Energy Process km'],dict_values['S1 Energy OM'],
                                        dict_values['S1 Energy OM km'],dict_values['S1 H2 Emissions'],dict_values['S1 H2 Emissions km'])
        instance.productionmeth.sobol_update(dict_values['S2 Yield'],dict_values['S2 Capacity Factor'],dict_values['S2 Lifetime'],
                                            dict_values['S2 Emissions Embodied'],dict_values['S2 Emissions Process'],dict_values['S2 Emissions OM'],
                                            dict_values['S2 Energy Embodied'],dict_values['S2 Energy Process'],dict_values['S2 Energy OM'],
                                            dict_values['S2 H2 Emissions'])
        instance.conversions[0].sobol_update(dict_values['S3 Yield'],dict_values['S3 Capacity Factor'],dict_values['S3 Lifetime'],
                                            dict_values['S3 Emissions Embodied'],dict_values['S3 Emissions Process'],dict_values['S3 Emissions OM'],
                                            dict_values['S3 Energy Embodied'],dict_values['S3 Energy Process'],dict_values['S3 Energy OM'],
                                            dict_values['S3 H2 Emissions'])
        instance.storage_method[0].sobol_update(dict_values['S4 Yield'],dict_values['S4 Capacity Factor'],dict_values['S4 Loss day'],dict_values['S4 Lifetime'],
                                                dict_values['S4 Emissions Embodied'],dict_values['S4 Emissions Process'], dict_values['S4 Emissions OM'],
                                                dict_values['S4 Energy Embodied'],dict_values['S4 Energy Process'],dict_values['S4 Energy OM'],
                                                dict_values['S4 H2 Emissions'])
        instance.tinfra[1].sobol_update(dict_values['S5 Yield'],dict_values['S5 Capacity Factor'],dict_values['S5 Loss km'],dict_values['S5 Lifetime'],
                                        dict_values['S5 Speed'],dict_values['S5 Emissions Embodied'],dict_values['S5 Emissions Embodied km'],
                                        dict_values['S5 Emissions Process'],dict_values['S5 Emissions Process km'],dict_values['S5 Emissions OM'],
                                        dict_values['S5 Emissions OM km'],dict_values['S5 Energy Embodied'],dict_values['S5 Energy Embodied km'],
                                        dict_values['S5 Energy Process'],dict_values['S5 Energy Process km'],dict_values['S5 Energy OM'],
                                        dict_values['S5 Energy OM km'],dict_values['S5 H2 Emissions'],dict_values['S5 H2 Emissions km'])
    
    else:
        instance.energysource.sobol_update(dict_values['S0 Emissions (gCO2e/kWh)'],dict_values['S0 Utilisation Factor'])
        instance.tinfra[0].sobol_update(dict_values['S1 Yield'],dict_values['S1 Capacity Factor'],dict_values['S1 Loss km'],dict_values['S1 Lifetime'],
                                        dict_values['S1 Speed'],dict_values['S1 Emissions Embodied'],dict_values['S1 Emissions Embodied km'],
                                        dict_values['S1 Emissions Process'],dict_values['S1 Emissions Process km'],dict_values['S1 Emissions OM'],
                                        dict_values['S1 Emissions OM km'],dict_values['S1 Energy Embodied'],dict_values['S1 Energy Embodied km'],
                                        dict_values['S1 Energy Process'],dict_values['S1 Energy Process km'],dict_values['S1 Energy OM'],
                                        dict_values['S1 Energy OM km'],dict_values['S1 H2 Emissions'],dict_values['S1 H2 Emissions km'])
        instance.productionmeth.sobol_update(dict_values['S2 Yield'],dict_values['S2 Capacity Factor'],dict_values['S2 Lifetime'],
                                            dict_values['S2 Emissions Embodied'],dict_values['S2 Emissions Process'],dict_values['S2 Emissions OM'],
                                            dict_values['S2 Energy Embodied'],dict_values['S2 Energy Process'],dict_values['S2 Energy OM'],
                                            dict_values['S2 H2 Emissions'])
        instance.conversions[0].sobol_update(dict_values['S3 Yield'],dict_values['S3 Capacity Factor'],dict_values['S3 Lifetime'],
                                            dict_values['S3 Emissions Embodied'],dict_values['S3 Emissions Process'],dict_values['S3 Emissions OM'],
                                            dict_values['S3 Energy Embodied'],dict_values['S3 Energy Process'],dict_values['S3 Energy OM'],
                                            dict_values['S3 H2 Emissions'])
        instance.tinfra[1].sobol_update(dict_values['S4 Yield'],dict_values['S4 Capacity Factor'],dict_values['S4 Loss km'],dict_values['S4 Lifetime'],
                                        dict_values['S4 Speed'],dict_values['S4 Emissions Embodied'],dict_values['S4 Emissions Embodied km'],
                                        dict_values['S4 Emissions Process'],dict_values['S4 Emissions Process km'],dict_values['S4 Emissions OM'],
                                        dict_values['S4 Emissions OM km'],dict_values['S4 Energy Embodied'],dict_values['S4 Energy Embodied km'],
                                        dict_values['S4 Energy Process'],dict_values['S4 Energy Process km'],dict_values['S4 Energy OM'],
                                        dict_values['S4 Energy OM km'],dict_values['S4 H2 Emissions'],dict_values['S4 H2 Emissions km'])
        


        instance.conversions[1].sobol_update(dict_values['S5 Yield'],dict_values['S5 Capacity Factor'],dict_values['S5 Lifetime'],
                                            dict_values['S5 Emissions Embodied'],dict_values['S5 Emissions Process'],dict_values['S5 Emissions OM'],
                                            dict_values['S5 Energy Embodied'],dict_values['S5 Energy Process'],dict_values['S5 Energy OM'],
                                            dict_values['S5 H2 Emissions'])

        
        instance.storage_method[0].sobol_update(dict_values['S6 Yield'],dict_values['S6 Capacity Factor'],dict_values['S6 Loss day'],dict_values['S6 Lifetime'],
                                                dict_values['S6 Emissions Embodied'],dict_values['S6 Emissions Process'], dict_values['S6 Emissions OM'],
                                                dict_values['S6 Energy Embodied'],dict_values['S6 Energy Process'],dict_values['S6 Energy OM'],
                                                dict_values['S6 H2 Emissions'])

        instance.tinfra[2].sobol_update(dict_values['S7 Yield'],dict_values['S7 Capacity Factor'],dict_values['S7 Loss km'],dict_values['S7 Lifetime'],
                                        dict_values['S7 Speed'],dict_values['S7 Emissions Embodied'],dict_values['S7 Emissions Embodied km'],
                                        dict_values['S7 Emissions Process'],dict_values['S7 Emissions Process km'],dict_values['S7 Emissions OM'],
                                        dict_values['S7 Emissions OM km'],dict_values['S7 Energy Embodied'],dict_values['S7 Energy Embodied km'],
                                        dict_values['S7 Energy Process'],dict_values['S7 Energy Process km'],dict_values['S7 Energy OM'],
                                        dict_values['S7 Energy OM km'],dict_values['S7 H2 Emissions'],dict_values['S7 H2 Emissions km'])
        instance.conversions[2].sobol_update(dict_values['S8 Yield'],dict_values['S8 Capacity Factor'],dict_values['S8 Lifetime'],
                                            dict_values['S8 Emissions Embodied'],dict_values['S8 Emissions Process'],dict_values['S8 Emissions OM'],
                                            dict_values['S8 Energy Embodied'],dict_values['S8 Energy Process'],dict_values['S8 Energy OM'],
                                            dict_values['S8 H2 Emissions'])
        instance.storage_method[1].sobol_update(dict_values['S9 Yield'],dict_values['S9 Capacity Factor'],dict_values['S9 Loss day'],dict_values['S9 Lifetime'],
                                                dict_values['S9 Emissions Embodied'],dict_values['S9 Emissions Process'], dict_values['S9 Emissions OM'],
                                                dict_values['S9 Energy Embodied'],dict_values['S9 Energy Process'],dict_values['S9 Energy OM'],
                                                dict_values['S9 H2 Emissions'])
        instance.tinfra[3].sobol_update(dict_values['S10 Yield'],dict_values['S10 Capacity Factor'],dict_values['S10 Loss km'],dict_values['S10 Lifetime'],
                                        dict_values['S10 Speed'],dict_values['S10 Emissions Embodied'],dict_values['S10 Emissions Embodied km'],
                                        dict_values['S10 Emissions Process'],dict_values['S10 Emissions Process km'],dict_values['S10 Emissions OM'],
                                        dict_values['S10 Emissions OM km'],dict_values['S10 Energy Embodied'],dict_values['S10 Energy Embodied km'],
                                        dict_values['S10 Energy Process'],dict_values['S10 Energy Process km'],dict_values['S10 Energy OM'],
                                        dict_values['S10 Energy OM km'],dict_values['S10 H2 Emissions'],dict_values['S10 H2 Emissions km'])
        
        #try to make it worksss
        {'S0':instance.energysource,
                    'S1':instance.tinfra[0],
                    'S2':instance.productionmeth,
                    'S3':instance.conversions[0],
                    'S4':instance.tinfra[1],
                    'S5':instance.conversions[1],
                    'S6':instance.storage_method[0],
                    'S7':instance.tinfra[2],
                    'S8':instance.conversions[2],
                    'S9':instance.storage_method[1],
                    'S10':instance.tinfra[3]}
        
    #run the model#
    emissions = instance.sobol()
    return emissions

#wrap the function to be used in sobol analysis
def wrapped_problem(X,func=func):
    N, D = X.shape
    results = np.empty(N)
    for i in range(N):
        samplevalues = X[i, :]
        #func defined in sobol_def, creates pathway selected for the iteration and returns CO2e or Energy depending on variable chosen
        results[i] = func(samplevalues,names,supplychain)
    return results


print(len(H2_supply_chain.instances))
num=0
dfs_sobol=[]
dict_num={}
for supplychain in H2_supply_chain.instances.values():
    values, names  = getvalues(supplychain)
    values, names = processvalues(values,names)
    groupnames = []
    dict_num[num] = supplychain.productionmeth.ID+supplychain.pathwaydefinition[0].origin.country
    
    for name in names:
        stage = name.split(" ")[0]
        groupnames.append(stage)
    sp = ProblemSpec({
    'groups': groupnames,
    'names': names,
    'num_vars': len(values),
    'bounds': values 
    })
    
    num+=1
    
    (
    sp.sample_sobol(2**10,calc_second_order=False)
    .evaluate(wrapped_problem)
    .analyze_sobol(calc_second_order=False)
    )
    
    total_Si, first_Si = sp.to_df()
    sobol_results = total_Si.rename(columns={'ST':num})
    print(num)
    sobol_results.drop(['ST_conf'],axis=1,inplace=True)
    sobol_results = sobol_results.T
    dfs_sobol.append(sobol_results)

combined_sobol_df = pd.concat(dfs_sobol,axis=0, ignore_index=True)   
print(combined_sobol_df)
savepickle(combined_sobol_df,'Dataframes_Sobol_offshore_CO2e1.xz','Pickle')
combined_sobol_df.to_csv('combined sobol CO2e1.csv')


#dictionary to df
df = pd.DataFrame.from_dict(dict_num,orient='index')
df.to_csv('dict_num.csv')

