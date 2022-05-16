# rpi-pico-audio-player
 A very crude program to play a MIDI file on a pico, using no extra parts other than a speaker

# Use: (you might want to modify it to run on a seperate core or something to make it more useful)
open the python script, change the file paths as needed, and run the script

open the generated text file and copy the contents into midi_data.h (the entire header is generated)

compile the .uf2 file, and drag it onto the pico

the speaker is connected between ground and the selected gpio (GP17 is the default)