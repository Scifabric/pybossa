#! /usr/bin/env bash

# check python version, should be over 2.7
ret=`python -c 'import sys; print("%i" % (sys.hexversion<0x02060000))'`
if [ $ret -eq 0 ]; then
    echo "Required version of Python already installed."

else 
    echo "You need to install Python 2.7.X"
    echo -e "Install Python 2.7.3? [y/n] \c "
    read word
    if [ $word == "y" ]; then
       if [ "$(whoami)" != "root" ]; then
          echo "You need root access"
          exit 1
       fi
       # echo "You said yes"
       echo `wget http://python.org/ftp/python/2.7.3/Python-2.7.3.tar.bz2`
       echo `tar xf Python-2.7.3.tar.bz2`
       cd Python-2.7.3
       echo `./configure --prefix=/usr/local`
       echo `make && make altinstall`
       echo `rm Python-2.7.3.tar.bz2`
     else
       echo "Aborting installation script."
       exit 1
    fi
fi

echo "Testing whether virtualenv is installed..."
# test whether virtualenv is installed
ve=`command -v virtualenv`
if [ -z "$ve" ]; then
   echo "You need to install virtualenv?"
   echo -e "Install virtualenv? [y/n] \c "
   read word
   if [ $word == "y" ]; then
      echo "This will install virtualenv in your home directory"
      if [ "$(whoami)" != "root" ]; then
         echo "You need root access"
         exit 1
      fi
      echo "Installing virtualenv..."
      currdir=`pwd`
      cd $HOME
      echo `curl -O https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.10.1.tar.gz`
      echo `tar xvfz virtualenv-1.10.1.tar.gz`
      cd virtualenv-1.10.1
      echo `python setup.py install`
      cd $currdir
   fi
fi
# start virtual env and install flask
echo `virtualenv -p python venv`
currentDir=`pwd`
virtualenvPath='venv/bin/activate'
source $currentDir/$virtualenvPath 

pip install -r requirements.txt
echo "Installation complete."
