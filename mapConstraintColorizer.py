# -*- coding: utf-8 -*-
"""
Created on Sat Feb 13 12:09:30 2021

@author: ansonl
"""

import geopandas as gpd
import matplotlib.pyplot as plt
from collections import OrderedDict
import sys

regionFile = 'geographic-data/us_state_stats/us_state_stats.shp'

gdf = gpd.read_file(regionFile)

statesData = {}

# Cache for longest chains found for each state
statesLongestChainCache = {}

GENERATE_ANIMATION = True
currentAnimationFrame = 0
ANIMATION_COLOR_NEIGHBOR_EVAL = 2
ANIMATION_COLOR_START = 10
currentAnimationTmpValue = ANIMATION_COLOR_START

for index, state in gdf.iterrows():
    
    neighbors = gdf[~gdf.geometry.disjoint(state.geometry)].STUSPS.tolist()
    
    #Remove the state from its own neighbors list
    neighbors = [ stAbbr for stAbbr in neighbors if state.STUSPS != stAbbr ]
    
    #Table column names are truncated to 10 chracters
    #print(state)
    
    popDensity = ((float(state.TotalFores) + float(state.LandRParkW)*2 + float(state.GrasslandP)) / float(state.TotalLand))
    #popDensity += ((float(state.TotalFores) + float(state.LandRParkW)*2 ) / float(state.TotalLand))
    
    popDensity += (float(state.LandRParkW)*4) / float(state.TotalLand)
    
    #popDensity = float(state.FIAForestC) + 100*((float(state.TotalFores) + float(state.LandRParkW) + float(state.GrasslandP)) / float(state.TotalLand))
    
    singleStateData = {'name':state.STUSPS, 'popDensity':popDensity, 'neighbors':neighbors}
    
    statesData[state.STUSPS] = singleStateData
    
statesData = OrderedDict(sorted(statesData.items(), key=lambda item: item[1]['popDensity'], reverse=True))

def clearAnimationFrame():
    global currentAnimationTmpValue
    #Setup geo dataframe for plotting    
    gdf['TMP'] = 0
    currentAnimationTmpValue = ANIMATION_COLOR_START
    for state in statesData.keys():
        statesData[state]['tmp'] = 0

def generateAnimationFrame():
    global currentAnimationFrame
    #Print number of frames
    #print(currentAnimationFrame)
    #currentAnimationFrame += 1
    #return
    
    print('Generating animation frame {}'.format(currentAnimationFrame))
    for index, state in gdf.iterrows():
        if 'tmp' not in statesData[state.STUSPS]:
            statesData[state.STUSPS]['tmp'] = 0
        gdf.at[index, 'TMP'] = statesData[state.STUSPS]['tmp']
        
    f, ax = plt.subplots()
    
    #https://matplotlib.org/stable/tutorials/colors/colormaps.html
    #qualitative tab20c
    gdf.plot(ax=ax, column="TMP", legend=False, cmap=plt.get_cmap('viridis'))
    ax.set_xlim(-172.44 - .1, -66.94 - .1) # added/substracted value is to give some margin around total bounds
    ax.set_ylim(18.91 - .1, 71.38+.1)
    plt.title('Constraint Colorizer Algorithm Step {}'.format(currentAnimationFrame))
    plt.savefig('frames/{}.png'.format(currentAnimationFrame), dpi=150)
    f.clear()
    plt.close("all")
    currentAnimationFrame += 1
    #plt.show()


def findNextChainStep(state, previousState):
    global currentAnimationTmpValue #need global keyword because we try to edit the value later in the function        
    if GENERATE_ANIMATION == True:
        if previousState == None:
            currentAnimationTmpValue += 1
        statesData[state]['tmp'] = currentAnimationTmpValue
        generateAnimationFrame()
        
        
    
    #Check states longest chain cache to find previously found chain
    if state in statesLongestChainCache.keys():
        return statesLongestChainCache[state]
    
    neighbors = statesData[state]['neighbors']
    
    #Remove previousState from neighbors that can be next step
    neighbors = [n for n in neighbors if previousState != n]
    
    if GENERATE_ANIMATION == True:
        for n in neighbors:
            if statesData[n]['tmp'] != ANIMATION_COLOR_NEIGHBOR_EVAL:
                statesData[n]['tmpSave'] = statesData[n]['tmp']
            statesData[n]['tmp'] = ANIMATION_COLOR_NEIGHBOR_EVAL
        generateAnimationFrame()
    

    longestStatesToEnd = []
    
    for n in neighbors:
        if statesData[n]['popDensity'] <= statesData[state]['popDensity']:
            if (GENERATE_ANIMATION == True) and (previousState == None):
                currentAnimationTmpValue += 1
            statesToEnd = findNextChainStep(n, state)
            if len(statesToEnd) > len(longestStatesToEnd):
                longestStatesToEnd = statesToEnd
                
    if GENERATE_ANIMATION == True:
        statesData[state]['tmp'] = currentAnimationTmpValue
        for n in neighbors:
            statesData[n]['tmp'] = statesData[n]['tmpSave']
        generateAnimationFrame()
                
    if len(longestStatesToEnd) == 0 :
        return [state]
            
    #print('{} found {} neighbor with longest chain {}'.format(state, longestStatesToEnd[0], len(longestStatesToEnd)))
    
    longestStatesToEnd.insert(0, state)
    
    #memoization does not work. All entries in dictionary are set each time!?
    #statesLongestChainCache[state] = longestStatesToEnd[:]
    
    return longestStatesToEnd

print('Finding neighbors for regions...')

for state in statesData.keys():
    if GENERATE_ANIMATION == True:
        currentAnimationTmpValue = 0
        clearAnimationFrame()
        
    chain = findNextChainStep(state, None)
    #print(chain, len(chain))
    
def computeDensityColorForState(state):
    lowestNeighborDensityColor = 0
    for neighbor in statesData[state]['neighbors']:
        if 'densityColor' in statesData[neighbor]:
            nColor = statesData[neighbor]['densityColor']
            if nColor > lowestNeighborDensityColor:
                lowestNeighborDensityColor = nColor
        
    return lowestNeighborDensityColor + 1

print('Computing color for ' + str(len(statesData)) + ' regions...')

for state in statesData.keys():
    color = computeDensityColorForState(state)
    statesData[state]['densityColor'] = color
    #print(state, color)

def computeSmoothedDensityColorForState(state):
    # highest neighbor density color that is less than current state density color
    highestNeighborDensityColor = sys.maxsize
    for neighbor in statesData[state]['neighbors']:
        if 'densityColor' in statesData[neighbor]:
            nColor = statesData[neighbor]['densityColor']
            #print(state, statesData[state]['densityColor'], "smooth neigh ", neighbor, nColor ," target", highestNeighborDensityColor - 1)
            if nColor < highestNeighborDensityColor and nColor > statesData[state]['densityColor']:
                highestNeighborDensityColor = nColor
    
    #print(state, statesData[state]['densityColor'], "smooth neigh target", highestNeighborDensityColor - 1)
    
    if highestNeighborDensityColor != sys.maxsize and highestNeighborDensityColor - 1 > statesData[state]['densityColor']:
        return highestNeighborDensityColor - 1

print('Smoothing colors...')

for state in reversed(statesData.keys()):
    color = computeSmoothedDensityColorForState(state)
    if color != None:
        statesData[state]['densityColor'] = color

print('Plotting on map...')

#Setup geo dataframe for plotting    
gdf['DENSITYCOLOR'] = 0

for index, state in gdf.iterrows():
    gdf.at[index, 'DENSITYCOLOR'] = statesData[state.STUSPS]['densityColor']
    
f, ax = plt.subplots()
#qualitative tab20c

gdf.plot(ax=ax, column="DENSITYCOLOR", legend=True, cmap=plt.get_cmap('Spectral'))
ax.set_xlim(-172.44 - .1, -66.94 - .1) # added/substracted value is to give some margin around total bounds
ax.set_ylim(18.91 - .1, 71.38+.1)
plt.savefig('colorizedMap.png', dpi=1200)
plt.show()
