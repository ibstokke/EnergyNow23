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
3. [Selection Algorithm]

For calculation application uses datasets:
- [EPEX Spot Market D-1 Hourly Prices](https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show?name=&defaultValue=true&viewType=TABLE&areaType=BZN&atch=false&dateTime.dateTime=02.12.2023+00:00|CET|DAY&biddingZone.values=CTY|10YCH-SWISSGRIDZ!BZN|10YCH-SWISSGRIDZ&resolution.values=PT60M&dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2))
- [Swissgrid Auction Results for Control Power](https://www.swissgrid.ch/en/home/customers/topics/ancillary-services/tenders.html)


## Electricity Production Only <a name="ElProd"></a>

### Assumptions:
- Fixed operating cost of a power plant. This value does not vary between the operation modes and therefore is not considered for calculations​
- Reservoir is constant for the year​. No inflow/losses.
- Using datasets from the past: possible to use simulations about the  future prices​
- No inflation

Operating Capacity P can be freely choosen between P<sub>min</sub> < P < P<sub>max</sub> with resolution of 1MW: 

![Screenshot](FigurePlots/ElProd.png)

The prices of electricity S<sub>el</sub> vary on hourly basis. For each hour the income from the electricity production is $$P_{el} = S_{el} * P $$
, where we can freely adjust $P$:

![Screenshot](FigurePlots/ElIncome.png)

## Electricity Production and Primary Control Reserves <a name="PRL"></a>

### Assumptions
- ONE price for Primary Control Reserves (PRL): price-as-clear: highest accepted bidder sets the price.
- While offering PRL, the downwards and upwards regulation contribute equally. While operating at given capacity $P$ those contributions add up to zero: no reservoir is used up.

PRL regulation is symmetric. The maximal PRL capacity that can be offered is given by the minimal difference between the operating capacity and either maximal and minimal capcity: 

![Screenshot](FigurePlots/PRLProd.png)

With given price for PRL $S_{PRL}, thehe maximal income from PRL at given capacity P is described by the expression $P_{PRL} \cdot max(P-P_{min}, P_{max}-P)$.

**As no reservoir is used up, it is always most profitable to offer maximal PRL capacity whenever possible**

The total income is given by the sum electricity production and primary control reserves:
$$S_{PRL} =  S_{el} * P_{el} + S_{PRL} \cdot max(P-P_{min}, P_{max}-P)$$


![Screenshot](FigurePlots/PRLIncome.png)



