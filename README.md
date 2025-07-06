# __FreqScanR.py__

Is an experimental frequency scanning utility for more modern (> 2015) radios that support Yaesu CAT commands. Written by A. Del Vecchio and D. Doler K3DFD. 
Feel free to fork this repository and make useful mods/improvements. Support for Icom transceivers would be ideal. If you create new frequency lists
please share them with other Hams and especially the members of the Delaware Valley Radio Association.

--------------------------------------------------------------------------------------------------------------------------------------------------------------------
FreqScanR is a Python script designed to interface with Yaesu transceivers via CAT (Computer Aided Transceiver) control. It sequentially steps through a 
list of frequency-mode pairs, issuing the appropriate CAT commands to set the VFO frequency and operating mode for each entry. After tuning to each 
target frequency, the script holds the transceiver on that frequency for a configurable dwell time (1–5 seconds) before advancing to the next.

The scan process is interactive: pressing the spacebar toggles pause/resume, allowing the user to manually halt on interesting signals for further 
listening. FreqScanR dynamically adjusts both frequency and mode settings to match each row in the scan list, supporting flexible scanning across various
bands and services.

Additionally, individual entries in the scan list can be temporarily disabled by double-clicking on them. When disabled, the corresponding row is 
visually dimmed (displayed in gray) to indicate it is excluded from the active scan rotation. Double-clicking the entry again re-enables it, restoring 
the original text color (black) and returning the frequency to the scan cycle.

--------------------------------------------------------------------------------------------------------------------------------------------------------------------
Before using FreqScanR.py:
Download the files from this repository and place them all in the same directory. All .csv files should be in the same directory as FreqScanR.py,
freqscanr.ini and the radio .cfg file.

Assuming you have your radio connected to your PC via USB and everything works as expected, you'll need Python installed on your PC in a location that is 
in the %path% so you can double-click on python programs to run them. You will also need to install the following Python libraries either via an editor 
like Thonny or directly using PIP. See Python's instruction if you are unfamiliar with it. To work with Linux or Mac, change the code to work with 
/dev/tty* per your system.

Install tkinter, serial, datetime, numpy and pyserial

--------------------------------------------------------------------------------------------------------------------------------------------------------------------
Using FreqScanR (Read formatting the radio .cfg and frequency list .csv files section below first)*

Connect your radio and turn the power on:
Ensure your Yaesu FT-991A (or Yaesu-compatible radio) is powered on and connected to your computer via USB.

Load your radio profile:
Click the “Load Radio Profile” button and select your radio’s configuration file (.cfg). See below for the expected format.

Load a frequency list:
Click the “Open CSV” button and choose the .csv file containing the frequencies you want to scan. See below for the required format.

Set the scan delay:
Use the “Delay” dropdown to select how long the program should pause (or "dwell") on each frequency before moving to the next.

Start scanning:
Click the “Start” button to begin scanning through your frequency list. You can pause/resume scanning at any time by pressing the spacebar.

Skip frequencies on the fly:
You can double-click a frequency in the list to skip it during scanning. Skipped rows will appear in gray. Double-click again to include them back in the scan.

Stop scanning:
Click the “Stop” button to stop scanning. Note that this action does not terminate the program and the list remains displayed.

__If you change the dwell time in the delay pulldown, be sure to then click on the frequency listbox (tree control) to take the focus off of the delay. 
This is a known issue and may be fixed in the next revision. If you don't the program may not scan through the list. Just select a new delay number, click on the 
listbox and try again.__
--------------------------------------------------------------------------------------------------------------------------------------------------------------------
Formating the radio .cfg and frequency list .csv files -

There are three files required to use FreqScanR:
<radio>.cfg Example: FT991A.cfg
<freq_list>.cfg    Example: HFtime.csv
freqscanr.ini: This file is set by the program and should not be edited by the user.

The radio-specific configuration file <radio>.cfg contains 6 lines
Note: You can find these in the settings of WSJT-X or FLRig if you have used either program successfully.

Yaesu FT991A
        This is just a header for reference. FreqScanR does not read this line

PORT=COM9
    This is the name of the radio. FreqScanR does not parse this line.

BAUD=19200
    The USB Baud rate that the radio and computer communicate at

POLLINTV=500
    The polling rate used between the radio and computer.

POSTDEL=25
    The post delay rate used between the radio and computer.

STOPBITS=2
    The stop bit selected for USB communications between the radio and computer.
    
The frequency/description/mode-specific .csv file <freq_list>.cfg contains as many lines as desired

The format is <frequency in hz>,<description up to 30 characters>,<mode USB LSB AM FM CW>
For example, here's a list of HF time services contained in a simple text file called HFtime.csv:

02500000,WWV Fort Collins Colorado USA 2.5kW,AM
05000000,WWV Fort Collins Colorado USA 10kW,AM
10000000,WWV Fort Collins Colorado USA 10kW,AM
15000000,WWV Fort Collins Colorado USA 10kW,AM
25000000,WWV Fort Collins Colorado USA 2.5kW,AM

This is an experimental Python app written (mostly) by a non-Ham and may not always work as expected. If you fork a version for development, GNU General Public License v3.0 applies and please give attribution to the authors.


