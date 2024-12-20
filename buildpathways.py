from import_data import *
from geopy import Nominatim
from datetime import datetime
import io
import lzma

startTime = datetime.now()
current_date = datetime.now().strftime("%d%m%y")

"""Function to load pickle data"""
def loadpickle(name,folder='Pickle Files'):   
    with lzma.open(os.getcwd()+'\\'+folder+'\\'+name,'rb') as inp:
        return pickle.load(inp)

"""Function to create folder if doesn't exist"""   
def create_folder(path):
    if os.path.exists(path):
        pass
    else:
        os.mkdir(path)   

"""Function to save pickle data"""    
def savepickle(list1,filename,folder='Pickle Files'):
    path = os.getcwd()
    create_folder(path)
    with lzma.open(path+'\\'+folder+'\\'+filename,'wb') as outp:
        pickle.dump(list1,outp,-1)

"""Create the possible transmission pathways from production to end_use"""
def create_options(transmissionpaths=False,country = ['UK'],filename = 'Supplychains'+current_date+'.xz'):
    #add location options and make transmission pathways if required
    if transmissionpaths == False:
        transmissionpaths = createalltrans_stages(locations_df,locations.instances,country)
        savepickle(transmissionpaths,'TransmissionPaths'+current_date+'.xz','Pickle')
        transmissionpaths = loadpickle('TransmissionPaths'+current_date+'.xz','Pickle')
    supplychains = connect_transpaths_to_supplychain(transmissionpaths)
    supplywithtransinfra = add_transinfra_andprodmethod_to_supplychain(supplychains,transmissioninfra_df,Transmission_infra.instances,storage_df)
    completesupplychain = add_energysources_to_supplychain(supplywithtransinfra,energysources_df)
    savepickle(completesupplychain,filename,'Pickle')

    return completesupplychain

"""Add the variables using Monte Carlo method"""
def montecarlo(num):
    for y in range(num):
        for instance in H2_production.instances.values():
            instance.add_variables(production_df)
        for instance in Transmission_infra.instances.values():
            instance.add_variables(transmissioninfra_df)
        for instance in conversions.instances.values():
            instance.add_variables(conversions_df)
        for instance in energysources.instances.values():
            instance.add_variables(energysources_df)
        for instance in storage.instances.values():
            instance.add_variables(storage_df)
        for x in H2_supply_chain.instances.values():
            x.calc_values(y)
        print(y)
    print(len(results.instances))
    
    results_instances = results.instances
    d=[]
    for result in results_instances:
        if results_instances[result].use_impacts['Emissions']['Total'] >300:
            print(results_instances[result].emissions_by_stage)
        if results_instances[result].use != 'LH2':
            if results_instances[result].pathwaydefinition[0].origin.ID in ('EN_OFWUK','EN_NGUK','EN_WUK'):
                Tvector= 'Domestic'
            else:
                Tvector = results_instances[result].vectors[2]
            dict= {'Origin':results_instances[result].pathwaydefinition[0].origin.ID,
                'Pathwaynum':results_instances[result].pathwaynum,
                'Production Method':results_instances[result].productionmeth.ID,
                'Energy Source':results_instances[result].energysource.ID,
                'Use':results_instances[result].use,
                'stage emissions':results_instances[result].emissions_total['Total'],
                'stage energy':results_instances[result].energy_total['Total'],
                #'stage emissions split':[results_instances[result].emissions_by_stage[x] for x in results_instances[result].emissions_by_stage],
                'Use Emissions':results_instances[result].use_impacts['Emissions']['Total'],
                'Use Energy':results_instances[result].use_impacts['Energy']['Total'],
                'Use Energy ES':results_instances[result].use_impacts['Energy ES Total'],
                #'Emissions Factor':results_instances[result].emissionsfactor,
                'T Vector':Tvector,
                'vectors':results_instances[result].vectors}
                #'pathway':results_instances[result].pathwaydefinition}
            d.append(dict)
    end_uses_dataframe = pd.DataFrame(d)

    print(end_uses_dataframe['stage emissions'].max())
    print(end_uses_dataframe['stage emissions'].std())
    print(end_uses_dataframe['stage emissions'].mean())
    print(end_uses_dataframe['stage emissions'].min())
    print(end_uses_dataframe['stage energy'].quantile(0.95))
    print(end_uses_dataframe['stage energy'].quantile(0.05))

    print(datetime.now() - startTime)
    savepickle(end_uses_dataframe,'End_uses_dataframe_final2.xz','Pickle')

"""Set up variables"""
geolocator = Nominatim(user_agent='HydrogenPathways_13')
with open('Data\\Updated_Inputs.xlsx', "rb") as f:
    file_io_obj = io.BytesIO(f.read())

"""Import raw data from excel to dataframes"""
conversions_df = pd.read_excel(file_io_obj,'Conversions')
transmissioninfra_df = pd.read_excel(file_io_obj,'TransmissionInfra')
locations_df = pd.read_excel(file_io_obj,'Locations')     
production_df = pd.read_excel(file_io_obj,'ProductionMethods')
energysources_df = pd.read_excel(file_io_obj,'EnergySources')
uses_df = pd.read_excel(file_io_obj,'Uses')
storage_df = pd.read_excel(file_io_obj,'Storage')

"""Create instances of classes - locations added if needed"""
add_storage(storage_df)
print('Storage added')
add_locations(locations_df)
print('Locations added')
add_energysources(energysources_df)
print('Energy sources added')
add_conversions(conversions_df)
print('Conversions added')
add_production(production_df)
print('Production added')
add_transinfra(transmissioninfra_df)
print('Transmission infra added')
add_uses(uses_df)
print('Uses added')

create_options()
montecarlo(500)

