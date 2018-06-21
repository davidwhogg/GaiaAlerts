import os
import bs4
import sys
import warnings

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import astropy.utils.data as aud
from astropy.table import Table, hstack, vstack
from astropy.io.ascii import InconsistentTableError


def get_data(name, output_directory):

    baseurl = 'http://gsaweb.ast.cam.ac.uk/alerts/alert'

    content = aud.get_file_contents("{}/{}".format(baseurl, name), cache=True)
    htmldoc = bs4.BeautifulSoup(content, 'html5lib')

    for line in htmldoc.strings:
        if 'var spectra' in line:
            spectra_data = line.split('=')[1].strip()

            spectra_data = Table(eval(spectra_data[1:-2]))

    try:
        spectra_meta = Table.read(content, format='ascii.html')
    except InconsistentTableError:
        if "Not found" in content:
            warnings.warn("data is not found for {}, check whether it's a "
                          "valid GaiaAlerts object".format(name))
            return None
    spectra = hstack([spectra_meta, spectra_data], join_type='outer')

    spectra['Name'] = name

    if output_directory is not None:
        spectra.write(os.path.join(output_directory, '{}.fits'.format(name)),
                      overwrite=True)

    return spectra


def make_plot(spectra, name, output_directory, interval=400):

    # To be less sensitive to extreme outliers, we set the maximum values
    # based on the median

    max_b = np.median(np.max(spectra['bp'], axis=1)) * 2
    max_r = np.median(np.max(spectra['rp'], axis=1)) * 2

    fig, ax = plt.subplots(2, 1)
    fig.set_tight_layout(True)
    ax[0].set_title(name)

    date_text = ax[0].text(0.02, 1.05, '', transform=ax[0].transAxes)

    line_b, = ax[0].plot(spectra[1]['bp'], color='b')
    line_r, = ax[1].plot(spectra[1]['rp'], color='r')

    line = [line_b, line_r]

    ax[0].set_ylim(-0.1 * max_b, max_b)
    ax[1].set_ylim(-0.1 * max_b, max_r)

    ax[0].axhline(0., color="k", alpha=0.5, zorder=-10.)
    ax[1].axhline(0., color="k", alpha=0.5, zorder=-10.)

    ax[1].set_xlabel('Pixel')
    ax[0].set_ylabel('Bp flux (Gaia units)')
    ax[1].set_ylabel('Rp flux (Gaia units)')

    def update(i):
        line_b.set_ydata(spectra[i]['bp'])
        line_r.set_ydata(spectra[i]['rp'])
        date_text.set_text('JD = {0:.2f}'.format(spectra[i]['JD']))
        return line, date_text

    anim = FuncAnimation(fig, update, frames=np.arange(0, len(spectra)),
                         interval=interval)

    if output_directory is not None:
        anim.save(os.path.join(output_directory, '{}.gif'.format(name)),
                  dpi=200, writer='imagemagick')


def main(name='Gaia18ace', output_directory='../outputs', make_plots=False):
    """
    Function to scrape Gaia spectrum data from the GaiaAlers page.

    Saves the spectroscopy data to a fits file, and optionally creates a gif
    animation.

    Parameters
    ----------
    name : str
        Name of the alert, or comma separated names of alerts.

    output_directory : str
        Name of output directory. Use None if no output is required.
        Defaults to '../outputs'. Results are overwritten.

    make_plots : bool
        If True, creates a gif animation.


    Returns
    -------
    alerts_spectra : astropy.table.Table
        A table containing the spectra data for all the valid input objects.

    """
    if output_directory is not None:
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

    spectra = []
    missing = 0

    for alert_name in name.split(','):
        alert_spectra = get_data(alert_name, output_directory)

        if alert_spectra is None:
            missing += 1
        else:
            spectra.append((alert_spectra, alert_name))

    all_spectra = vstack([i[0] for i in spectra])

    if make_plots is True:
        for alert_spectra, alert_name in spectra:
            make_plot(alert_spectra, alert_name, output_directory)

    if len(spectra) > 1:
        if output_directory is not None:
            all_spectra.write(os.path.join(output_directory,
                                           'GaiaAlertsspectra.fits'),
                              overwrite=True)

        return all_spectra

    else:
        return alert_spectra


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if 'help' in str(sys.argv[1:]):
            print("Usage of {0}:".format(os.path.basename(sys.argv[0])))
            print(main.__doc__)
        else:
            main(name=sys.argv[1])

    else:
        main()
