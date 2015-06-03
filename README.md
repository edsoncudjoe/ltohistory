# ltohistory
A tool to report total amounts of data archived to LTO

------------
Introduction
------------

This tool was designed to collect information on the amount of archiving storage held for clients. There currently isn't a way to produce this info from either CatDV or GBlabs software so this program acts as a link between the two.

Ltohistory collects individual barcode numbers from our LTO tapes
and the storage information of files that have been written to LTO. It then separates the data for each client and adds up the total archived storage space.

Inputs: GBLabs exported 'history' file. Both CSV and JSON files can be used as input. The program will collect the Intervideo barcode numbers and size of each LTO tape from these files. 
There is also the choice of accessing the CatDV database or manually opening text files to collect client barcode information.

Outputs: Result data is printed to the CLI. There is an option to output barcode numbers and LTO tape sizes to a CSV file.

------------
Requirements
------------

The following python built-in modules are required:

csv,
json,
re,
sys,
time,
tkFileDialog,
Tkinter

-------------------
Recommended modules
-------------------

To access the CatDV database the module CatDVlib is required.

https://github.com/edsoncudjoe/Py-CatDV

------------
Installation
------------

This program and the CatDV library should copied to the same location.

-----------
Maintainers
-----------

Edson Cudjoe 

----
TODO
----

Create a GUI.
