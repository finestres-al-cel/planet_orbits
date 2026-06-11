
Usage instructions:
1. Open a new terminal
2. Go to planet_orbits `bin` folder:
    `cd <path to your planet_orbits repo>/bin`
2. Load your conda environment (see README.md):
    `conda activate my_planet_orbits_env`
3. Download the coordinates of your favourite planet:
    `python build_planets_catalogue.py my_catalogue.csv --planet mars`
If you want, you can specify the starting and ending dates, and the step between datapoints. To get more detail info on how the planet builder code works, type:
    `python build_planets_catalogue.py --help`
This will download data from the JPL service (https://ssd.jpl.nasa.gov/)
4. Launch `planet_orbits`:
    `python planet_orbits_app.py`
5. Open your catalogue
6. Select the planet periods (you can always change them later and return to this step)
7. Click on `find yearly series based on oppositions` and select the data series you like
8. Try different values for Earth's orbit parameters. If the orbit is correct, Your selected planet points should be closer. This is quantified by the sigma_R parameter, on the top left. Your goal is to minimize it. TIP: if you want to try other planets later, keep these parameters in your notes, as Earth's orbit should not change (though we can expect mild variations given uncertainties in the data)
9. Now that we have established Earth's orbit, we want to find the orbital parameters for your target planet. The chi^2 value given in the top left is telling you how close your orbit is following the points. Your goal is to minimize it.
10. Congratulations! you have rediscovered your favourite planet's orbit. You may now try a different planet and see if you can also find Keplers 3rd law!