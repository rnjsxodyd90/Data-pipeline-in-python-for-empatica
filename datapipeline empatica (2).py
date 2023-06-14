#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pyempatica import EmpaticaClient, EmpaticaE4, EmpaticaDataStreams, EmpaticaServerConnectError
import time
import pandas as pd

CACHE = {}
MAX_LEN = 120
WINDOW_SIZE = 30

def process_row(d, key, max_len=MAX_LEN, _cache=CACHE):
    """
    Append row d to the store 'key'.

    When the number of items in the key's cache reaches max_len,
    append the list of rows to the DataFrame and clear the list.

    """
    # keep the rows for each key separate.
    lst = _cache.setdefault(key, [])
    if len(lst) >= max_len:
        store_and_clear(lst, key)
    lst.append(d)

def store_and_clear(lst, key):
    """
    Convert key's cache list to a DataFrame and append that to the DataFrame store.
    """
    df = pd.DataFrame(lst)
    _cache[key] = []  # Clear the cache for the key
    return df

# Create an empty DataFrame to store the incoming data
df_store = pd.DataFrame()

try:
    client = EmpaticaClient()
    print("Connected to E4 Streaming Server...")
    client.list_connected_devices()
    print("Listing E4 devices...")
    time.sleep(1)
    if len(client.device_list) != 0:
        e4 = EmpaticaE4(client.device_list[0])
        if e4.connected:
            print("Connected to", str(client.device_list[0]), "device...")
            for stream in EmpaticaDataStreams.ALL_STREAMS:
                e4.subscribe_to_stream(stream)
            print("Subscribed to all streams, starting streaming...")
            try:
                e4.start_streaming()
                gsr_buffer = []
                while True:
                    data = e4.receive()  
                    if data is not None:
                        data_str = data.decode("utf-8") 
                        data_lines = data_str.strip().split("\r\n")         
                        for line in data_lines:
                            if "E4_Gsr" in line:
                                line_parts = line.split(" ")
                                if len(line_parts) >= 3:
                                    gsr_data = line_parts[2].replace(",", ".")  # Extraction of datapoint/timestamp
                                    gsr_data = float(gsr_data)
                                    # Append to the buffer
                                    gsr_buffer.append(gsr_data)
                                    # Calculate rolling mean
                                    if len(gsr_buffer) > WINDOW_SIZE:
                                        rolling_mean = sum(gsr_buffer[-WINDOW_SIZE:]) / WINDOW_SIZE
                                        gsr_dict = {
                                            'GSR': gsr_data,
                                            'RollingMean': rolling_mean
                                        }
                                        process_row(gsr_dict, 'GSR')
                                        print('Received GSR data:', gsr_data)
                                        print('Rolling Mean:', rolling_mean)
                                    else:
                                        gsr_dict = {
                                            'GSR': gsr_data,
                                            'RollingMean': gsr_data
                                        }
                                        process_row(gsr_dict, 'GSR')
                                        print('Received GSR data:', gsr_data)
                                        print('Rolling Mean:', gsr_data)
                    else:
                        print('No data received.')
            except Exception as e:
                print("Error:", str(e))
except EmpaticaServerConnectError:
    print("Failed to connect to server, check that the E4 Streaming Server is open and connected to the BLE dongle.")
# Concatenating the cached rows into a single DataFrame
df = pd.concat([store_and_clear(data_list, key) for key, data_list in CACHE.items()])
# Appending the concatenated DataFrame to the existing DataFrame store
df_store = df_store.append(df)
# printing the final stored data
print(df_store)


# In[ ]:


from pyempatica import EmpaticaClient, EmpaticaE4, EmpaticaDataStreams, EmpaticaServerConnectError
from scipy.signal import savgol_filter
import numpy as np
import time

def extract_features_gsr(data):
    
    features = {
        'mean': np.mean(data),
        'std_dev': np.std(data),
        'min': np.min(data),
        'max': np.max(data)
    }
    return features


try:
    client = EmpaticaClient()
    print("Connected to E4 Streaming Server...")
    client.list_connected_devices()
    print("Listing E4 devices...")
    time.sleep(1)
    if len(client.device_list) != 0:
        e4 = EmpaticaE4(client.device_list[0])
        if e4.connected:
            print("Connected to", str(client.device_list[0]), "device...")
       
            for stream in EmpaticaDataStreams.ALL_STREAMS:
                e4.subscribe_to_stream(stream)
            print("Subscribed to all streams, starting streaming...")
            try:
                e4.start_streaming()
                while True:
                    data = e4.receive()  
                    if data is not None:
                        data_str = data.decode("utf-8") 
                        
                       
                        data_lines = data_str.strip().split("\r\n")
                        
                        for line in data_lines:
                            if "E4_Gsr" in line:
                                line_parts = line.split(" ")
                                if len(line_parts) >= 3:
                                    gsr_data = line_parts[2]  #The extraction
                                    gsr_data = float(gsr_data)
                                    
                                    
                                    
                                   
                                    gsr_features = extract_features_gsr(gsr_data)
                                    
                                    print('Preprocessed GSR data:', gsr_data)
                                    print('Extracted GSR features:', gsr_features)
                                else:
                                    print('Invalid data format:', line)
                       
                    else:
                        print('No data received.')
            except Exception as e:
                print("Error:", str(e))

except EmpaticaServerConnectError:
    print("Failed to connect to server, check that the E4 Streaming Server is open and connected to the BLE dongle.")

