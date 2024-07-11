# ES_Assessment
This is the repo I used for Ecosystem Services Assessment.
The ES assessment model includes following indicators:
   1. Temperature regulation
   2. Water flow regulation
   3. Air Quality
   4. Carbon Storage
   5. Carbon Sequestration

# Assessment Framework
**The Assessment is based on the frame work built by Anna Porucznik**

Ecosystem Services and indicator description

| Ecosystem Services     | Indicator                    | Description                                                             | Unit    |
| ---------------------- | ---------------------------- | ----------------------------------------------------------------------- | ------- |
| Temperature Regulation | Cooling Capacity/Temperature | Potential of an area to mitigate heat during a single heat wave         | °C      |
| Water Flow Regulation  | Runoff                       | Amount of water transformed into runoff after a 24 hr event of rain     | mm      |
| Air Quality            | PM 10 Deposition             | Particulate matter amount deposited in vegetation per year              | µg/m2   |
| Carbon Storage         | Carbon Stored in Vegetation  | Carbon stored in above ground vegetation and roots                      | kg/m2   |
| Carbon Sequestration   | Carbon Sequestration Rate    | Amount of carbon sequestrated into vegetation annually (per LULC class) | g/m2 /y |

## Temperature Regulation
Cooling capacity can be calculated as follows:

\[ CC = 0.6 \cdot \text{shade} + 0.2 \cdot \text{albedo} + 0.2 \cdot \text{ETI} \tag {1} \]

\[ \text{ETI} = \frac{K_c \cdot ET_0}{ET_{\text{max}}} \tag {2} \]

where 𝑠ℎ𝑎𝑑𝑒 and 𝑎𝑙𝑏𝑒𝑑𝑜 represent, respectively, the proportion of canopy and proportion of solar radiation of each LULC class and are assigned values between 0 and 1. The 𝐸𝑇𝐼, the evapotranspiration index, is calculated as in Formula 2, where 𝐸𝑇 0 is the reference evapotranspiration, while 𝐸𝑇𝑚𝑎𝑥 is the maximum value of 𝐸𝑇0 on a given site. The weighting (0.6, 0.2, 0.2) follows recommendations of the inVEST software user guide (Natural Capital Project, 2023).

Furthermore, the expected air temperature across the sites was modelled as in the Equation 3, where 𝑇 𝑎𝑖𝑟 𝑛𝑜𝑚𝑖𝑥 is the air temperature of each pixel without air mixing, 𝑇 is the rural reference temperature and 𝑈𝐻𝐼 𝑚𝑎𝑥 is the UHI intensity or the maximum urban heat island effect observed on each site. The latter has been derived as a difference between the maximum air temperature observed in an urban area around each site during a recent heatwave,𝑇 𝑎𝑖𝑟 𝑚𝑎𝑥, and an average air temperature in a surrounding rural area on the same day (Equation 4). Finally, to account for air mixing, 𝑇 𝑎𝑖𝑟 , was derived from the 𝑇 𝑎𝑖𝑟 𝑛𝑜𝑚𝑖𝑥 using a Gaussian function with a kernel radius of 10m (Martini et al., 2018).


\[ T_{\text{air nomix}} = T_{\text{air, ref}} + (1 - CC) \cdot UHI_{\text{max}} \tag {3}\]

\[ UHI_{\text{max}} = T_{\text{air, max}} - T_{\text{air, ref}} \tag {4}\]

**Table 1: Input Variables and Their Parametrizations**
| Input Variable                | Symbol | Unit  | Parametrization                                                                                                                                       | Data Source                                                                                                                                              |
|-------------------------------|--------|-------|--------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| Evapotranspiration            | ET₀    | mm    | Grass Reference ET at 30x30 m resolution; Landsat image (id:LE72050312023235ASN00) taken on 23/08/2023 with 29% cloud coverage                         | EEFlux Platform [https://eeflux-level1.appspot.com](https://eeflux-level1.appspot.com) (Allen et al., 2015)                                               |
| Crop Coefficient              | Kc     | ratio | Calculated based on comparative studies; for Pavement_50, an average of Kc of grass and Pavement; for Green_Roof, the Kc of Grass                      | Appendix A.1.3                                                                                                                                           |
| Albedo                        | -      | ratio | The proportion of solar radiation that is directly reflected by this LULC class; within the range suggested by the Local Climate Zones (LCZ)           | Appendix A.1.3; Local Climate Zones (Stewart & Oke, 2012)                                                                                                |
| Shade                         | -      | ratio | Proportion of area shaded by tree canopy per LULC class, based on comparative studies                                                                  | Appendix A.1.3                                                                                                                                           |
| Reference Air Temperature     | Tₐᵢᵣ,ᵣₑ𝒻   | °C    | As in Veerkamp et al. (2023): average temperature registered across multiple rural weather stations around Porto on the 22/08/2023; 33.3°C             | Wunderground.com                                                                                                                                         |
| UHI Intensity                 | UHIₘₐₓ | °C    | Difference between the Tₐᵢᵣ,ᵣₑ𝒻 and the maximum temperature registered in the urban area of Porto on the 22/08/2023; 6.7°C                            | Wunderground.com                                                                                                                                         |
| Air Blending Distance         | -      | m     | Radius over which to average air temperatures to account for air mixing; 10m                                                                           | Natural Capital Project (2023); Martini et al. (2018)                                                                                                     |

## Water Flow Regulation
\[ Q = \frac{(P - 0.05S_{0.05})^2}{P + 0.95S_{0.05}} \tag{5} \]  
\[ S_{0.05} = 1.33S_{0.20}^{1.15} \tag{6} \]
\[ S_{0.20} = \frac{1000}{CN} - 10 \tag{7} \]

where 𝑄 is the amount of runoff, 𝑃 is precipitation, 𝑆 0.05and 𝑆 0.20are a site index and 𝐶𝑁 is the curve number. The latter is a value ranging from 0 to 100, assigned based on the LULC category of the assessed area/pixel and its Hydrological Soil Group (HSG) (Cronchey, 1986).

**Table: Parameters used to run the Water Flow Regulation ES model on all sites.**

| Input Variable            | Symbol | Unit   | Parametrization                                                                                                                                         | Data Source                           |
|---------------------------|--------|--------|----------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| Hydrological Soil Group   | HSG    | A - D  | Global HSGs gridded dataset at 250-m resolution in GeoTIFF format. HSG-C for Porto, Paris and Florence.                                                  | Ross et al. (2018)                    |
| Curve Numbers             | CN     | -      | Curve number for urban areas; value per LULC class with a corresponding site-specific HSG; CN for extensive Green Roofs assumed for dry soil and slope of 7% | USDA Cronshey (1986) <br> For Green Roofs: Berndtsson (2010) |
| Precipitation             | P      | mm (kg/m²) | Maximum 1-day precipitation per site aggregated yearly; gridded dataset at 0.1° x 0.1° resolution, spatially aggregated to NUTS level 3                    | E-OBS Total Precipitation Amount <br> Mercogliano et al. (2021) |

## Air Quality
\[ \text{Deposited Amount} = \text{LAI} \cdot v_d \cdot C \cdot t \tag{8} \]

where the \(\text{Deposited Amount}\) is the amount of PM\(_{10}\) particles deposited on vegetation, \(\text{LAI}\) is the Leaf Area Index, \(v_d\) is the deposition velocity, \(C\) is the concentration of PM\(_{10}\) in the local air, and \(t\) is the time during which the given type of vegetation is in/off season.

**Table 5: Parameters used to run the Air Quality ES model on all sites.**

| Input Variable       | Symbol | Unit   | Parametrization                                                                                                                                             | Data Source                                    |
|----------------------|--------|--------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------|
| PM\(_{10}\) Concentration  | C      | µg/m³  | 90.4 percentile of daily mean PM10 concentrations per site (maximum value)                                                                                   | Europe’s Air Quality Status 2023 <br> European Environmental Agency (2023)          |
| Leaf Area Index      | LAI    | -      | LAI value for tree crown radius of 7m, 4.95m and 2.45m respectively: 6.3, 4.45 and 2.6, as presented in various studies across Europe                         | Šrámek & Čermák (2012)                         |
|                      |        |        | LAI value for evergreen Shrubs <0.5m: 1.92                                                                                                                   | Sonnentag et al. (2007)                        |
|                      |        |        | LAI value for grass at 10cm height: 0.5                                                                                                                      | Byrne et al. (2005)                            |
|                      |        |        | LAI of Green_Roof assumed equal to Grass; LAI of Pavement_50 assumed equal to 0.25 (or half-Grass)                                                           | -                                              |
| Deposition Velocity  | v_d    | m/s    | 0.0064 for in-leaf season (0.0014 for off-leaf season)                                                                                                       | Nowak et al. (1998)                            |
| Time off/in-season   | t      | month  | 7 for in-leaf season and 5 for off-leaf season; 12 months for grass; 12 months for shrub                                                                     | Selmi et al. (2016)                            |


## Carbon Storage

The equations can be represented in LaTeX as follows:

\[ C_{sto} = \text{Veg.Vol} \cdot \text{Density of Biomass} \cdot \left( 1 + \frac{\text{Root}}{\text{Shoot}} \right) \cdot \text{C content} \tag{9} \]

where \( C_{sto} \) is the amount of carbon stored per m\(^2\) of vegetation, \( \text{Veg.Vol} \) is the vegetation volume, \( \text{Density of Biomass} \) is standing dry biomass per unit volume, \( \frac{\text{Root}}{\text{Shoot}} \) is the root to shoot ratio, and \( \text{C content} \) is the amount of carbon in dry biomass. \( \text{Veg.Vol} \) has been calculated following Huang et al. (2013), using Formulas 10 and 11, which differentiate between the type of vegetation,

\[ \text{Veg.Vol}_{\text{grass,shrub}} = S_{g,S} \cdot H \tag{10} \]

\[ \text{Veg.Vol}_{\text{tree}} = S_{t} \cdot H \cdot K \tag{11} \]

where \( \text{Veg.Vol}_{\text{grass,shrub}} \) is the volume of grass and shrubs, \( \text{Veg.Vol}_{\text{tree}} \) is the volume of trees, \( S_{g,S} \) is the area of grass or shrub, \( S_{t} \) is the crown area of a given tree, \( H \) is the height of vegetation (tree, grass or shrub), and \( K \) is the morphological parameter. The latter allows to account for a shape of tree, which is otherwise not reflected in a two-dimensional space. Table 6 shows the parameters used to model Carbon Storage.

**Table 6: Parameters used to run the Carbon Storage ES model on all sites.**

| Input Variable       | Symbol | Unit  | Parametrization                                                                                                                                         | Data Source                           |
|----------------------|--------|-------|----------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| Vegetation Volume    | -      | m³    | Volume of tree and grass objects based on vegetation height, area and morphological parameter (shape, for trees only).                                   | Huang et al. (2013)                   |
| Morphological parameter | K      | -     | 0.5 for crown radius of 2.45m and height between 1m and 5; 0.5 for crown radius of 4.95m and height between 5m and 10m; 0.7 for crown radius of 7m and height between 1m and 10m | Huang et al. (2013)                   |
| Vegetation Height    | H      | -     | 5m for crown radius of 2.45m; 7m for crown radius of 4.95m; 10m for crown radius of 7m; 12cm for grass; 30 cm for shrubs                                 | Huang et al. (2013)                   |
| Biomass Density      | -      | kg/m³ | Standing dry biomass per unit volume (biomass packing) at around 1 kg/m³                                                                                  | Proulx et al. (2015)                  |
| Root/Shoot Value     | -      | ratio | Median plant below versus aboveground biomass distributions estimated at 0.226 for temperate broadleaf forest (Tree); at 4.224 for temperate grasslands (Grass); and at 1.063 for temperate shrubland (Shrub) | Mokany et al. (2006)                  |
| Carbon Content       | -      | kg    | Conversion factor of 0.5 from amount biomass (dry mass) to carbon in biomass, i.e. 500g of C in 1kg of dry biomass                                        | IPCC (Penman et al., 2013)            |

## Carbon Sequestration

Carbon Sequestration has been approximated using a benefit transfer method (Johnston et al., 2015). The annual carbon sequestration values per LULC type have been found in literature as detailed in Table 7.

**Table 7: Carbon sequestration values per LULC category found in scientific literature, used as a proxy for Carbon Sequestration ES estimation.**

| Input Variable            | Symbol | Unit   | Value | Parametrization                                                                                                                                                          | Data Source                  |
|---------------------------|--------|--------|-------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------|
| Carbon sequestration per LULC | C      | g/m²/y | 185   | Grass: gross C sequestration for Turfgrasses                                                                                                                              | Flude et al. (2022)          |
|                           |        |        | 180   | Tree: gross C sequestration for Urban Trees                                                                                                                               | Flude et al. (2022)          |
|                           |        |        | 201   | Shrub: gross C sequestration for Shrubs                                                                                                                                   | Flude et al. (2022)          |
|                           |        |        | 671   | Green_roof: carbon sequestration of _Z. Matrella_ species of grass, studies on extensive rooftops                                                                         | Kuronuma et al. (2018)       |
|                           |        |        | 92.5  | Pavement_50: half of the value of Grass                                                                                                                                   | -                            |
