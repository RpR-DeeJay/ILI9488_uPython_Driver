# ILI9488_uPython_Driver
A custom Driver for ILI9488 displays and integrated touch screens using the micropython programming language.

THERE ARE TWO VERSIONS:
One for the Display driver only with screens which do not have a touch screen.
One which allows the use of integrated touchscreens.
USING THE TOUCH SCREEN ON A DISPLAY WITHOUT A TOUCH SCREEN WILL FAIL TO RUN.
You can still use the non touch screen driver on a display which has one, but the touch screen will not work.

# INITIAL DISCLAIMER:
This entire project was created using chatGPT to code the large majority of the actual scripting, every script it gave me was tested using a micropython pyboard v1.1 to ensure features worked as intended, some bugs occured and were fixed as neccesary throught the process however its not impossible that some may have slipped through the cracks.

# SETUP INSTRUCTIONS
While the pure driver may be small enough to fit on the pyboards flash, additional demos and images for BMP loading will likely exceed the limit and cause memory issues, it is recommended to use a microSD card to store the scripts and assets.
Additionally it is highly recommended to use the example script first to ensure it works on your display.

The pin set up for the example scripts are as follows (it is also recommended and/or required to use these for your own scripts as well):
FOR THE LCD
    CS    -> X5
    RESET -> X3
    DC    -> X4
    SDI   -> X8
    SCK   -> X6
    LED   -> 3V3 (or PWM for dimming)
    SDO   -> disconnected (must be disconnected for the touch screen to function)
FOR THE TOUCH SCREEN
    T_CLK -> X6
    T_CS  -> X2
    T_DIN -> X8
    T_DO  -> X7
    T_IRQ -> X1
REFER TO EXAMPLE_IMAGES TO SEE THE WIRING I USED.

The touch screen demo requires a touch_calibration.py file to function
if present, it will automatically be used
if absent, it will automatically run the calibration stage and then create the file to be used in future
you can also set "FORCE_CALIBRATION" to True to force a recreation of the file even if it already exists.

# SCRIPT "COMMANDS"
To actually use the display you must use the following "commands" in your code to make the display do things:
