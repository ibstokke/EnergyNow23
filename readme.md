Download python file and extract the datasets.

You can find a .exe for win64 here: [https://drive.google.com/drive/folders/1AXrvOB1_Tahe7awww3GUY8QRZIQZaU5q?usp=drive_link]

# Ancillary Services Calculator

The aim of this application is to provide comparision of income for a power plant offering different ancillary services in Switzerland.

The application takes a simple input which can be applied to any power plant: 

- Maximal Capacity P<sub>min</sub>
- Minimal Capacity P<sub>max</sub>
- Annual Reservoir Capacity Res

And converts calculates the most profitable mode of operation using:

1. [Electricity Production only](#ElProd)
2. [Electricity Production and Primary Control Reserves](#PRL)
3. ...

For calculation application uses datasets:
- [EPEX Spot Market D-1](https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show?name=&defaultValue=true&viewType=TABLE&areaType=BZN&atch=false&dateTime.dateTime=02.12.2023+00:00|CET|DAY&biddingZone.values=CTY|10YCH-SWISSGRIDZ!BZN|10YCH-SWISSGRIDZ&resolution.values=PT60M&dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2))
- [Swissgrid Auction Results for Control Power](https://www.swissgrid.ch/en/home/customers/topics/ancillary-services/tenders.html)

## Electricity Production Only <a name="ElProd"></a>
balbla



