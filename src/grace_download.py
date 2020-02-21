# https://earth.gsfc.nasa.gov/geo/data/grace-mascons
import os
import requests


def main(path):
    url = 'https://earth.gsfc.nasa.gov/sites/default/files/neptune/grace/mascons_2.4/GSFC.glb.200301_201607_v02.4-ICE6G.h5'
    remote_file = os.path.join(path, 'GSFC.glb.200301_201607_v02.4-ICE6G.h5')

    try:
        conn = requests.get(url)
    except BaseException:
        from requests.packages.urllib3.exceptions \
            import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(
            InsecureRequestWarning)
        conn = requests.get(url, verify=False)
    print(conn.status_code)

    with open(remote_file, 'wb') as fp:
        fp.write(conn.content)
        conn.close()


if __name__ == "__main__":
    path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(path)
    print(os.getcwd())
    
    main(path)