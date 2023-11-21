import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

Pmin = 10
Pmax = 50
reservoir = 10000

# Choosing which years/files to read
el_csv_files = ["Day-ahead Prices_202301010000-202401010000.csv"]
electricity_df = pd.DataFrame()
start_date = datetime(year=2023, month=1, day=1, hour=0, minute=0)
end_date = datetime(year=2023, month=11, day=3)

# Processing electricity prices

for filename in el_csv_files:
    process_df = pd.read_csv(filename)
    electricity_df = pd.concat([electricity_df, process_df])

electricity_df = electricity_df[electricity_df["Day-ahead Price [EUR/MWh]"] != "-"].drop(labels="BZN|CH", axis=1)
electricity_df[['time_start', 'time_stop']] = electricity_df['MTU (CET/CEST)'].str.split(' - ', expand=True)
electricity_df["time_start"] = pd.to_datetime(electricity_df["time_start"], format="%d.%m.%Y %H:%M")
electricity_df["time_stop"] = pd.to_datetime(electricity_df["time_stop"], format="%d.%m.%Y %H:%M")
electricity_df["Day-ahead Price [EUR/MWh]"] = pd.to_numeric(electricity_df["Day-ahead Price [EUR/MWh]"])

interval_size_int = 4
interval_size = pd.Timedelta(hours=interval_size_int)

electricity_df["average_electricity_price [EUR/MW]"] = pd.Series()
prices_series = pd.Series()
date_iterator = start_date
while date_iterator < end_date:
    df = electricity_df[(electricity_df["time_start"] >= date_iterator) & (
                electricity_df["time_start"] < date_iterator + interval_size)]
    # Finding the average 4 hour price in EUR/MW
    avg_price = df["Day-ahead Price [EUR/MWh]"].sum()
    indices = list(df.index.values)
    electricity_df.loc[indices[0]:indices[-1], "average_electricity_price [EUR/MW]"] = avg_price
    date_iterator = date_iterator + interval_size
electricity_df = electricity_df[electricity_df["time_start"].dt.hour % 4 == 0].drop(
    labels=["MTU (CET/CEST)", "Day-ahead Price [EUR/MWh]", "time_stop", "Currency"], axis=1)
# processing ancillary bids to find average bid, max bid, and min bid per 4-hour session

ancillary_df = pd.DataFrame()

an_csv_files = ["2023-PRL-SRL-TRL-Ergebnis.csv"]
ancillary_df = pd.DataFrame()

for filename in an_csv_files:
    process_df = pd.read_csv(filename, sep=";", low_memory=False)
    ancillary_df = pd.concat([ancillary_df, process_df])

# specifying and filtering by ancillary service type
ancillary_type = "PRL"
ancillary_df = ancillary_df[ancillary_df["Ausschreibung"].str[0:3] == ancillary_type]

# ancillary_df = ancillary_df.apply(lambda col: pd.to_numeric(col, downcast= 'float', errors = "ignore"), axis = 1)

day = ancillary_df["Ausschreibung"].str[-8:]
time = ancillary_df["Beschreibung"].str[-len("00:00 bis 04:00"):]
time_string = day + " " + time.str[0:5]
ancillary_df["time_start"] = pd.to_datetime(time_string, format="%y_%m_%d %H:%M")

# We see by unhashing the line below that volume that cannot be parted is relatively small so we can look away from that in the first place
# print(ancillary_df[ancillary_df["Teilbarkeit"] != "Ja"]["Angebotenes Volumen"].sum()/ancillary_df["Angebotenes Volumen"].sum())


# We are at the moment only keeping the 'Leisungspreis' out of the prices
ancillary_df.drop(columns=ancillary_df.columns[:4], axis=1, inplace=True)
ancillary_df.drop(columns=ancillary_df.columns[4:8], axis=1, inplace=True)
ancillary_df.drop(columns=ancillary_df.columns[5:7], axis=1, inplace=True)
# ancillary_df.drop(columns=ancillary_df.columns[])

# Unhash line below to get only bids in Switzerland
# ancillary_df = ancillary_df[ancillary_df["Land"] == "CH"]

# Renaming columns
unit_column_names = ancillary_df[ancillary_df.columns[1::2]].values[0]
new_column_names = ["volume_sold [" + str(unit_column_names[0]) + "]",
                    "ancillary_price [" + str(unit_column_names[1]) + "]", "country", "divisibility"]
ancillary_df.drop(columns=ancillary_df.columns[1:4:2], axis=1, inplace=True)
ancillary_df = ancillary_df.rename(
    columns=dict(zip(["Zugesprochenes Volumen", "Leistungspreis", "Land", "Teilbarkeit"], new_column_names)))

# Defining a capacity for the powerplant to filter the dataframe
capacity = 10

ancillary_df = ancillary_df.groupby(by=["time_start", "ancillary_price [EUR/MW]", "divisibility"], as_index=False)[
    "volume_sold [MW]"].sum()
ancillary_df = ancillary_df.merge(right=electricity_df, on="time_start").sort_values("ancillary_price [EUR/MW]",
                                                                                     ascending=False).sort_values(
    "time_start")


# define classes


class powerPlant:
    def __init__(self, P_min, P_max, reservoir):
        if (P_min > P_max):
            raise ValueError("miniaml capacity cannot be larger than the maximal capacity")
        elif (reservoir < 0):
            raise ValueError("reservoir cannot be smaller than 0!")
        else:
            self.P_min = P_min
            self.P_max = P_max
            self.P_mid = (P_min + P_max) / 2
            self.reservoir = reservoir

    def priceFunction(self, P, S_el, S_prl):
        if (self.P_min <= P and P <= self.P_mid):
            return (S_el + S_prl) * P
        elif (self.P_mid < P and P <= self.P_max):
            return (S_el - S_prl) * P + S_prl * self.P_mid * 2
        elif (P == 0):
            return 0
        else:
            raise ValueError("Operating outside of the scope of the function")

    def __str__(self):
        return "Pmin = " + str(self.P_min) + " Pmax = " + str(self.P_max) + " reservoir = " + str(
            self.reservoir) + " income_el " + str(self.income_el) + " income_as = " + str(self.income_as)

# per1 = period("test", 10, 20)
# print(per1)
# print(per1.priceFunction(25, p1))


def average_best_ancillary_prices(volume, ancillary_df):
    '''
        volume: float
        ancillary_df: dataframe formatted as the corresponding dataframes above
    '''
    ancillary_df = ancillary_df.sort_values(by=["time_start", "ancillary_price [EUR/MW]"], ascending=[True, False])
    ancillary_df["cumsum"] = ancillary_df.groupby("time_start", as_index=False)["volume_sold [MW]"].cumsum()

    ancillary_df.loc[(ancillary_df["cumsum"] > volume) & (
                ancillary_df["cumsum"] - ancillary_df["volume_sold [MW]"] < volume), "volume_sold [MW]"] = ancillary_df[
                                                                                                               "volume_sold [MW]"] - (
                                                                                                                       ancillary_df[
                                                                                                                           "cumsum"] - volume)
    ancillary_df["cumsum"] = ancillary_df.groupby("time_start", as_index=False)["volume_sold [MW]"].cumsum()
    ancillary_df = ancillary_df[ancillary_df["cumsum"] <= volume]

    # calculating weighted average of the highest ancillary prices

    ancillary_df["weight"] = ancillary_df["ancillary_price [EUR/MW]"] * ancillary_df["volume_sold [MW]"]
    result_df = pd.DataFrame()
    result_df["S_el"] = ancillary_df.groupby("time_start").first()["average_electricity_price [EUR/MW]"]
    result_df["S_prl"] = ancillary_df.groupby("time_start").sum()["weight"] / volume
    result_df["P_el"] = np.zeros(len(result_df))
    result_df["In_el"] = np.zeros(len(result_df))
    result_df["P_as"] = np.zeros(len(result_df))
    result_df["In_as"] = np.zeros(len(result_df))
    result_df["B"] = np.zeros(len(result_df))
    result_df["C"] = np.zeros(len(result_df))

    return result_df.reset_index()

result_df = average_best_ancillary_prices(30,ancillary_df=ancillary_df)

#print("creating dataframe")
#print(result_df)


#result_df = result_df.sort_values(by=['S_prl', 'S_el'], ascending=False)
#result_df = result_df.reset_index(drop=True)


#create a power plant
p1 = powerPlant(Pmin, Pmax, reservoir)

#algorithm
for index, row in result_df.iterrows():
    result_df.at[index, 'B'] = p1.priceFunction(p1.P_mid, row['S_el'], row['S_prl'])
    result_df.at[index, 'C'] = p1.priceFunction(p1.P_max, row['S_el'], row['S_prl'])
    #print(str(Bthis) + " , " + str(Bnext) + " , " + str(Cthis))

#order the result table
result_df = result_df.sort_values(by=['B', 'C'], ascending=False)
result_df = result_df.reset_index(drop=True)
res = p1.reservoir

#print(len(result_df))

for index, row in result_df.iterrows():
    if (res < p1.P_min):
        break
    elif (res <= p1.P_mid):
        result_df.at[index, 'In_as'] = p1.priceFunction(res, row['S_el'], row['S_prl'])
        result_df.at[index, 'P_as'] = res
        res = 0
        break
    elif (res == p1.P_max):
        result_df.at[index, 'In_as'] = result_df.at[index, 'C']
        result_df.at[index, 'P_as'] = p1.P_max
        res = 0
        break
    elif (res < p1.P_max):
        result_df.at[index, 'In_as'] = result_df.at[index, 'B']
        result_df.at[index, 'P_as'] = p1.P_mid
        res = res - p1.P_mid
    elif (index >= len(result_df)-1):
        result_df.at[index, 'In_as'] = result_df.at[index, 'C']
        result_df.at[index, 'P_as'] = p1.P_max
        res = res - p1.P_max
        break
    elif ((result_df.at[index, 'B'] + result_df.at[index+1, 'B'])/(p1.P_max + p1.P_min) > (result_df.at[index, 'C'])/p1.P_max):
        result_df.at[index, 'In_as'] = result_df.at[index, 'B']
        result_df.at[index, 'P_as'] = p1.P_mid
        res -= p1.P_mid
    else:
        result_df.at[index, 'In_as'] = result_df.at[index, 'C']
        result_df.at[index, 'P_as'] = p1.P_max
        res = res - p1.P_max



    if (res < 0):
        raise ValueError("reservoir cannot be smaller than 0!")




    #print("p1.income_as = " + str(p1.income_as)+ " index = " + str(index) + "P = " + str(row['P_as']) + " S = " + str(row['In_as']) + " reservoir = " + str(res))

#print("calculating as")
#print(result_df)



#order the result table
result_df = result_df.sort_values(by=['C', 'B'], ascending=False)
result_df = result_df.reset_index(drop=True)



res = p1.reservoir

for index, row in result_df.iterrows():
    if (index >= len(result_df)):
        break
    #print("test")
    if (res < p1.P_min):
        break
    elif (res <= p1.P_max):
        result_df.at[index, 'In_el'] = p1.priceFunction(res, row['S_el'], row['S_prl'])
        result_df.at[index, 'P_el'] = res
        res = 0
    else:
        result_df.at[index, 'In_el'] = row['C']
        result_df.at[index, 'P_el'] = p1.P_mid
        res -= p1.P_max

    if (res < 0):
        raise ValueError("reservoir cannot be smaller than 0!")



    #print("p1.income_el = " + str(p1.income_el)+ "index = " + str(index) + " P_el = " + str(row['P_el']) + " In_el = " + str(row['In_el']) + " reservoir = " + str(res))


#print("calculating electricity")
#print(result_df)

result_df = result_df.sort_values(by=['time_start'], ascending=True)
result_df = result_df.reset_index(drop=True)

#print("rearranging colomn")
#print(result_df)

result_df["res_el"] = np.zeros(len(result_df))
result_df["res_as"] = np.zeros(len(result_df))
result_df.at[0, 'res_el'] = p1.reservoir
result_df.at[0, 'res_as'] = p1.reservoir

for index, row in result_df.iterrows():
    if(index == 0):
        continue
    if(result_df.at[index-1, 'res_as']-result_df.at[index, 'P_as'] < 0):
        break
    else:
        result_df.at[index, 'res_as'] = result_df.at[index - 1, 'res_as'] - result_df.at[index, 'P_as']

for index, row in result_df.iterrows():
    if(index == 0):
        continue
    if(result_df.at[index-1, 'res_el']-result_df.at[index, 'P_el'] < 0):
        break
    else:
        result_df.at[index, 'res_el'] = result_df.at[index - 1, 'res_el'] - result_df.at[index, 'P_el']

#print("calculating reservoir")
#print(result_df)

income_el = 0
income_as = 0

output = [[],[],[],[],[]]
for index, row in result_df.iterrows():
    output[0].append(row['time_start'])
    output[1].append(row['In_el'])
    output[2].append(row['res_el'])
    output[3].append(row['In_as'])
    output[4].append(row['res_as'])

    income_el = income_el + row['In_el']
    income_as = income_as + row['In_as']


fig, ax1 = plt.subplots(2, sharey='col')
fig.suptitle("Opportunity cost = " + str((income_as - income_el)/1000) + "kCHF", fontsize=14)


ax1[0].set_title("Income form EL only = " + str(income_el/1000) + " kCHF", fontsize=11, x=0.5, y=0.85)
ax1[0].set_xlabel('Time')
ax1[0].set_ylabel('Income from EP [EUR]',  color = 'red')
ax1[0].plot(output[0], output[1], 'r')
ax1[0].tick_params(axis ='y', labelcolor = 'red')

ax2 = ax1[0].twinx()
ax2.set_ylabel('Remaining Reservoir [MWh]', color='blue')
ax2.plot(output[0], output[2], 'b')
ax2.tick_params(axis='y', labelcolor='blue')


ax1[1].set_title("Income from PRL + EL = " + str(income_as/1000) + " kCHF",  fontsize=11, x=0.5, y=0.85)
ax1[1].set_xlabel('Time')
ax1[1].set_ylabel('Income from EP + PRL [EUR]',  color = 'red')
ax1[1].plot(output[0], output[3], 'r')
ax1[1].tick_params(axis ='y', labelcolor = 'red')

ax3 = ax1[1].twinx()
ax3.set_ylabel('Remaining Reservoir [MWh]', color='blue')
ax3.plot(output[0], output[4], 'b')
ax3.tick_params(axis='y', labelcolor='blue')


plt.show()









