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


def make_plot(spectra, name, output_directory, interval=200):

    fig, ax = plt.subplots()
    fig.set_tight_layout(True)

    line, = ax.plot(spectra[1]['rp'])

    ax.set_xlabel('Pixel')
    ax.set_ylabel('ADU')

    def update(i):
        line.set_ydata(spectra[i]['rp'])
        return line, ax

    anim = FuncAnimation(fig, update, frames=np.arange(0, len(spectra)),
                         interval=interval)

    if output_directory is not None:
        anim.save(os.path.join(output_directory, '{}.gif'.format(name)),
                  dpi=200, writer='imagemagick')


def main(name='Gaia18ace', output_directory='../outputs', make_plots=False):
    """

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

    if make_plots is True:
        for alert_spectra, alert_name in spectra:
            make_plot(alert_spectra, name, output_directory)

    if len(spectra) > 1:
        all_spectra = vstack([i[0] for i in spectra])
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
