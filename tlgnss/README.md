# Python code for GNSS receiver

This code will read and save GNSS raw message to standard RINEX file.

Note:

1. The GNSS receiver is installed in digital room.

2. Due to hardware limitation, by now, only serial connection is supported. If to use tcp connection, some parts of the codes must be modified before running properly.


# Usage

Once powered on, you should run:

`python set_gnss.py`

to set parameters for the receiver. And then you can start recording data by:

`python tlgnss.py`

in foreground or in background (suggested):

`./run_tlgnss.sh`

To end the code, use **Ctrl+C** (if run in foreground) or `./end_tlgnss.sh` (if run background).

