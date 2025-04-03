import matplotlib.pyplot as plt
import numpy as np
import sys, os
import json
from types import SimpleNamespace
import pandas as pd
import re
from datetime import datetime

filenames = []
individual_file_or_parent_folder = input('Input is a file or parent folder: ')

if 'folder' in individual_file_or_parent_folder:
    parent_folder_path = input('Input the parent folder path containg subfolders with CV data: ')
    if parent_folder_path == '':
        parent_folder_path = r"C:\Users\paras\Desktop\cyclic voltammetry"
        print('Using default path:', parent_folder_path)
    else:
        sys.path.append(parent_folder_path)
        os.chdir(parent_folder_path)
    for root, dirs, files in os.walk(parent_folder_path):
        for file in files:
            if file.endswith('.pssession') and 'cv' in file:
                # print(os.path.join(root, file))
                filenames.append(os.path.join(root, file))
else:
    # x = input('Input the path of file: ')
    # filenames.append(x)
    filenames = [r"C:\Users\paras\OneDrive - IIT Delhi\MFC data\cyclic voltammetry\29_1_25\mfc1_anode_manali_5mvps.pssession"]


def parse_and_save_experiment_data(file_paths):
    # Create DataFrame using previous parsing logic
    df = parse_experiment_data(file_paths)
    
    # Determine parent directory of 'cyclic voltammetry'
    try:
        sample_path = file_paths[0]
        parts = sample_path.split('\\')
        cv_index = parts.index('cyclic voltammetry')
        parent_dir = '\\'.join(parts[:cv_index])
    except (ValueError, IndexError):
        print("Error: Could not find 'cyclic voltammetry' in file paths")
        return

    # Get user format choice
    format_choice = input("Choose file format (csv/txt) [default: csv]: ").strip().lower()
    if not format_choice:
        format_choice = 'csv'
    elif format_choice not in ['csv', 'txt']:
        print("Invalid choice. Defaulting to csv.")
        format_choice = 'csv'

    # Create save path
    filename = f"experiment_data.{format_choice}"
    save_path = os.path.join(parent_dir, filename)

    # Save file
    try:
        if format_choice == 'csv':
            df.to_csv(save_path, index=False)
        else:
            df.to_csv(save_path, sep='\t', index=False)
        print(f"Successfully saved data to:\n{save_path}")
    except Exception as e:
        print(f"Error saving file: {str(e)}")

def group_same_experiments(file_paths):
    # Regex to match scan rate patterns like "5mvps", "10mvs", etc.
    scan_rate_pattern = re.compile(r'\d+mvp?s')

    # Dictionary to hold groups of experiments
    experiment_groups = {}

    for path in file_paths:
        filename = path.split('\\')[-1]  # Extract filename from path
        
        # Replace the scan rate part with a placeholder
        normalized_name = scan_rate_pattern.sub('SCAN_RATE', filename)
        
        if normalized_name not in experiment_groups:
            experiment_groups[normalized_name] = []
        experiment_groups[normalized_name].append(file_paths.index(path))

    # Return groups with multiple scan rates for the same experiment
    return experiment_groups

def parse_experiment_data(file_paths):
    data = []
    
    # Regex patterns
    scan_rate_pattern = re.compile(r'(\d+)mvp?s')  # Captures scan rates like 5mvps, 10mvs
    mfc_pattern = re.compile(r'mfc(\d+)')  # Captures MFC numbers
    ferricyanide_pattern = re.compile(r'ferricyanide(?:_(\d+mM))?')  # Captures concentration
    material_pattern = re.compile(r'(avcarb|carbon felt|carbon cloth|graphite)')
    
    for path in file_paths:
        # Split path into components
        parts = path.split('\\')
        filename = parts[-1]
        date_str = parts[-2]  # Get date from folder name
        
        # Parse date (format dd_mm_yy)
        date = datetime.strptime(date_str, '%d_%m_%y').date()
        
        # Initialize row dictionary
        row = {
            'path': path,
            'date': date,
            'scan_rate': None,
            'electrode_type': None,
            'material': None,
            'mfc_number': None,
            'mfc_location': 'Manali',  # Default to Manali
            'ferricyanide_conc': None,
            'additional_info': []
        }
        
        # Extract scan rate
        scan_match = scan_rate_pattern.search(filename)
        if scan_match:
            row['scan_rate'] = f"{scan_match.group(1)} mV/s"
        
        # Extract MFC details
        mfc_match = mfc_pattern.search(filename)
        if mfc_match:
            row['mfc_number'] = int(mfc_match.group(1))
            
            # Determine MFC location (Goa after Jan 2025)
            if date >= datetime(2025, 1, 1).date() and 'manali' not in filename.lower():
                row['mfc_location'] = 'Goa'
        
        # Extract materials
        material_match = material_pattern.search(filename)
        if material_match:
            row['material'] = material_match.group(1).replace('_', ' ').title()
        else:
            row['material'] = 'carbon felt'
        
        # Electrode type (anode/cathode)
        if 'cathode' in filename.lower():
            row['electrode_type'] = 'Cathode'
        else:
            row['electrode_type'] = 'Anode'
        
        # Ferricyanide testing
        if 'ferricyanide' in filename.lower():
            fer_match = ferricyanide_pattern.search(filename)
            row['ferricyanide_conc'] = fer_match.group(1) if fer_match else 'Concentration not specified'
        
        # Additional info from filename
        additional_info = []
        if 'reference' in filename:
            additional_info.append('Reference electrode mentioned')
        if 'start_at' in filename:
            additional_info.append('Custom starting potential')
        
        row['additional_info'] = ', '.join(additional_info) if additional_info else None
        
        data.append(row)
    
    return pd.DataFrame(data)

def _getMethodType(method):
    methodName = ''
    splitted = method.split("\r\n")
    for line in splitted:
        if "METHOD_ID" in line:
            methodName = line.split("=")[1]
    return methodName

def extract_cv_data_from(filenames):
    index = 0
    _experimentList = []
    readData = {}
    for filename in filenames:
        f = open(filename, "rb")
        readData[index] = f.read().decode('utf-16').replace('\r\n',' ').replace(':true',r':"True"').replace(':false',r':"False"')
        index = index + 1
        f.close()

    def _getMethodType(method):
        methodName = ''
        splitted = method.split("\r\n")
        for line in splitted:
            if "METHOD_ID" in line:
                methodName = line.split("=")[1]
        return methodName

    parsedData = {}
    for file in range(len(filenames)):
        data2 = readData[file][0:(len(readData[file]) - 1)] # has a weird character at the end
        parsedData[file] = json.loads(data2, object_hook=lambda d: SimpleNamespace(**d))

    for file in range(len(filenames)):
        for measurement in parsedData[file].Measurements:
            currentMethod = _getMethodType(measurement.Title).upper()
            index = len([i for i, s in enumerate(_experimentList) if currentMethod in s])
            _experimentList.append(currentMethod + ' ' + str(index + 1))
    
    return parsedData

def extract_voltage_current_values(data):
    date = data.MethodForMeasurement.split("\n")[1].split(' ')[0][1:]
    g = False
    num_plots_per_file = (len(data.Measurements[0].DataSet.Values)-1)//2
    voltage_values = []
    current_values = []
    try:
        if num_plots_per_file == 1:
            for i in range(len(data.Measurements[0].DataSet.Values[1].DataValues)):
                voltage_values.append(data.Measurements[0].DataSet.Values[1].DataValues[i].V)
                current_values.append(data.Measurements[0].DataSet.Values[2].DataValues[i].V)
        else:
            g = True
            for j in range(num_plots_per_file):
                voltage_values.append([])
                current_values.append([])
                for i in range(len(data.Measurements[0].DataSet.Values[1].DataValues)):
                    voltage_values[j].append(data.Measurements[0].DataSet.Values[2*j+1].DataValues[i].V)
                    current_values[j].append(data.Measurements[0].DataSet.Values[2*j+2].DataValues[i].V)
    except:
        return
    if g:
        return voltage_values[0], current_values[0], date, g
    else:
        return voltage_values, current_values, date, g
    
def compiled_extracted_data(data):
    extracted_data = {}
    count = 0
    for i in parsedData:
        v = parsedData[i]
        try:
            extracted_data[count] = extract_voltage_current_values(v)
        except:
            pass
        count+=1
    return extracted_data


'''Plotting the data for anodic, cathodic and net current'''
def individual_cv_plots_with_or_without_net_current(v, i, labels, name, plot_title = 'Cyclic Voltammetry', if_net_current = True):
    i_anodic = np.array(i[:len(i)//2])
    i_cathodic = i[len(i)//2:]
    i_cathodic.reverse()
    i_cathodic = np.array(i_cathodic)
    v_range = np.array(v[:len(v)//2])
    net_current = i_anodic + i_cathodic

    plt.plot(v_range, i_anodic, label='Anodic Current')
    plt.plot(v_range, i_cathodic, label='Cathodic Current')
    if if_net_current:
        plt.plot(v_range, net_current, '-.', label='Net Current (Anodic + Cathodic) ')
    plt.plot(v_range, np.zeros(len(v_range)), 'k--', label='Zero Current')
    plt.xlabel('Voltage (V)')
    plt.ylabel('Current (mA)')
    plt.title(plot_title)
    plt.legend()
    plt.savefig('C:/files/python scripts/plots/{}.png'.format(name), dpi=600)
        


def same_group_plots(file):
    for group in file:
        l = len(group)
        c = False
        q = 'Manali'
        for index in file[group]:
            scan_rate = meta_data.loc[index, 'scan_rate']
            culture = meta_data.loc[index, 'mfc_location']
            date = meta_data.loc[index, 'date']
            if total_data[index]:
                v, i, date, g = total_data[index]
                if g:
                    plt.plot(v[0], i[0], label = scan_rate)
                plt.plot(v, i, label = scan_rate)
                c = True
        if c:
            plt.plot(v, np.zeros(len(v)), 'k--', label='Zero Current')
            plt.xlabel('Voltage (V)')
            plt.ylabel('Current (mA)')
            if culture == 'Goa':
                q = 'Goa'
            plt.title('{} MFC Cyclic Voltammetry on {}'.format(q, date))
            plt.legend()
            plt.savefig('C:/files/python scripts/plots/{}.png'.format(date), dpi=600)
            plt.close()


meta_data = parse_experiment_data(filenames)

'''Extract cv data from pssession file'''
parsedData = extract_cv_data_from(filenames)

total_data = compiled_extracted_data(parsedData)



'''plot grouped together plots'''
# same_group_plots(group_same_experiments(filenames))



index=0
for data in parsedData:
    '''Extract individual voltage and current values'''
    if index == 2:
        break
    try:
        v, i, date, g = extract_voltage_current_values(parsedData[data])
        name = str(date)+'__'+str(index)
        x = individual_cv_plots_with_or_without_net_current(v, i, 'x', name)
        plt.close()
    except:
        print(index)
    index+=1