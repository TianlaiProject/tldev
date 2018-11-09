# Heating system controller

Python code to controll the water heating system in Tianlai station house.

This is still a raw version. I will rewrite the whole code in the future.

## Usage

*Power on:*

`python heating_system.py poweron`

Once powered on, the highest temperature would be limited to 45 Celcius degree by the heating system itself.

*Power off:*

`python heating_system.py poweroff`

Automatically power off after some time:

`python timer.py [second]`

Note that the time unit is second.
