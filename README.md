# cupcade-launcher
A full-screen graphical menu for Adafruit Cupcade arcade machine using Pygame

# Setup Instructions
This should be compatible with the Adafruit Cupcade iso from 05/2014 without needing to install any additional packages. 

Copy the `advmame.rc.*` files to `/boot/advmame`. The only changes are to `sound_volume`, the changes (and new `.muted` file) are for allowing global mute functionality by pressing Select/Coin at the launcher menu. 

Put files `splash.png` and `about.png` in the `/home/pi` directory, these will be displayed when `launcher.py` is loaded and when user presses Start/1P button, respectively. They should ideally be 320x240 but will scale to fit the screen if not. 

In each of the rom folders ( `/boot/fceu/rom` and `/boot/advmame/rom` ), add images (any format but preferably .png 320x240) matching the file name of the zip file for EACH rom, this will be displayed full-screen for each rom in the menu. They'll be arranged alphabetically by .zip file name. I've found "press start" title screen shots padded with black borders work very well. 

In other words, `/boot/fceu/rom` should contain `"Snake Game.zip"`, `"Snake Game.jpg"`, `"pong (homebrew).nes"`, `"pong (homebrew).png"`: one image for each rom matching the filename exactly except for extension. 

Set up `/etc/inittab` to auto-login user pi on tty1:

    1:2345:respawn:/sbin/getty --autologin pi 38400 tty1

Copy `launcher.py` to `/home/pi` and make it executable. 

Then add a line at the end of pi's `~/.bashrc` to auto-launch `launcher.py`. The following will launch only on tty1 (freeing tty3 and ssh for bug fixing) and shutdown when the user presses Esc:

    [[ $(fgconsole 2>/dev/null) -eq "1" ]] && /home/pi/launcher.py && sudo shutdown -h now
