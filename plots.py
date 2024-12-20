import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import pickle
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import numpy as np
import lzma
from datetime import datetime
import matplotlib.ticker as ticker

cwd = os.getcwd()
#open data file
with open('Data\\Updated_Inputs.xlsx', "rb") as f:
    file_io_obj = io.BytesIO(f.read())


"""Function to save pickle data"""    
def savepickle(list1,filename,folder='Pickle Files'):
    path = os.getcwd()
    with lzma.open(path+'\\'+folder+'\\'+filename,'wb') as outp:
        pickle.dump(list1,outp,-1)

colordict = {'UK':'#fb8072',
                 'Australia':'#8dd3c7',
                 'Brazil':'#ffffb3',
                 'Kazakhstan':'#80b1d3',
                 'USA':'#b3de69',
                 'Egypt':'#bebada',
                 'Mauritania':'#fdb462',
                 'Spain':'#fccde5'}

def loadmcdata(name,folder):   
    with lzma.open(os.getcwd()+'\\'+folder+'\\'+name,'rb') as inp:
        return pickle.load(inp)
    
#create uses_df
uses_df = pd.read_excel(file_io_obj,sheet_name='Uses')
locations_df = pd.read_excel(file_io_obj,sheet_name='Locations')
    
#create columns needed in uses_df
uses_df['Emissions assuming electrification'] = float(0)
for index,row in uses_df.iterrows():
    if row['Electrification Emissions (kgCO2e/unit)'] == 0:
        uses_df.loc[index,'Emissions assuming electrification'] = float(row['Base emissions (kgCO2e/unit)'])
        uses_df.loc[index,'Emissions assuming electrification 2'] = float(row['Base emissions (kgCO2e/unit)'])
    else:
        uses_df.loc[index,'Emissions assuming electrification'] = row['Electrification Emissions (kgCO2e/unit)']
        uses_df.loc[index,'Emissions assuming electrification 2'] = row['Electrification Emissions 2 (kgCO2e/unit)']

uses_df['Total_emissions_baseline'] = uses_df['Demand (Unit/Year)']*uses_df['Base emissions (kgCO2e/unit)']
uses_df['Total_emissions_electrification'] = uses_df['Demand (Unit/Year)']*uses_df['Emissions assuming electrification']
uses_df['Total_emissions_electrification2'] = uses_df['Demand (Unit/Year)']*uses_df['Emissions assuming electrification 2']

total_emissions_baseline = uses_df['Total_emissions_baseline'].sum()
total_emissions_electrification = uses_df['Total_emissions_electrification'].sum()
total_emissions_electrification2 = uses_df['Total_emissions_electrification2'].sum()


def process_results(results_df,uses_df):
    #process the results and create extra columns required for the plots

    #create columns needed in results df
    results_df['Country'] = results_df['Origin'].map(dict(locations_df[['ID', 'Country']].values))
    results_df['Pathway legend'] = results_df['Pathwaynum'].astype(str)+results_df['Use']
    results_df['Base Emissions'] = results_df['Use'].map(dict(uses_df[['ID', 'Base emissions (kgCO2e/unit)']].values))     
    results_df['Input (kgH2/unit)'] = results_df['Use'].map(dict(uses_df[['ID', 'Input (kgH2e/unit)']].values))
    results_df['Electrification Emissions'] = results_df['Use'].map(dict(uses_df[['ID','Emissions assuming electrification']].values))
    results_df['Electrification Emissions 2'] = results_df['Use'].map(dict(uses_df[['ID','Emissions assuming electrification 2']].values))
    results_df['Use Demand (Unit/yr)'] = results_df['Use'].map(dict(uses_df[['ID', 'Demand (Unit/Year)']].values))
    results_df['Min value'] = results_df['Use'].map(dict(uses_df[['ID','Min Hydrogen (kg/yr)']]))
    results_df['Total Demand (kgH2/yr)'] = results_df['Use Demand (Unit/yr)']*results_df['Input (kgH2/unit)']
    results_df['Emissions reduction baseline'] = (results_df['Base Emissions'] - results_df['Use Emissions'])/results_df['Input (kgH2/unit)']
    for index,row in results_df.iterrows():
        if row['Emissions reduction baseline'] < -310:
            print(row['Country'],row['Use'],row['Input (kgH2/unit)'],row['Use Emissions'],row['Base Emissions'])
            exit()
    results_df['Emissions reduction electrification'] = (results_df['Electrification Emissions'] - results_df['Use Emissions'])/results_df['Input (kgH2/unit)']
    results_df['Emissions reduction electrification 2'] = (results_df['Electrification Emissions 2'] - results_df['Use Emissions'])/results_df['Input (kgH2/unit)']

    return results_df

def filter_results(results_df,production_method=['CPL'],pathway_var='min'):
    #filter the results based on inputted variables
    dfs = []
    print(production_method)
    print(results_df)
    results_df = results_df[results_df['Production Method'].isin(production_method)].copy()
    for name,group in results_df.groupby(['Country','Use']):
        x = int(len(group)/2)
        group = group.sort_values('Use Emissions')
        if pathway_var == 'min':
                emissions = group['Use Emissions'].min()
        elif pathway_var == 'max':
            emissions = group['Use Emissions'].max()
        elif pathway_var == 'average':
            emissions = group.iloc[x]['Use Emissions']
        #need to idenitfy by pathway number and use as otherwise not unique
        pathway = group[group['Use Emissions'] == emissions].iloc[0]['Pathwaynum'].astype(str)
        use = group[group['Use Emissions'] == emissions].iloc[0]['Use']
        dfs.append(group[group['Pathway Legend']==pathway+use])

    concatresults = pd.concat(dfs)
    #print(len(concatresults))
    #print(concatresults.loc[concatresults['Country']=='Australia']['Pathway legend'])

    return concatresults

def fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'average','num':10,'baseline':'base','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'}):
    
    #define column value and base emissions depending on baseline
    if plotvars['baseline'] == 'base':
        emissionscolumn = 'Emissions reduction baseline'
        baselineemissions = total_emissions_baseline
    elif plotvars['baseline'] == 'electrification':
        emissionscolumn = 'Emissions reduction electrification'
        baselineemissions = total_emissions_electrification
    elif plotvars['baseline'] == 'electrification2':
        emissionscolumn = 'Emissions reduction electrification 2'
        baselineemissions = total_emissions_electrification2

    #Create a new DataFrame supply df to hold data for the plots
    supply_df = pd.DataFrame()

    #define plot limit from plotvars
    if plotvars['plotlim'] == 'Total Demand':
        total_demand = uses_df['Total Demand (kgH2/yr)'].sum()
    else:
        total_demand = plotvars['plotlim']

    #create rows in dataframe to define the supply at each scenario point
    H2_perdivision = (total_demand)/(plotvars['num'])
    supply_df['Supply (kgH2/yr)'] = float(0)
    for num in range(plotvars['num']+1):
        supply_df.loc[num,'Supply (kgH2/yr)'] = float(H2_perdivision*(num))
    
    #add columns to supply_df for each unique ID from uses_df,save in variable for use later
    usecolumns=uses_df['ID'].unique()
    print(usecolumns)
    for ID in usecolumns:
        supply_df[ID] = float(0)
        
    #add column total emissions reduction to supply_df, start at the total emissions baseline
    supply_df['Total Emissions Reduction (kgCO2e/yr)'] = float(baselineemissions)

    #filter the results for plot
    results_df_filtered = filter_results(results_df,plotvars['production_method'],plotvars['pathway_var'])

    #create empty dictionaries to hold results for plots in
    finalresults= {}

    for name,group in results_df_filtered.groupby('Country'):
        supply_df2=supply_df.copy()
        print(group[['Country','Use']])
        dict_uses = {}
        #find order of uses
        for name2,group2 in group.groupby('Use'):
            if plotvars['MC_variable'] == 'average':
                value = group2[emissionscolumn].mean()
            elif plotvars['MC_variable'] == 'min':
                value = group2[emissionscolumn].min()
            elif plotvars['MC_variable'] == 'max':
                value = group2[emissionscolumn].max()
            dict_uses[name2]=value

        #create sorted tuple of uses and values    
        orderandvalue = sorted(dict_uses.items(),key=lambda x:x[1],reverse = True)

        #save to final results dict
        finalresults[name] = {'Order':orderandvalue}
        
        #iterate through supply scenarios
        for index,row in supply_df2.iterrows():
            supply = row['Supply (kgH2/yr)']
            for use,value in orderandvalue:
                if supply > 0 and supply > uses_df[uses_df['ID']==use]['Min Hydrogen (kg/yr)'].iloc[0]:
                    rowresults = group.loc[group['Use']==use].iloc[0]
                    usedh2 = min(supply,rowresults['Total Demand (kgH2/yr)'])
                    supply = supply - usedh2
                    supply_df2.loc[index,use] = usedh2
                else:
                    break
        
        #calculate the total emissions reduction for each supply scenario
        for index,row in supply_df2.iterrows():
            total = 0
            for column in usecolumns:
                total = total + row[column]*dict_uses[column]
            supply_df2.loc[index,'Total Emissions Reduction (kgCO2e/yr)'] = baselineemissions - total
        finalresults[name]['DF'] = supply_df2

    return finalresults

def plot_fig4(results,barplotdf=pd.DataFrame([]),filename='fig4.svg'):
    #define country colours dict, second one is a darker shade to distinguish between two sections
    countries = results_df['Country'].unique()
    colordict = {'UK':'#fb8072',
                'Australia':'#8dd3c7',
                'Brazil':'#ffffb3',
                'Kazakhstan':'#80b1d3',
                'USA':'#b3de69',
                'Egypt':'#bebada',
                'Mauritania':'#fdb462',
                'Spain':'#fccde5'}
    
    #define plots
    fig, ax = plt.subplots()


    #results is a list of dictionaries, each dictionary contains a different set of information to be plotted
    n1=2
    n2=3
    uklims = []
    handle_list, label_list = [], []   

    #plot uk baselines
    for result in [results[0],results[1]]:
        mean_df = result['line']['UK']['DF']
        x = mean_df['Supply (kgH2/yr)']
        yav = mean_df['Total Emissions Reduction (kgCO2e/yr)']
        ax.plot(x,yav,label='UK',color='black',zorder=n2,linewidth=2.0,linestyle='--')
        uklims.append(yav)


    #plot other results
    for result_dict in [results[2],results[3]]:   
        
        countries = result_dict['low'].keys() 
        for country in ['USA','Australia','Brazil','Kazakhstan','Egypt','Mauritania','Spain','UK']:
            if country in countries:
                low_df = result_dict['low'][country]['DF']
                high_df = result_dict['high'][country]['DF']
                mean_df = result_dict['line'][country]['DF']
                x = low_df['Supply (kgH2/yr)']
                ymin=low_df['Total Emissions Reduction (kgCO2e/yr)']
                ymax=high_df['Total Emissions Reduction (kgCO2e/yr)']
                yav = mean_df['Total Emissions Reduction (kgCO2e/yr)']
                if country == 'UK': 
                    uklims.append(ymin)
                ax.fill_between(x,ymin,ymax,color=colordict[country],alpha=0.7,zorder=n1,linewidth=0.0)
                ax.plot(x,yav,label=country,color=colordict[country],zorder=n2)
                handles, labels = ax.get_legend_handles_labels()
                for handle, label in zip(handles, labels):
                    if label not in label_list:
                        handle_list.append(handle)
                        label_list.append(label)
        n1+=1
        n2=n1+1

    ax.fill_between(x,0,uklims[3],color='#636363',alpha=1,zorder=0)
    ax.fill_between(x,uklims[3],uklims[2],color='#487db5',alpha=0.3,zorder=1,hatch='...')
    ax.legend(handle_list, label_list,ncols=2)

    #change axis ticks to show in megatonnes
    scale_x = 1e9
    scale_y = 1e9
    ticks_x = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/scale_x))
    ax.xaxis.set_major_formatter(ticks_x)

    ticks_y = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/scale_y))
    ax.yaxis.set_major_formatter(ticks_y)

    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0,top=2000*scale_y)
    ax.set_xlabel('Hydrogen Supply (MtH2/yr)')
    ax.set_ylabel('Total Emissions (MtCO2e/yr)')

    plt.savefig(filename,dpi=600)

def plot_fig3A(results,barplotdf=pd.DataFrame([])):
    #define country colours dict, second one is a darker shade to distinguish between two sections
    countries = results_df['Country'].unique()
    colordict = {'UK':'#fb8072',
                 'Australia':'#8dd3c7',
                 'Brazil':'#ffffb3',
                 'Kazakhstan':'#80b1d3',
                 'USA':'#b3de69',
                 'Egypt':'#bebada',
                 'Mauritania':'#fdb462',
                 'Spain':'#fccde5'}

    #summary of values
    print('UK Min:',results[0]['low']['UK']['DF']['Total Emissions Reduction (kgCO2e/yr)'].min())
    print('UK Max:',results[0]['low']['UK']['DF']['Total Emissions Reduction (kgCO2e/yr)'].max())
    print('UK Max uncertaointy:',results[0]['high']['UK']['DF']['Total Emissions Reduction (kgCO2e/yr)'].min())
    print('UK Min Eelctrification:',results[1]['high']['UK']['DF']['Total Emissions Reduction (kgCO2e/yr)'].min())
    print('Spain Min:',results[0]['high']['Spain']['DF']['Total Emissions Reduction (kgCO2e/yr)'].min())
    print('Kazakhstan:',results[0]['low']['Kazakhstan']['DF']['Total Emissions Reduction (kgCO2e/yr)'])

    
    #define plots
    fig, [[ax1, ax2],[ax3, ax4],[ax5,ax6]] = plt.subplots(3,2,width_ratios=[6,1],height_ratios=[4,1,1],figsize=(10,10))
    plt.subplots_adjust(hspace = 0.01)
   
    #results is a list of dictionaries, each dictionary contains a different set of information to be plotted
    n1=0
    n2=1
    uklims = []
    uklims_min = []
    othermin = []
    handle_list, label_list = [], []   
    hatch = ['...',None,'x','o','O','+','*','|'] 
    for result_dict,hatchnum in zip([results[0],results[1]],hatch):   
        print(hatchnum)
        countries = result_dict['low'].keys() 
        for country in countries:
            low_df = result_dict['low'][country]['DF']
            high_df = result_dict['high'][country]['DF']
            mean_df = result_dict['line'][country]['DF']
            x = low_df['Supply (kgH2/yr)']
            ymin=low_df['Total Emissions Reduction (kgCO2e/yr)']
            ymax=high_df['Total Emissions Reduction (kgCO2e/yr)']
            yav = mean_df['Total Emissions Reduction (kgCO2e/yr)']
            if country == 'UK': 
                uklims.append(ymax)
            ax1.fill_between(x,ymin,ymax,color=colordict[country],alpha=0.5,zorder=n1,linewidth=0.0)
            #add hatching
            ax1.fill_between(x,ymin,ymax, color='none', edgecolor='grey',alpha=0.5,zorder=n1,linewidth=0.0,hatch=hatchnum)
            ax1.plot(x,yav,label=country,color=colordict[country],zorder=n2)
            handles, labels = ax1.get_legend_handles_labels()
            for handle, label in zip(handles, labels):
                if label not in label_list:
                    handle_list.append(handle)
                    label_list.append(label)
        n1+=1
        n2=n1+1

    
    ax1.fill_between(x,0,uklims[1],color='#101E33',alpha=0.5,zorder=0,edgecolor=None)
    ax1.fill_between(x,uklims[0],uklims[1],color='#4E607A',alpha=0.5,zorder=0,hatch='...')
    #ax1.fill_between(x,uklims[2],uklims[1],color='#263750',alpha=0.5,zorder=0,hatch='...')

    #plot bar chart (b)
    if len(barplotdf) == 0:
        ax2.remove()
    else:
        for country in ['USA','Australia','Brazil','Kazakhstan','Egypt','Mauritania','Spain','UK']:
            ax2.bar(barplotdf.loc[barplotdf['Country']==country]['Name'],barplotdf.loc[barplotdf['Country']==country]['Total'],color=colordict[country],alpha=0.7)

        bars = ax2.patches
        # set hatch patterns in the correct order
        patterns = ['...',None,'...',None,'...',None,'...',None,'...',None,'...',None,'...',None,'...',None] 
        hatches = []  # list for hatches in the order of the bars
        for h in patterns:  # loop over patterns to create bar-ordered hatches
            for i in range(int(len(bars) / len(patterns))):
                hatches.append(h)
        for bar, hatch in zip(bars, hatches):  # loop over bars and hatches to set hatches in correct order
            bar.set_edgecolor('grey')
            bar.set_hatch(hatch)
        ax2.axhline(0.267, color='grey', linewidth=1,linestyle='--')
        ax2.set_ylabel('Energy Required for Hydrogen Production (PWh/yr)')
        ax2.set_title('') 
        ax2.set_xlabel('')
        ax2.set_xticks(ax2.get_xticks())
        ax2.set_xticklabels(['Base','Electrification'],rotation=90)

    #change axis ticks to show in megatonnes
    scale_x = 1e9
    scale_y = 1e9
    ticks_x = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/scale_x))
    ax1.xaxis.set_major_formatter(ticks_x)

    ticks_y = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/scale_y))
    ax1.yaxis.set_major_formatter(ticks_y)

    ax1.set_xlim(left=0)
    ax1.set_ylim(bottom=0)
    ax1.set_xlabel('')
    ax1.set_ylabel('Total Emissions (MtCO2e/yr)')
    ax1.legend(handle_list, label_list,ncols=2) 

    #plot c and d

    combined_df_base = results[0]['line']
    combined_df_electrification = results[1]['line']

    colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', 
        '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080']
    colordict={}
    
    for country,colour in zip(uses_df.ID.unique(),colors):
            colordict[country] = colour

    handles2,labels2 = [],[]
    for item,ax,hatch in zip([combined_df_base, combined_df_electrification],[ax3,ax5],['...',None]):
        order = item['UK']['Order']
        values = item['UK']['DF']

        #print(values.loc[-1].columns())
        startwidth=0
        minuse=0
        for use in order:
            width = values.iloc[-1][use[0]]
            ax.fill_betweenx([0,use[1]],startwidth,startwidth+width,alpha=0.5,color=colordict[use[0]],hatch=hatch,label=use[0])
            if use[1] < minuse:
                minuse = use[1]
            startwidth += width
            if use[1] > 0:
                demand = startwidth
        print('total demand',demand) 

        #change axis ticks to show in megatonnes
        scale_x = 1e9
        scale_y = 1e9
        ticks_x = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/scale_x))
        ax.xaxis.set_major_formatter(ticks_x)

        ax.set_xlim(left=0)
        ax.set_ylim(top=30)
        ax.spines['bottom'].set_position(('data', 0))
        ax.set_xlabel('Hydrogen Supply (MtH2/yr)')
    
    #get handles and labels for legend
    handles, labels = ax5.get_legend_handles_labels()

    #change labels to make them more readable
    newlabels = {'Fertiliser-AmmoniumNitrate':'Nitrate Fertiliser',
                 'Fertiliser-Phosphate':'Phosphate Fertiliser',
                 'Hydrogenation':'Replacing Grey Hydrogen in Refineries',
                 'IronandSteel':'Steel Production',
                 'Methanol':'Methanol Production',
                 'JetAviation':'Aviation',
                 'HighTemperatureHeat':'High Temperature Heat',
                 'Longdistancetrucksandcoaches':'Trucks and Coaches',
                 'Longdurationgridbalancing':'Grid Balancing',
                 'Biogasupgrading':'Biogas Upgrading',
                 'Non-RoadMobileMachinery':'Non-Road Mobile Machinery',
                 '2and3wheelers':'Motorcycles',
                 'MetroTrainsandBuses':'Buses',
                 'RemoteandRuralTrains':'Trains',
                 'LightTrucks':'Vans',
                 'Cars':'Cars',
                 'CommercialHeating':'Commercial Heating',
                 'Domesticheating':'Domestic Heating',
                 'Mid/LowTemperatureHeat':'Mid/Low Temperature Heat',
                 'Shipping-Ammonia':'Shipping (Ammonia)',
                }

    labels = [newlabels[label] for label in labels]
    #ax5.legend(handles,labels,bbox_to_anchor=(1.4,0.8),ncol=3)
    #ax5.set_ylabel('Emissions Reduction\nPotential (kgCO2e/kgH2)')
    ax4.remove()
    ax6.remove()

    for ax in [ax1,ax2,ax3,ax5]:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    ax5.set_ylabel('')
    ax3.set_xlabel('')
    
    #plt.tight_layout()
    #plt.subplots_adjust(height_ratios=[4,1,1,1])
    plt.savefig('fig3.svg',dpi=600)
    plt.show()

def plot_fig3A_SI(results,barplotdf=pd.DataFrame([])):
    #define country colours dict, second one is a darker shade to distinguish between two sections
    countries = results_df['Country'].unique()
    colordict = {'UK':'#fb8072',
                 'Australia':'#8dd3c7',
                 'Brazil':'#ffffb3',
                 'Kazakhstan':'#80b1d3',
                 'USA':'#b3de69',
                 'Egypt':'#bebada',
                 'Mauritania':'#fdb462',
                 'Spain':'#fccde5'}

    
    #define plots
    fig, [[ax1, ax2],[ax3, ax4],[ax5,ax6],[ax7,ax8]] = plt.subplots(4,2,width_ratios=[6,1],height_ratios=[4,1,1,1],figsize=(11,9))
    plt.subplots_adjust(hspace = 0.01)
   

    #results is a list of dictionaries, each dictionary contains a different set of information to be plotted
    n1=0
    n2=1
    uklims = []
    uklims_min = []
    othermin = []
    handle_list, label_list = [], []   
    hatch = ['/','...',None,'x','o','O','+','*','|'] 
    for result_dict,hatchnum in zip([results[0],results[2],results[1]],hatch):   
        print(hatchnum)
        countries = result_dict['low'].keys() 
        for country in countries:
            low_df = result_dict['low'][country]['DF']
            high_df = result_dict['high'][country]['DF']
            mean_df = result_dict['line'][country]['DF']
            x = low_df['Supply (kgH2/yr)']
            ymin=low_df['Total Emissions Reduction (kgCO2e/yr)']
            ymax=high_df['Total Emissions Reduction (kgCO2e/yr)']
            yav = mean_df['Total Emissions Reduction (kgCO2e/yr)']
            if country == 'UK': 
                uklims.append(ymax)
            ax1.fill_between(x,ymin,ymax,color=colordict[country],alpha=0.5,zorder=n1,linewidth=0.0)
            #add hatching
            ax1.fill_between(x,ymin,ymax, color='none', edgecolor='grey',alpha=0.5,zorder=n1,linewidth=0.0,hatch=hatchnum)
            ax1.plot(x,yav,label=country,color=colordict[country],zorder=n2)
            handles, labels = ax1.get_legend_handles_labels()
            for handle, label in zip(handles, labels):
                if label not in label_list:
                    handle_list.append(handle)
                    label_list.append(label)
        n1+=1
        n2=n1+1

    
    ax1.fill_between(x,0,uklims[2],color='#101E33',alpha=0.5,zorder=0,edgecolor=None)
    ax1.fill_between(x,uklims[0],uklims[1],color='#4E607A',alpha=0.5,zorder=0,hatch='/')
    ax1.fill_between(x,uklims[2],uklims[1],color='#263750',alpha=0.5,zorder=0,hatch='...')

    #plot bar chart (b)
    if len(barplotdf) == 0:
        ax2.remove()
    else:
        #sns.barplot(ax=ax2,data=barplotdf,hue='Name',y='Total',palette=['#80b1d3','#bebada'])
        for country in ['USA','Australia','Brazil','Kazakhstan','Egypt','Mauritania','Spain','UK']:
            ax2.bar(barplotdf.loc[barplotdf['Country']==country]['Name'],barplotdf.loc[barplotdf['Country']==country]['Total'],color=colordict[country],alpha=0.7)

        bars = ax2.patches
        # set hatch patterns in the correct order
        patterns = ['/','...',None,
                    '/','...',None,
                    '/','...',None,
                    '/','...',None,
                    '/','...',None,
                    '/','...',None,
                    '/','...',None,
                    '/','...']  
        hatches = []  # list for hatches in the order of the bars
        for h in patterns:  # loop over patterns to create bar-ordered hatches
            for i in range(int(len(bars) / len(patterns))):
                hatches.append(h)
        for bar, hatch in zip(bars, hatches):  # loop over bars and hatches to set hatches in correct order
            bar.set_edgecolor('grey')
            bar.set_hatch(hatch)
        ax2.axhline(0.267, color='grey', linewidth=1,linestyle='--')
        ax2.set_ylabel('Energy Required for Hydrogen Production (PWh/yr)')
        ax2.set_title('') 
        ax2.set_xlabel('')
        ax2.set_xticks(ax2.get_xticks())
        ax2.set_xticklabels(['Base','Electrified\nCurrent Grid Intensity UK','Electrified\nRenewable Power'],rotation=90)

    #change axis ticks to show in megatonnes
    scale_x = 1e9
    scale_y = 1e9
    ticks_x = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/scale_x))
    ax1.xaxis.set_major_formatter(ticks_x)

    ticks_y = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/scale_y))
    ax1.yaxis.set_major_formatter(ticks_y)

    ax1.set_xlim(left=0)
    ax1.set_ylim(bottom=0)
    ax1.set_xlabel('')
    ax1.set_ylabel('Total Emissions (MtCO2e/yr)')
    ax1.legend(handle_list, label_list,ncols=2) 

    #plot c and d

    combined_df_base = results[0]['line']
    combined_df_electrification = results[1]['line']
    combined_df_electrification2 = results[2]['line']

    colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', 
        '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080']
    colordict={}
    
    for country,colour in zip(uses_df.ID.unique(),colors):
            colordict[country] = colour

    handles2,labels2 = [],[]
    for item,ax,hatch in zip([combined_df_base,combined_df_electrification2, combined_df_electrification],[ax3,ax5,ax7],['/','...',None]):
        order = item['UK']['Order']
        values = item['UK']['DF']

        #print(values.loc[-1].columns())
        startwidth=0
        minuse=0
        for use in order:
            width = values.iloc[-1][use[0]]
            ax.fill_betweenx([0,use[1]],startwidth,startwidth+width,alpha=0.5,color=colordict[use[0]],hatch=hatch,label=use[0])
            if use[1] < minuse:
                minuse = use[1]
            startwidth += width

        #change axis ticks to show in megatonnes
        scale_x = 1e9
        scale_y = 1e9
        ticks_x = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/scale_x))
        ax.xaxis.set_major_formatter(ticks_x)

        ax.set_xlim(left=0)
        ax.set_ylim(bottom=-1,top=30)
        ax.spines['bottom'].set_position(('data', 0))
        ax.set_xlabel('Hydrogen Supply (MtH2/yr)')
    
    #get handles and labels for legend
    handles, labels = ax5.get_legend_handles_labels()

    #change labels to make them more readable
    newlabels = {'Fertiliser-AmmoniumNitrate':'Nitrate Fertiliser',
                 'Fertiliser-Phosphate':'Phosphate Fertiliser',
                 'Hydrogenation':'Replacing Grey Hydrogen in Refineries',
                 'IronandSteel':'Steel Production',
                 'Methanol':'Methanol Production',
                 'JetAviation':'Aviation',
                 'HighTemperatureHeat':'High Temperature Heat',
                 'Longdistancetrucksandcoaches':'Trucks and Coaches',
                 'Longdurationgridbalancing':'Grid Balancing',
                 'Biogasupgrading':'Biogas Upgrading',
                 'Non-RoadMobileMachinery':'Non-Road Mobile Machinery',
                 '2and3wheelers':'Motorcycles',
                 'MetroTrainsandBuses':'Buses',
                 'RemoteandRuralTrains':'Trains',
                 'LightTrucks':'Vans',
                 'Cars':'Cars',
                 'CommercialHeating':'Commercial Heating',
                 'Domesticheating':'Domestic Heating',
                 'Mid/LowTemperatureHeat':'Mid/Low Temperature Heat',
                 'Shipping-Ammonia':'Shipping (Ammonia)',
                }

    labels = [newlabels[label] for label in labels]

    ax4.remove()
    ax6.remove()
    ax8.remove()

    for ax in [ax1,ax2,ax3,ax5,ax7]:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    ax5.set_ylabel('')
    ax3.set_xlabel('')
    
    plt.savefig('fig3 SI.svg',dpi=600)
    #plt.show()

def fig3B_data(basedf,electrificationdf,results_df):
    dfs=[]

    base = basedf['UK']['DF']
    electrification = electrificationdf['UK']['DF']
    #find the maximum emissions reduction for each supply case for the UK (minimum total)
    baseminindex = base['Total Emissions Reduction (kgCO2e/yr)'].idxmin()
    elecminindex = electrification['Total Emissions Reduction (kgCO2e/yr)'].idxmin()
    
    for country in basedf.keys():

        #list of uses
        uses = results_df['Use'].unique()

        #find the pathways with the least emissions for each supply case
        results_df_pem = results_df[(results_df['Production Method'] == 'CPL')&(results_df['Country']==country)].copy()
        results_df_pem.index = range(len(results_df_pem))
        print(results_df_pem['Use Emissions'].idxmin(),len(results_df_pem))
        results_df_pem['Pathway legend'] = results_df_pem['Pathwaynum'].astype(str)+results_df_pem['Use']
        
        energy_intensity = {}
        for name,group in results_df_pem.groupby('Use'):
            pathwayindex = group['Use Emissions'].idxmin()
            pathway = results_df_pem.iloc[pathwayindex]['Pathwaynum'].astype(str)+results_df_pem.iloc[pathwayindex]['Use']
            df = results_df_pem[results_df_pem['Pathway legend'] == pathway]
            energy_intensity[name] = df['stage energy'].mean()

        value1 =[]
        value2 = []
        value3 = []
        for use in uses:
            value1.append(base.loc[baseminindex,use]*energy_intensity[use]/1e12)
            value2.append(electrification.loc[elecminindex,use]*energy_intensity[use]/1e12)
        
        #creata a dataframe with value1 and value2 as indexes and the uses as columns
        df = pd.DataFrame.from_dict({'Base':value1,'Electrification\nRenewable':value2},orient='index')
        df['Total'] = df.sum(axis=1)
        df['Name']=df.index
        df['Country'] = country
        dfs.append(df)
    df = pd.concat(dfs)
    df.to_csv('barplotdf.csv')
    return df

def fig3B_data_SI(basedf,electrificationdf,electrification2df,results_df):
    dfs=[]

    base = basedf['UK']['DF']
    electrification = electrificationdf['UK']['DF']
    electrification2 = electrification2df['UK']['DF']
    #find the maximum emissions reduction for each supply case for the UK (minimum total)
    baseminindex = base['Total Emissions Reduction (kgCO2e/yr)'].idxmin()
    elecminindex = electrification['Total Emissions Reduction (kgCO2e/yr)'].idxmin()
    elec2minindex = electrification2['Total Emissions Reduction (kgCO2e/yr)'].idxmin()
    
    for country in basedf.keys():

        #list of uses
        uses = results_df['Use'].unique()

        #find the pathways with the least emissions for each supply case
        results_df_pem = results_df[(results_df['Production Method'] == 'CPL')&(results_df['Country']==country)].copy()
        results_df_pem.index = range(len(results_df_pem))
        print(results_df_pem['Use Emissions'].idxmin(),len(results_df_pem))
        results_df_pem['Pathway legend'] = results_df_pem['Pathwaynum'].astype(str)+results_df_pem['Use']
        
        energy_intensity = {}
        for name,group in results_df_pem.groupby('Use'):
            pathwayindex = group['Use Emissions'].idxmin()
            pathway = results_df_pem.iloc[pathwayindex]['Pathwaynum'].astype(str)+results_df_pem.iloc[pathwayindex]['Use']
            df = results_df_pem[results_df_pem['Pathway legend'] == pathway]
            energy_intensity[name] = df['stage energy'].mean()

        value1 =[]
        value2 = []
        value3 = []
        for use in uses:
            value1.append(base.loc[baseminindex,use]*energy_intensity[use]/1e12)
            value2.append(electrification.loc[elecminindex,use]*energy_intensity[use]/1e12)
            value3.append(electrification2.loc[elec2minindex,use]*energy_intensity[use]/1e12)
        
        #creata a dataframe with value1 and value2 as indexes and the uses as columns
        df = pd.DataFrame.from_dict({'Base':value1,'Electrification\nGrid 2023':value3,'Electrification\nRenewable':value2},orient='index')
        df['Total'] = df.sum(axis=1)
        df['Name']=df.index
        df['Country'] = country
        dfs.append(df)
    df = pd.concat(dfs)
    df.to_csv('barplotdfSI.csv')
    return df
    
def plotfig3andfig4(num,run=True,figSI=False):
    
    if run == True:
        results_dicts_low = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'min','num':num,'baseline':'base','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        results_dicts_high = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'max','num':num,'baseline':'base','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        results_dicts_mean = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'average','num':num,'baseline':'base','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        e_results_low = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'min','num':num,'baseline':'electrification','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        e_results_high = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'max','num':num,'baseline':'electrification','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        e_results_mean = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'average','num':num,'baseline':'electrification','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        e2_results_low = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'min','num':num,'baseline':'electrification2','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        e2_results_high = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'max','num':num,'baseline':'electrification2','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        e2_results_mean = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'average','num':num,'baseline':'electrification2','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        barplotdf = fig3B_data(results_dicts_mean,e_results_mean,results_df)
        barplotdfSI = fig3B_data_SI(results_dicts_mean,e_results_mean,e2_results_mean,results_df)

        plot_inputs  = [{'low':results_dicts_low,'high':results_dicts_high,'line':results_dicts_mean},{'low':e_results_low,'high':e_results_high,'line':e_results_mean}]
        plot_inputs_SI  = [{'low':results_dicts_low,'high':results_dicts_high,'line':results_dicts_mean},{'low':e_results_low,'high':e_results_high,'line':e_results_mean},
                            {'low':e2_results_low,'high':e2_results_high,'line':e2_results_mean}]

        savepickle(plot_inputs,'fig3A.pkl','Pickle')
        savepickle(barplotdf,'barplotdf.pkl','Pickle')
        savepickle(plot_inputs_SI,'fig3A_SI.pkl','Pickle')
        savepickle(barplotdfSI,'barplotdfSI.pkl','Pickle')

    plot_inputs = loadmcdata('fig3A.pkl','Pickle')
    barplotdf = loadmcdata('barplotdf.pkl','Pickle')
    plot_inputs_SI = loadmcdata('fig3A_SI.pkl','Pickle')
    barplotdfSI = loadmcdata('barplotdfSI.pkl','Pickle')
    
    plot_fig3A(plot_inputs,barplotdf)
    plot_fig3A_SI(plot_inputs_SI,barplotdfSI)


    if figSI == True:
        results_dicts_low = fig3and4_data(uses_df,results_df[results_df['Country']=='UK'],plotvars={'MC_variable':'min','num':num,'baseline':'base','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        results_dicts_high = fig3and4_data(uses_df,results_df[results_df['Country']=='UK'],plotvars={'MC_variable':'max','num':num,'baseline':'base','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        results_dicts_mean = fig3and4_data(uses_df,results_df[results_df['Country']=='UK'],plotvars={'MC_variable':'average','num':num,'baseline':'base','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        e_results_low = fig3and4_data(uses_df,results_df[results_df['Country']=='UK'],plotvars={'MC_variable':'min','num':num,'baseline':'electrification','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        e_results_high = fig3and4_data(uses_df,results_df[results_df['Country']=='UK'],plotvars={'MC_variable':'max','num':num,'baseline':'electrification','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        e_results_mean = fig3and4_data(uses_df,results_df[results_df['Country']=='UK'],plotvars={'MC_variable':'average','num':num,'baseline':'electrification','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        

        atr_results_low = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'min','num':num,'baseline':'base','plotlim':'Total Demand','production_method':['AHL'],'pathway_var':'max'})
        atr_results_high = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'max','num':num,'baseline':'base','plotlim':'Total Demand','production_method':['AHL'],'pathway_var':'min'})
        atr_results_mean = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'average','num':num,'baseline':'base','plotlim':'Total Demand','production_method':['AHL'],'pathway_var':'min'})
        e_atr_results_low = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'min','num':num,'baseline':'electrification','plotlim':'Total Demand','production_method':['AHL'],'pathway_var':'max'})
        e_atr_results_high = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'max','num':num,'baseline':'electrification','plotlim':'Total Demand','production_method':['AHL'],'pathway_var':'min'})
        e_atr_results_mean = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'average','num':num,'baseline':'electrification','plotlim':'Total Demand','production_method':['AHL'],'pathway_var':'min'})

        plot_fig4([{'low':results_dicts_low,'high':results_dicts_high,'line':results_dicts_mean},{'low':e_results_low,'high':e_results_high,'line':e_results_mean},
                {'low':atr_results_low,'high':atr_results_high,'line':atr_results_mean},{'low':e_atr_results_low,'high':e_atr_results_high,'line':e_atr_results_mean}],filename='fig4SIATR.png')


        pem_results_low = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'min','num':num,'baseline':'base','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'max'})
        pem_results_high = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'max','num':num,'baseline':'base','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        pem_results_mean = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'average','num':num,'baseline':'base','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'max'})
        e_pem_results_low = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'min','num':num,'baseline':'electrification','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'max'})
        e_pem_results_high = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'max','num':num,'baseline':'electrification','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'min'})
        e_pem_results_mean = fig3and4_data(uses_df,results_df,plotvars={'MC_variable':'average','num':num,'baseline':'electrification','plotlim':'Total Demand','production_method':['CPL'],'pathway_var':'max'})

        plot_fig4([{'low':results_dicts_low,'high':results_dicts_high,'line':results_dicts_mean},{'low':e_results_low,'high':e_results_high,'line':e_results_mean},
                {'low':pem_results_low,'high':pem_results_high,'line':pem_results_mean},{'low':e_pem_results_low,'high':e_pem_results_high,'line':e_pem_results_mean}],filename='fig4SIPEM.png')

def plot_fig1(end_uses_df_original,vector):
    #filter the end_uses_df to only include the vector
    use = {'Hydrogenation':'CH2','Shipping-Ammonia':'NH3','Methanol':'CH3OH'}
    #flip values and keys in use dict
    use = dict((v,k) for k,v in use.items())
    basevalues = {'CH2':2.4,'NH3':2.9,'CH3OH':0.79}

    end_uses_df = end_uses_df_original[end_uses_df_original['Use'] == use[vector]].copy()
    print(end_uses_df['Use Emissions'].min(),end_uses_df['Use Emissions'].max())

    #create country column from origin value
    mapping = dict(locations_df[['ID', 'Country']].values)
    end_uses_df['Country'] = end_uses_df['Origin'].map(mapping)
    end_uses_df['Legend'] = end_uses_df['Production Method']+' - '+end_uses_df['T Vector']

    #find the minimum average emissions pathway for each country, production method and transmission vector
    avminpathways = []
    for name,group in end_uses_df.groupby(['Country','Production Method','T Vector']):
        pathway = {'Pathway Number':0,'Emissions':float(200)}
        for name2,group2 in group.groupby('Pathwaynum'):
            if group2['Use Emissions'].mean() < pathway['Emissions']:
                pathway['Emissions'] = group2['Use Emissions'].mean()
                pathway['Pathway Number'] = name2
        avminpathways.append(pathway)
    #find the maximum emissions pathway for each country, production method and transmission vector
    maxpathways = []
    for name,group in end_uses_df.groupby(['Country','Production Method','T Vector']):
        pathway = {'Pathway Number':0,'Emissions':float(0)}
        for name2,group2 in group.groupby('Pathwaynum'):
            if group2['Use Emissions'].max() > pathway['Emissions']:
                pathway['Emissions'] = group2['Use Emissions'].max()
                pathway['Pathway Number'] = name2
        maxpathways.append(pathway)
    
    minpathways = []
    for name,group in end_uses_df.groupby(['Country','Production Method','T Vector']):
        pathway = {'Pathway Number':0,'Emissions':float(200)}
        for name2,group2 in group.groupby('Pathwaynum'):
            if group2['Use Emissions'].min() < pathway['Emissions']:
                pathway['Emissions'] = group2['Use Emissions'].min()
                pathway['Pathway Number'] = name2
        minpathways.append(pathway)

    avminpathways = end_uses_df[end_uses_df['Pathwaynum'].isin([x['Pathway Number'] for x in avminpathways])]
    maxpathways = end_uses_df[end_uses_df['Pathwaynum'].isin([x['Pathway Number'] for x in maxpathways])]
    minpathways = end_uses_df[end_uses_df['Pathwaynum'].isin([x['Pathway Number'] for x in minpathways])]

    #define colours of each vector
    unique_values = end_uses_df['Legend'].unique()
    colors = ['#a5c46c','#fc8d62','#8da0cb','#e78ac3','#a87cc4','#ffd92f','#e5c494','#b3b3b3','#66c2a5']
    color_dict={}
    for i, x in zip(unique_values, colors):
        color_dict[i] = x
    
    #plot the minimum and maximum as bar charts on the same axis
    fig, (ax1, ax2,ax3,ax4) = plt.subplots(1, 4, sharey=True,width_ratios=[2,4,3,30],figsize=(12,8))

    df_uk = avminpathways[avminpathways['Country'] == 'UK']
    df_sp = avminpathways[avminpathways['Country'] == 'Spain']
    df_AU = avminpathways[avminpathways['Country'] == 'Australia']
    df_other = avminpathways[(avminpathways['Country'] != 'UK')&(avminpathways['Country'] != 'Spain')&(avminpathways['Country'] != 'Australia')]

    handle_list, label_list = [], []
    for df,ax in zip([df_uk,df_sp,df_AU,df_other],[ax1,ax2,ax3,ax4]):
        df = df.sort_values('Legend')
        sns.barplot(data=df, x='Country', y='Use Emissions', hue='Legend', palette=color_dict, ax=ax, errorbar=('pi',100),err_kws={'linewidth': 0.9}, capsize=0.2,alpha=1)
    
    df_uk = maxpathways[maxpathways['Country'] == 'UK']
    df_sp = maxpathways[maxpathways['Country'] == 'Spain']
    df_AU = maxpathways[maxpathways['Country'] == 'Australia']
    df_other = maxpathways[(maxpathways['Country'] != 'UK')&(maxpathways['Country'] != 'Spain')&(maxpathways['Country'] != 'Australia')]

    for df,ax in zip([df_uk,df_sp,df_AU,df_other],[ax1,ax2,ax3,ax4]):
        df = df.sort_values('Legend')
        sns.barplot(data=df, x='Country', y='Use Emissions', hue='Legend', palette=color_dict,errorbar=None, ax=ax,alpha=0.2)

    df_uk = avminpathways[avminpathways['Country'] == 'UK']
    df_sp = avminpathways[avminpathways['Country'] == 'Spain']
    df_AU = avminpathways[avminpathways['Country'] == 'Australia']
    df_other = avminpathways[(avminpathways['Country'] != 'UK')&(avminpathways['Country'] != 'Spain')&(avminpathways['Country'] != 'Australia')]

    handle_list, label_list = [], []
    for df,ax in zip([df_uk,df_sp,df_AU,df_other],[ax1,ax2,ax3,ax4]):
        df = df.sort_values('Legend')
        sns.barplot(data=df, x='Country', y='Use Emissions', hue='Legend', palette=color_dict, ax=ax, errorbar=('pi',100),err_kws={'linewidth': 0.9}, capsize=0.2,alpha=1)
        handles, labels = ax.get_legend_handles_labels()
        for handle, label in zip(handles, labels):
            if label not in label_list:
                handle_list.append(handle)
                label_list.append(label)

    #edit legend labels to be legible
    newlabels = {'AHL - Domestic':'ATR with CCS - No Transmission',
                 'AHL - CH3OH':'ATR with CCS - Methanol Tanker',
                 'AHL - NH3':'ATR with CCS - Ammonia Tanker',
                 'AHL - LH2':'ATR with CCS - Liquified Hydrogen Tanker',
                 'CPL - Domestic':'PEM Electrolysis - No Transmission',
                 'CPL - CH3OH':'PEM Electrolysis - Methanol Tanker',
                 'CPL - NH3':'PEM Electrolysis - Ammonia Tanker',
                 'CPL - LH2':'PEM Electrolysis - Liquified Hydrogen Tanker',
                 'CPL - CH2': 'PEM Electrolysis - Hydrogen Pipeline'}
    
    print(label_list)

    label_list_new = []
    for label in label_list:
        label_list_new.append(newlabels[label])


    #combine subplots
    ax1.set_ylabel('Emissions Intensity (kg CO\u2082e/kg H\u2082)')
    ax1.set_xlabel('')
    ax1.set_title('')
    ax2.set_title('')
    ax3.set_title('')
    ax4.set_title(use)

    for ax in [ax2,ax3,ax4]:
        ax.set_ylabel('')
        ax.tick_params(left = False) 
        ax.spines[['left']].set_visible(False)
        ax.spines[['right']].set_visible(False)
        ax.set_xlabel('')
 
    ax1.spines[['right']].set_visible(False)
    ax4.spines[['right']].set_visible(True)
    ax.set_xlabel('')

    # Combine legends from ax1, ax2, ax3 and ax4
    ax1.get_legend().remove()
    ax2.get_legend().remove()
    ax3.get_legend().remove()
    ax4.get_legend().remove()
    fig.text(0.5, 0.04, 'Production Country', ha='center', va='center')

    orderoflegend = [1,2,3,4,5,0,6,7,8]
    handle_list = [handle_list[i] for i in orderoflegend]
    label_list_new = [label_list_new[i] for i in orderoflegend]
    if vector == 'CH2':
        plt.ylim(0,58)
        for ax in [ax1,ax2,ax3,ax4]: 
            ax.axhline(12, color='grey', linewidth=1,linestyle='--') 
            ax.axhline(basevalues[vector], color='green', linewidth=1,linestyle='--')
        ax1.set_ylabel('Emissions Intensity (kg CO\u2082e/kg H\u2082)')
    elif vector == 'NH3':
        plt.ylim(0,25)
        for ax in [ax1,ax2,ax3,ax4]: 
            scale_y = 1
            ax.axhline(2.4*scale_y, color='grey', linewidth=1,linestyle='--') 
            #ax.set_yticks([0,17/6,17/3,17,17*3/6,17*4/6,17*5/6,17,17*7/6,17*8/6,17*9/6])
            #ticks_y = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/scale_y))
            #ax.yaxis.set_major_formatter(ticks_y) 
        ax1.set_ylabel('Emissions Intensity (kg CO\u2082e/kg NH\u2083)')
    elif vector == 'CH3OH':
        plt.ylim(0,30)
        for ax in [ax1,ax2,ax3,ax4]: 
            scale_y = 1
            ax.axhline(0.8*scale_y, color='grey', linewidth=1,linestyle='--') 
            #ax.set_yticks([0,scale_y/4,scale_y*2,scale_y*3/4,scale_y,scale_y*5/4,scale_y*3/2,scale_y*7/4,scale_y*2,scale_y*9/4,scale_y*5/2])
            #ticks_y = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/scale_y))
            #ax.yaxis.set_major_formatter(ticks_y)
            ax.axhline(0.8, color='grey', linewidth=1,linestyle='--') 
        ax1.set_ylabel('Emissions Intensity (kg CO\u2082e/kg CH\u2083OH)')
    plt.legend(handle_list, label_list_new, bbox_to_anchor=(1,1), loc='upper right',fontsize=9,framealpha=0.5,fancybox=True,ncol=2)
    title = {'CH2':'Hydrogen','NH3':'Ammonia','CH3OH':'Methanol'}
    name = title[vector]
    plt.title('Emissions Intensity of '+name+' Supply Chain by Country')
    plt.subplots_adjust(wspace=0, hspace=0)
    plt.savefig(cwd+'\\figures\\fig1'+name+'.tiff',dpi=1000)
    plt.show()

def plot_fig5(uses_df,results_df,pathway_var='min',baseline='base'):

    results_df = filter_results(results_df,production_method=['CPL'],pathway_var='min')

    #all columns needed from uses to df
    results_df['Base Emissions'] = results_df['Use'].map(dict(uses_df[['ID', 'Base emissions (kgCO2e/unit)']].values))
    results_df['Electrification Emissions'] = results_df['Use'].map(dict(uses_df[['ID','Emissions assuming electrification']].values))
    results_df['Input (kgH2/unit)'] = results_df['Use'].map(dict(uses_df[['ID', 'Input (kgH2e/unit)']].values))
    
    #create baselines for plots
    if baseline == 'base':
        results_df['Emissions reduction'] = (results_df['Base Emissions'] - results_df['Use Emissions'])/results_df['Input (kgH2/unit)']
    elif baseline == 'electrification':
        results_df['Emissions reduction'] = (results_df['Electrification Emissions'] - results_df['Use Emissions'])/results_df['Input (kgH2/unit)']

    results_df['kgCO2e_kWh'] = results_df['Emissions reduction']/(results_df['Use Energy ES']/results_df['Input (kgH2/unit)'])

    #create new dataframe with just country, use and kgCO2e_kWh
    combined_df = results_df[['Country','Use','kgCO2e_kWh']].copy()
    combined_df['Type'] = 'H2'+combined_df['Country']
    combined_df['Width'] = 1
    otheroptions = pd.read_excel(file_io_obj,'Electrification Options')
    otheroptions['Type'] = 'Electrification'
    otheroptions['Width'] = 0.7
    otheroptions.rename(columns={'country':'Country','Name':'Use','Emissions Reduction per kWh':'kgCO2e_kWh'},inplace=True)
    
    #combine heating and transport categories for ease of reading plot
    roadtransport = ['2and3wheelers','Cars','MetroTrainsandBuses','LightTrucks','Longdistancetrucksandcoaches']
    heating = ['Mid/LowTemperatureHeat','CommercialHeating','HighTemperatureHeat','Domesticheating']
    fertilser = ['Fertiliser-AmmoniumNitrate','Fertiliser-Phosphate']

    for index,row in combined_df.iterrows():
        if row['Use'] in roadtransport:
            combined_df.at[index,'Use'] = 'Road Transport'

        elif row['Use'] in heating:
            combined_df.at[index,'Use'] = 'Heating'

        elif row['Use'] in fertilser:
            combined_df.at[index,'Use'] = 'Fertiliser'

        elif row['Use'] == 'Shipping-Ammonia':
            combined_df.at[index,'Use'] = 'Shipping'
        
        elif row['Use'] == 'JetAviation':
            combined_df.at[index,'Use'] = 'Aviation'
        
        elif row['Use'] == 'Biogasupgrading':
            combined_df.at[index,'Use'] = 'Biogas Upgrading'
        
        elif row['Use'] == 'Non-RoadMobileMachinery':
            combined_df.at[index,'Use'] = 'Non-Road Mobile Machinery'
        
        elif row['Use'] == 'Longdurationgridbalancing':
            combined_df.at[index,'Use'] = 'Grid Balancing'
        
        elif row['Use'] == 'RemoteandRuralTrains':
            combined_df.at[index,'Use'] = 'Trains'

        elif row['Use'] == 'Hydrogenation':
            combined_df.at[index,'Use'] = 'Replacing Grey Hydrogen'

        elif row['Use'] == 'IronandSteel':
            combined_df.at[index,'Use'] = 'Steel Production'


    combined_df = pd.concat([combined_df,otheroptions],ignore_index=True)
    combined_df = combined_df.sort_values('kgCO2e_kWh')
    
    new_df = pd.DataFrame()
    for name,group in combined_df.groupby(['Country','Use']):
        if name[0] == 'UK':
            new_df.at[len(new_df),'Country'] = name[0]
            new_df.at[len(new_df)-1,'Use'] = name[1]
            new_df.at[len(new_df)-1,'kgCO2e_kWh'] = group['kgCO2e_kWh'].max()
            new_df.at[len(new_df)-1,'Type'] = group['Type'].values[0]
            new_df.at[len(new_df)-1,'Width'] = group['Width'].values[0]
        else:
            new_df.at[len(new_df),'Country'] = name[0]
            new_df.at[len(new_df)-1,'Use'] = name[1]
            new_df.at[len(new_df)-1,'kgCO2e_kWh'] = group['kgCO2e_kWh'].max()
            new_df.at[len(new_df)-1,'Type'] = group['Type'].values[0]
            new_df.at[len(new_df)-1,'Width'] = group['Width'].values[0]

    print(new_df[new_df['Country'] == 'UK'])
    new_df = new_df.sort_values('kgCO2e_kWh')
    #add none electrification emissions reductions, data is in the uses_df - need renewable energy intensity

    fig, ax = plt.subplots(figsize=[12,6],layout='tight')
    sns.barplot(data=new_df[new_df['Country'] == 'UK'], x='kgCO2e_kWh', y='Use',hue='Type', ax=ax,palette=['#bebada','#fdb462','#8dd3c7'])

    sns.barplot(data=new_df[new_df['Country'] == 'Spain'], x='kgCO2e_kWh', y='Use',hue='Type',palette=['#fb8072'], ax=ax,errorbar=None,alpha=1)
    sns.barplot(data=new_df[new_df['Country'] == 'Brazil'], x='kgCO2e_kWh', y='Use',hue='Type',palette=['#8dd3c7'], ax=ax,errorbar=None,alpha=1)
    sns.barplot(data=new_df[new_df['Country'] == 'Australia'], x='kgCO2e_kWh', y='Use',hue='Type',palette=['#80b1d3'], ax=ax,errorbar=None,alpha=1)
    #y_pos = []
    #bars = []
    #total = -1
    #for x in new_df['Use'].unique():
    #    total += 1
    #    y_pos.append(total)
    #    bars.append(x)

    mapping  = {'H2UK':'UK','H2Spain':'Spain','H2Australia':'Australia','H2Brazil':'Brazil','Electrification':'Electrification'}
    handles, labels = ax.get_legend_handles_labels()
    newlabels = [mapping[label] for label in labels]
    plt.legend(handles, newlabels)
    ax.set_xlim(left=0)
    #ax.set_yticks(y_pos,bars)
    ax.set_xlabel('Emissions Reduction (kgCO2e/kWh)')
    ax.set_ylabel('Hydrogen Application')
    plt.show()

def sobol_plot():
    combined_sobol_df = loadmcdata('Dataframes_Sobol_offshore_CO2e1.xz','Pickle')
    combined_sobol_df.to_csv('combined sobol CO2e1.csv')


    sobol_df = pd.read_csv('combined sobol CO2e1.csv',header=0)
    dict_num = pd.read_csv('dict_num.csv',header=0)
    print(sobol_df.columns)
    num_dict = {}
    for index,row in dict_num.iterrows():
        num_dict[row['Num']] = row['Dict']

    #get column names from df

    sobol_df.rename(columns={'Unnamed: 0': "Num"},inplace=True)
    columns = sobol_df.columns.tolist()
    columns.remove('Num')

    #flatten the dataframe
    sobol_df = pd.melt(sobol_df,id_vars=['Num'],value_vars=columns,var_name='stage',value_name='Sobol Index (St)')

    sobol_df['Pathway type'] = sobol_df['Num'].map(num_dict)
    sobol_df['Production Meth'] = sobol_df['Pathway type'].apply(lambda x: x[:3])
    print(sobol_df['Production Meth'].unique())

    stage_labels = {'S0':'Energy Source','S1':'Energy Transmission','S2':'Hydrogen Production',
                    'S3':'Conversion 1','S4':'Storage 1','S5':'Transport 1',
                    'S6':'Conversion 2','S7':'Storage 2','S8':'Transport 2','S9':'Conversion 3','S10':'Storage 3'}
    
    sobol_df['stage label'] = sobol_df['stage'].map(stage_labels)

    ukdata = sobol_df[(sobol_df['Pathway type'].str.contains('UK'))&sobol_df['stage'].isin(['S0','S1','S2','S3','S4','S5'])].copy()

    fig, ax = plt.subplots(2,2,figsize=[12,6],sharex=True,height_ratios=[0.5,1])
    sns.boxplot(data=ukdata[ukdata['Pathway type']=='CPLUK'],x='Sobol Index (St)',y ='stage label', ax=ax[0,0],whis=[2.5,97.5],showfliers=False)
    sns.boxplot(data=sobol_df[(sobol_df['Pathway type']!='CPLUK')&(sobol_df['Pathway type']!='AHLUK')&
                              (sobol_df['Production Meth']=='AHL')],x='Sobol Index (St)',y ='stage label', ax=ax[1,0],whis=[2.5,97.5],showfliers=False)
    sns.boxplot(data=ukdata[ukdata['Pathway type']=='AHLUK'],x='Sobol Index (St)',y ='stage label', ax=ax[0,1],whis=[2.5,97.5],showfliers=False)
    sns.boxplot(data=sobol_df[(sobol_df['Pathway type']!='CPLUK')&(sobol_df['Pathway type']!='AHLUK')&
                              (sobol_df['Production Meth']=='CPL')],x='Sobol Index (St)',y ='stage label', ax=ax[1,1],whis=[2.5,97.5],showfliers=False)

    ax[0,0].set_title('A. PEM Electrolysis - UK',loc='left')
    ax[1,0].set_title('C. PEM Electrolysis - Imported',loc='left')
    ax[0,1].set_title('B. Autothermal Reforming with CCS - UK',loc='left')
    ax[1,1].set_title('D. Autothermal Reforming with CCS - Imported',loc='left')

    #remove x tick labels from all but the bottom plots

    ax[0,1].set_ylabel('')
    ax[0,1].set_yticklabels([])
    ax[1,1].set_ylabel('')
    ax[1,1].set_yticklabels([])

    ax[1,1].set_xlim(left=0)

    plt.subplots_adjust(wspace=0.05, hspace=0.2)
    plt.tight_layout()
    plt.show()

def plot_fig2(results_df):
    results_df = results_df[(results_df['Use'] == 'Hydrogenation')].copy()
    
    #for each country, find the minimum emissions
    minpathways = {}
    for name,group in results_df.groupby(['Country']):
        print(name[0])
        minpathways[name[0]] = group['Use Emissions'].min()

    print(minpathways)
    
    results_df['Min Emissions'] = results_df['Country'].map(minpathways)

    results_df['Compared to min'] = (results_df['Use Emissions']-results_df['Min Emissions'])*100/results_df['Min Emissions']

    energysourcemapping = {'Solar(AU)':'Solar','Solar(SP)':'Solar','Solar(UK)':'Solar','Solar(BR)':'Solar','Solar(EG)':'Solar','Solar(KA)':'Solar',
                        'Solar(MA)':'Solar','Solar(USA)':'Solar',
                        'Wind(AU)':'Wind','Wind(SP)':'Wind','OffshoreWind(UK)':'Wind','Wind(BR)':'Wind','Wind(EG)':'Wind',
                        'OnshoreWind(UK)':'Wind','Wind(KA)':'Wind','Wind(MA)':'Wind','Wind(USA)':'Wind',
                        'Grid2030(UK)':'Grid2030','Grid2030(SP)':'Grid2030','Grid2030(AU)':'Grid2030','Grid2030(BR)':'Grid2030',
                        'Grid2030(EG)':'Grid2030','Grid2030(KA)':'Grid2030','Grid2030(MA)':'Grid2030','Grid2030(USA)':'Grid2030',
                        'GridCurrent(UK)':'GridCurrent','GridCurrent(SP)':'GridCurrent','GridCurrent(AU)':'GridCurrent','GridCurrent(BR)':'GridCurrent',
                        'GridCurrent(EG)':'GridCurrent','GridCurrent(KA)':'GridCurrent','GridCurrent(MA)':'GridCurrent','GridCurrent(USA)':'GridCurrent',
                        'NG(UK)':'Natural Gas','NG(SP)':'Natural Gas','NG(AU)':'Natural Gas','NG(BR)':'Natural Gas',
                        'NG(EG)':'Natural Gas','NG(KA)':'Natural Gas','NG(MA)':'Natural Gas','NG(USA)':'Natural Gas'}

    results_df['Energy Source for plot'] = results_df['Energy Source'].map(energysourcemapping)

    results_df['Len Vectors'] = results_df['vectors'].apply(lambda x: len(set(x)))

    #if CH3OH in vectors, make column Methanol true
    results_df['Methanol'] = results_df['vectors'].apply(lambda x: 'CH3OH' in x)
    results_df['Other Vector'] = results_df['vectors'].apply(lambda x: 'CH3OH' in x or 'NH3' in x or 'LH2' in x)
    
    for country in ['UK']:
        results_dfbycountry = results_df[results_df['Country'] == country]

        pathwaynum = results_df[results_df['Use Emissions']==results_dfbycountry['Use Emissions'].min()]['Pathwaynum'].values[0]
        minpathwaymax = results_df[results_df['Pathwaynum']==pathwaynum]['Use Emissions'].max()
        vectors = results_df[results_df['Pathwaynum']==pathwaynum]['vectors'].values[0]
        country = results_df[results_df['Pathwaynum']==pathwaynum]['Country'].values[0]
        energysource = results_df[results_df['Pathwaynum']==pathwaynum]['Energy Source'].values[0]
        productionmethod = results_df[results_df['Pathwaynum']==pathwaynum]['Production Method'].values[0]

        results_df['vectors'] = results_df['vectors'].apply(lambda x: x[1:]).astype(str)
       
        vectors = results_df[results_df['Pathwaynum']==pathwaynum]['vectors'].values[0]
        energysource1 = results_df[(results_df['vectors'] == vectors)&
                                  (results_df['Production Method'] == productionmethod)&
                                  (results_df['Energy Source'] =='OffshoreWind(UK)')&
                                  (results_df['Country'] == country)]
        
        energysource2 = results_df[(results_df['vectors'] == vectors)&
                                  (results_df['Production Method'] == productionmethod)&
                                  (results_df['Energy Source'] =='Solar(UK)')&
                                  (results_df['Country'] == country)]

        productionmethod1 = results_df[(results_df['Country'] == country)&
                                    (results_df['Production Method'] != productionmethod)&
                                    (results_df['vectors'] == vectors)]

        lh2 = results_df[(results_df['Energy Source'] == energysource)&
                            (results_df['Production Method'] == productionmethod)&
                            (results_df['Country'] == country)&
                            (results_df['vectors'] == "['LH2']")]
        
        print(results_df[(results_df['Energy Source'] == energysource)&
                            (results_df['Production Method'] == productionmethod)&
                            (results_df['Country'] == country)]['vectors'].unique())
        
        nh3 = results_df[(results_df['Energy Source'] == energysource)&
                            (results_df['Production Method'] == productionmethod)&
                            (results_df['Country'] == country)&
                            (results_df['vectors'] == "['NH3']")]
        
        CH3OH = results_df[(results_df['Energy Source'] == energysource)&
                            (results_df['Production Method'] == productionmethod)&
                            (results_df['Country'] == country)&
                            (results_df['vectors'] == "['CH3OH']")]

        country = results_df[(results_df['Energy Source'] == "Wind(SP)")&
                            (results_df['Production Method'] == productionmethod)&
                            (results_df['Country'] == "Spain")&
                            (results_df['vectors'] == "['CH2', 'CH2', 'CH2']")]


        minimums = [
                    results_dfbycountry['Use Emissions'].min(),
                    energysource1['Use Emissions'].min(),
                    energysource2['Use Emissions'].min(),
                    lh2['Use Emissions'].min(),
                    nh3['Use Emissions'].min(),
                    CH3OH['Use Emissions'].min(),
                    productionmethod1['Use Emissions'].min(),
                    country['Use Emissions'].min()]
        
        maximums = [
                    minpathwaymax,
                    energysource1['Use Emissions'].max(),
                    energysource2['Use Emissions'].max(),
                    lh2['Use Emissions'].max(),
                    nh3['Use Emissions'].max(),
                    CH3OH['Use Emissions'].max(),
                    productionmethod1['Use Emissions'].max(),
                    country['Use Emissions'].max()]
        
        #reverse order or minimums and maximums
        minimums = minimums[::-1]
        maximums = maximums[::-1]

        for value in minimums:
            print((value-results_dfbycountry['Use Emissions'].min())/results_dfbycountry['Use Emissions'].min()*100)

        for value in maximums:
            print((value-results_dfbycountry['Use Emissions'].min())/results_dfbycountry['Use Emissions'].min()*100)

        start = minimums
        end = maximums

        yval = [x for x in range(len(minimums))]
        widths = [ x - y for x,y in zip(end,start)]

        fig, ax = plt.subplots(figsize=[5.2,5])
        ax.barh(y=yval, width=widths, left=start, height=0.4,color=['#b18ae7','#fc8d62','#8da0cb','#e78ac3','#a6d854','#ffd92f','#e5c494','#b3b3b3','#66c2a5'])
        
        plt.xlim(left=0,right=17)
        plt.yticks(np.arange(0, len(minimums), step=1),labels='')
        plt.savefig('fig2b.svg')
        plt.show()

def plot_fig5_SI(uses_df,results_df,baseline='base'):

    results_df = filter_results(results_df,production_method=['CPL'],pathway_var='min')

    #all columns needed from uses to df
    results_df['Base Emissions'] = results_df['Use'].map(dict(uses_df[['ID', 'Base emissions (kgCO2e/unit)']].values))
    results_df['Electrification Emissions'] = results_df['Use'].map(dict(uses_df[['ID','Emissions assuming electrification']].values))
    results_df['Input (kgH2/unit)'] = results_df['Use'].map(dict(uses_df[['ID', 'Input (kgH2e/unit)']].values))
    
    results_df = results_df[(results_df['Production Method'] == 'CPL')&(results_df['Country'].isin(['UK','Spain','Australia','Brazil']))].copy()

    #create baselines for plots
    if baseline == 'base':
        results_df['Emissions reduction'] = (results_df['Base Emissions'] - results_df['Use Emissions'])/results_df['Input (kgH2/unit)']
        labelx = 'Baseline'
    elif baseline == 'electrification':
        results_df['Emissions reduction'] = (results_df['Electrification Emissions'] - results_df['Use Emissions'])/results_df['Input (kgH2/unit)']
        labelx = 'Electrification'

    results_df['kgCO2e_kWh'] = results_df['Emissions reduction']/(results_df['Use Energy ES']/results_df['Input (kgH2/unit)'])

    #create new dataframe with just country, use and kgCO2e_kWh
    combined_df = results_df[['Country','Use','kgCO2e_kWh']].copy()
    combined_df['Type'] = 'H2'+combined_df['Country']
    otheroptions = pd.read_excel(file_io_obj,'Electrification Options')
    otheroptions['Type'] = 'Electrification'
    otheroptions.rename(columns={'country':'Country','Name':'Use','Emissions Reduction per kWh':'kgCO2e_kWh'},inplace=True)
    
    #combine heating and transport categories for ease of reading plot
    roadtransport = ['2and3wheelers','Cars','MetroTrainsandBuses','LightTrucks','Longdistancetrucksandcoaches']
    heating = ['Mid/LowTemperatureHeat','CommercialHeating','HighTemperatureHeat','Domesticheating']
    fertilser = ['Fertiliser-AmmoniumNitrate','Fertiliser-Phosphate']

    #rename columns

    for index,row in combined_df.iterrows():
        if row['Use'] in roadtransport:
            combined_df.at[index,'Use'] = 'Road Transport'

        elif row['Use'] in heating:
            combined_df.at[index,'Use'] = 'Heating'

        elif row['Use'] in fertilser:
            combined_df.at[index,'Use'] = 'Fertiliser'

        elif row['Use'] == 'Shipping-Ammonia':
            combined_df.at[index,'Use'] = 'Shipping'
        
        elif row['Use'] == 'JetAviation':
            combined_df.at[index,'Use'] = 'Aviation'
        
        elif row['Use'] == 'Biogasupgrading':
            combined_df.at[index,'Use'] = 'Biogas Upgrading'
        
        elif row['Use'] == 'Non-RoadMobileMachinery':
            combined_df.at[index,'Use'] = 'Non-Road Mobile Machinery'
        
        elif row['Use'] == 'Longdurationgridbalancing':
            combined_df.at[index,'Use'] = 'Grid Balancing'
        
        elif row['Use'] == 'RemoteandRuralTrains':
            combined_df.at[index,'Use'] = 'Trains'

        elif row['Use'] == 'Hydrogenation':
            combined_df.at[index,'Use'] = 'Replacing Grey Hydrogen'

        elif row['Use'] == 'IronandSteel':
            combined_df.at[index,'Use'] = 'Steel Production'


    #combined_df = pd.concat([combined_df,otheroptions],ignore_index=True)
    combined_df = combined_df.sort_values('kgCO2e_kWh',ascending=False)
    otheroptions['kgCO2e_kWh'] = otheroptions['kgCO2e_kWh'].round(2)
    otheroptions['Label'] = otheroptions['Use'] + ' ' + otheroptions['kgCO2e_kWh'].astype(str) + ' kgCO2e/kWh'
    order = combined_df['Use'].unique()
    fig, ax = plt.subplots(figsize=[10,6],layout='tight')
    for index,row in otheroptions.iterrows():
        ax.axvline(x=row['kgCO2e_kWh'],color='grey',alpha=1,linestyle = 'dotted')        
        ax.text(row['kgCO2e_kWh'],11,row['Label'],rotation=90,verticalalignment='bottom',horizontalalignment='right',fontsize=8)

    combined_df['y'] = combined_df['Use'] + ' ' + combined_df['Country']
    #combined_df = combined_df.sort_values('y')
    sns.stripplot(data=combined_df, x='kgCO2e_kWh', y='Use',hue='Country', dodge=False,jitter=True,ax=ax, alpha = 1,palette=colordict,
                  order  = order,s=2)

    ax.set_xlim(left=0)

    ax.legend(loc='upper right',markerscale = 5,title = 'Production Country')
    ax.set_xlabel('Emissions Reduction per unit of Renewable Electricity Compared to '+labelx+' Emissions (kgCO2e/kWh)')
    plt.savefig('fig5.png',dpi=1000)
    plt.show()

#end_uses_dataframe = loadmcdata('End_uses_dataframe_final.xz','Pickle')
#print(end_uses_dataframe['stage emissions'].min())
#end_uses_dataframe['Pathway Legend'] = end_uses_dataframe['Pathwaynum'].astype(str)+end_uses_dataframe['Use']
#results_df = process_results(end_uses_dataframe,uses_df)
#savepickle(results_df,'results_df.xz','Pickle')
#print('Results saved')
results_df = loadmcdata('results_df.xz','Pickle')

#plot_fig1(results_df,'CH2')
#plot_fig1(results_df,'NH3')
#plot_fig1(results_df,'CH3OH')
#plot_fig2(results_df)
plotfig3andfig4(30,False,True) 
plot_fig5_SI(uses_df,results_df)



#plotfig3andfig4(30)