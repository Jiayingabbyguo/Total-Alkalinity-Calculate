"""
This file is for generating a summarised csv file from .pclims files (alkalinity titration machine), then calculate the total alkalinity using calkulate
Date: 2024-3-5
Author: Flynn M, Advice from Jiaying G
"""
#You will need to put the file in a same folder (expect for the "end" and "dummy" files), then edit the “Folder_name”, which I usually set it as a date; “CRM1” and “CRM2” position; and then folder path and file path into the one on your computer. 

import subprocess
import importlib.util

def install_and_import(package):
    package_name = package.split('==')[0]  # Remove version constraints if present
    if importlib.util.find_spec(package_name) is None:
        print(f"{package_name} not found, installing...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
    else:
        print(f"{package_name} is already installed.")

install_and_import('pandas')
install_and_import('PyCO2SYS')  # This is for the Calkulate library

import os
import pandas as pd
import calkulate as calk

#get input from user for these values or change manually if false.
INPUT_FROM_USER = True #THIS MAKES IT RUN IN TERMINAL!!!

#input folder, containing pclims
INPUT_DIRECTORY = '20230815'

#output folder for csv
OUTPUT_DIRECTORY = '.\\' + INPUT_DIRECTORY

#CRM position in the titration sequence
CRM1 = 1
CRM2 = 17

#Line number to find for value in pclim file
LINE_NUMBER = 21 # this line number always has the same weight value

SALINITY = 35 #default salinity

#Total alkanity of reference material
CRM_TA = 2213.68

#Change salinity for each batch
BATCH_INTERVAL = [17]
BATCH_SALINITY = [35.51]

#Get list of file names and values from the the pclims files within the directory.
def read_file_names(folder_path):
    file_names = []
    values = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.txt') and os.path.isfile(os.path.join(folder_path, file_name)):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'r') as file:
                lines = file.readlines()
                if len(lines) >= LINE_NUMBER:
                    value = lines[LINE_NUMBER].strip().split('\t')[0]
                    file_names.append(file_name)
                    values.append(value)
                else:
                    print(f"Skipping file '{file_name}' as it doesn't have enough lines.")
    return file_names, values

#if the input is not from user, then use the default values
if(INPUT_FROM_USER):
    #Show a list of folders only in this folder, ask user for folder name to be input directory
    print("Folders in this directory: ")
    for folder in os.listdir():
        if os.path.isdir(folder):
            print(folder)

    INPUT_DIRECTORY = input("Enter the folder name containing the pclims files: ")
    OUTPUT_DIRECTORY = '.\\' + INPUT_DIRECTORY

    #ask for crm1 and crm2
    CRM1 = int(input("Enter the line number of CRM1: "))
    CRM2 = int(input("Enter the line number of CRM2: "))

    #ask for default salinity
    SALINITY = float(input("Enter the default salinity: "))

    #ask for CRM_TA
    CRM_TA = float(input("Enter the CRM_TA: "))

    #get batch intervals until user enters -1
    BATCH_INTERVAL = []
    BATCH_SALINITY = []
    batch_interval = int(input("Enter the batch interval (enter -1 to stop): "))
    while batch_interval != -1:
        BATCH_INTERVAL.append(batch_interval)
        batch_salinity = float(input("Enter the batch salinity: "))
        BATCH_SALINITY.append(batch_salinity)
        batch_interval = int(input("Enter the batch interval (enter -1 to stop): "))

# Call the function to get the file names and values
file_names, values = read_file_names(INPUT_DIRECTORY)

# Convert values to numeric and unit convert from milligrams to gram
values = pd.to_numeric(values) * 0.001

# Create a DataFrame with the file names and values
df = pd.DataFrame({'file_name': file_names, 
                   'salinity': SALINITY,
                   'analyte_mass': values,
                   'read_dat_method': 'pclims',
                   'alkalinity_certified': ""})

# Iterate through the batch intervals and update 'salinity' values between the intervals
for i in range(len(BATCH_INTERVAL)):
    if i == 0:
        # For the first batch, update 'salinity' from CRM1 to BATCH_INTERVAL[0]
        df.loc[CRM1 - 1 : BATCH_INTERVAL[i] - 1, 'salinity'] = BATCH_SALINITY[i]
    else:
        # For subsequent batches, update 'salinity' from the end of the previous batch to the current batch interval
        df.loc[BATCH_INTERVAL[i-1] : BATCH_INTERVAL[i] - 1, 'salinity'] = BATCH_SALINITY[i]

# Handle the last batch
if len(BATCH_INTERVAL) > 0:
    df.loc[BATCH_INTERVAL[-1] : , 'salinity'] = BATCH_SALINITY[-1]

#Manually set CRM1 and CRM2 salinity.
df.at[CRM1-1, 'salinity'] = SALINITY
df.at[CRM2-1, 'salinity'] = SALINITY

#Manually set CRM1 and CRM2 alkalinity.
df.at[CRM1-1, 'alkalinity_certified'] = CRM_TA
df.at[CRM2-1, 'alkalinity_certified'] = CRM_TA

# Specify the output Excel file path
TA_input_file =  "TA_" + INPUT_DIRECTORY + '.csv'
output_file_path = '.\\' + INPUT_DIRECTORY +'\\'+ TA_input_file

# Write the DataFrame to CSV
df.to_csv(output_file_path, index=False)

#PART 2. calculate the TA from the summarized csv file
os.chdir(OUTPUT_DIRECTORY)

data = calk.read_csv(TA_input_file).calkulate(verbose=True)
#data["alkalinity"]  # <== here are your alkalinity results
data.to_csv("output_"+INPUT_DIRECTORY +"_S.csv")
