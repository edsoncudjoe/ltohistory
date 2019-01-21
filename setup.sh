mkdir tmp 
cd tmp

# install requests module
curl https://pypi.python.org/packages/16/09/37b69de7c924d318e51ece1c4ceb679bf93be9d05973bb30c35babd596e2/requests-2.13.0.tar.gz4
tar -xzf requests-2.13.0.tar
cd requests-2.13.0/
sudo python setup.py install

# install selenium
curl https://pypi.python.org/packages/f1/68/4d0990587b9495e2e15d6859a0f42faf90a3a41f12926bfde2e7647ffce2/selenium-3.4.1.tar.gz
tar -xzf selenium-3.4.1.tar
cd selenium-3.4.1/
sudo python setup.py install

# install the Chrome driver
curl https://chromedriver.storage.googleapis.com/2.29/chromedriver_mac64.zip

unzip chromedriver_mac64.zip

mv chromedriver /usr/local/bin

echo 'Dependcies have been installed'
