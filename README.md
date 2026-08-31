# World Checklist of Vascular Plants Map Generator
This script makes maps of species richness of vascular plant families by botanical country, accessing data from the [World Checklist of Vascular Plants](https://powo.science.kew.org/about-wcvp). Botanical country data comes from the [World Geographical Scheme for Recording Plant Distributions](https://www.tdwg.org/standards/wgsrpd/)


# Requirements
- `geopandas`
- `urllib`
- `cartopy`

# Use
After installing the requirements using conda, import the wcvp 

# Example Usage
```py
import wcvpmaps
wcvpmaps.download_data()
wcvpmaps.SRMapFromFamily("Ericaceae")
```
See the example_notebook.ipynb for output examples.