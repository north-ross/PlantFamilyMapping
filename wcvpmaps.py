# This scipt downloads and processes the World Checklis of Vascular Plants (WCVP) data from 
# Plants of the World Online (POWO), Kew Gardens, and associated shapefiles for botanical country boundaries
# It creates a map of species richness by botanical country for a given family, suitable for upload to its Wikipedia page

# import requests
from zipfile import ZipFile
import os
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mapclassify
from matplotlib.colors import  ListedColormap
from urllib.request import urlretrieve
import cartopy.crs as ccrs

def download_data(): 
    """Downloads and extracts the zip files containing shapefile map data and plant checklist
    """
    # Create data folder if it doesn't exist
    os.makedirs("data", exist_ok=True)

    # Download
    wgsrpd_url = "https://github.com/tdwg/wgsrpd/archive/master.zip"
    filename = "data/master.zip"
    if not os.path.exists(filename):
        urlretrieve(wgsrpd_url, filename)
        print(f'Downloaded {filename}')

    # Extract
    with ZipFile(filename) as zf:
        zf.extractall("data")


    # Download data from WCVP https://sftp.kew.org/pub/data-repositories/WCVP/wcvp.zip
    # Import data from world vascular plant checklist
    wcvp_url = "https://sftp.kew.org/pub/data-repositories/WCVP/wcvp.zip"
    filename = "data/wcvp.zip"
    if not os.path.exists(filename):
        urlretrieve(wcvp_url, filename)
        print(f'Downloaded {filename}')

    with ZipFile(filename) as zf:
        zf.extractall("data")

# Load data to memory
world = gpd.read_file("data/wgsrpd-master/level3/level3.shp")
# world = world.to_crs("ESRI:54030")

# WCVP dataframe of plant names
df = pd.read_csv("data/wcvp_names.csv", sep="|")
# WCVP dataframe of plant distributions
ddf = pd.read_csv("data/wcvp_distribution.csv", sep="|")

def SRMapFromFamily(family, df=df, ddf=ddf, world=world, nbreaks=10, custom_breaks=None, custom_labels=None):
    """Creates a map of species richness by botanical country for the given plant family. 
        By default uses natural breaks, but custom breaks (ten) can be supplied as well

    Args:
        family (str): Plant family from WCVP database, e.g. "Orchidaceae".
        df (pandas.DataFrame, optional): Pandas dataframe of plant names, from WCVP
        ddf (pandas.DataFrame, optional): Pandas dataframe of plant distributions, from WCVP
        world (geopandas.GeoDataFrame, optional): GeoDataFrame of botanical countries
        nbreaks (int, optional): number of breaks for the legend
        custom_breaks (list, optional): List of n breakpoints to use instead of natural breaks plus zero. Defaults to None.
        custom_labels (list, optional): List of strings to use as custom labels in the legend. 
    """
    # Get list of accepted species in family
    species = df.loc[(df['family']==family) & (df['taxon_status']=="Accepted") & (df['taxon_rank']=="Species")]
    # Most common climate description for this family
    modal_climate = species.climate_description.mode()[0]
    print(f"Most common climate for {family}: {modal_climate}")
    # Now filter the distributions df to only include native plants from our query
    species_ids = species['plant_name_id'].unique()
    family_ddf = ddf[(ddf['plant_name_id'].isin(species_ids)) & (ddf['introduced']==0)]

    # Group this to just get a count of unique plant_name_ids in each area_code_l3
    sr = family_ddf[['area_code_l3', 'plant_name_id']].groupby('area_code_l3').nunique()

    # Combine with shp
    srworld = world.merge(sr, how='left', left_on="LEVEL3_COD", right_on="area_code_l3").fillna(0)

    # Custom colormap to match wikipedia thematic mapping standards for "no value"=0:
    ylg = plt.get_cmap('YlGn', nbreaks)
    newcolors = ylg(np.linspace(0, 1, nbreaks))
    grey = np.array([224/256,224/256,224/256,1])
    newcolors[0,] = grey
    newcmp = ListedColormap(newcolors)

    if not custom_breaks:
        # Plot the data using natural breaks with zero in its own category
        # First get the natural breaks
        natural = mapclassify.NaturalBreaks(y=srworld["plant_name_id"], k=nbreaks-1)
        # Then create custom ones by adding zero at the start
        custom_breaks = np.insert(natural.bins, 0, 0.6)

    if not custom_labels:
        # Make some nice looking labels based on the breaks if not specified
        custom_labels = ["0", "1 - {:.0f}".format(custom_breaks[1])]
        for i in range(2, len(custom_breaks)):
            custom_labels.append("{:.0f} - {:.0f}".format(custom_breaks[i-1]+1, custom_breaks[i]))

    # Use Cartopy to avoid antimeridian issues
    fig, ax = plt.subplots(figsize=(10, 7),subplot_kw={'projection': ccrs.Robinson()})
    ax = srworld.plot(
        ax=ax, transform=ccrs.PlateCarree(),
        column="plant_name_id",
        linewidth=0.1,
        edgecolor = "#646464",
        scheme="UserDefined",
        classification_kwds={"bins": custom_breaks},
        cmap=newcmp,
        legend=True,
        legend_kwds={
            "title": f"{family}\nSpecies Richness", 
            "bbox_to_anchor":(-0.3, 0., 0.55, 0.6), 
            "labels": custom_labels,
            "fmt": '{:.0f}'}
    )

    # Set the x and y axis off and adjust padding around the subplot
    plt.axis("off")
    plt.tight_layout()
    # plt.title = f"{family} Species Richness by floristic province"
    plt.savefig(f'{family}_SR.svg')