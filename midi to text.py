#  embarrassingly bad python code

import mido
import numpy as np
import os.path


midifilepath = 'replace with absolute input path (midi file)'
textdestpath = 'replace with absolute output path (a text file will be generated)'

mid = mido.MidiFile(midifilepath)

output_array = []
time_ac = 0  # time accumulation
length = 0


def base_wave_function(x):  # change this if you want
    # return np.sin(x)  # sounds boring and is too quiet
    return ((x / (np.pi / 2)) % 2) - 1
    # return (82502.0*np.cos(1*x+0)+68385.83302489584*np.cos(2*x+0)+43466.411231295235*np.cos(3*x+2.31305899363104)+39424.03628538376*np.cos(4*x+0)+7962.086579661307*np.cos(5*x+2.184650663560032)+19400.881856593922*np.cos(6*x+1.1709989336545943)+8284.207689496003*np.cos(7*x+2.1972080146529827)+3933.5752102732195*np.cos(8*x+0)+2209.8402835306615*np.cos(9*x+0)+2525.475692742575*np.cos(10*x+0)+0) / 200000


for msg in mid:
    time_ac += msg.time
    if msg.type == 'note_on' or msg.type == 'note_off':
        value = int(round(time_ac * 1000))
        type = 1  # on
        if msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            type = 0
        value &= 0x00FFFFFF
        value |= (type << 31)
        value |= (msg.note << 24)  # b CNNNNNNNTTTTTTTTTTTTTTTTTTTTTTTT
        output_array.append(value)
        length += 1

print("Required flash size: " + str(int(length * 4 / 1000)) + "kb (approx)")


with open(textdestpath, 'w') as f:
    f.write("#include <pico/stdlib.h>\n\n")
    f.write("// Written by hand in 27.23 days, https://github.com/thaumatichthys\n\nconst uint32_t midi_array[] = {")
    f.write(" // '" + os.path.basename(midifilepath) + "'")
    for i in range(length - 1):
        if not i % 99:
            f.write("\n   ")
        f.write(str(output_array[i]) + ", ")
    f.write(str(output_array[length - 1]) + "\n};")
    f.write("\n\nconst uint32_t midi_data_length = " + str(length) + ";")

    # Now we generate the sound lookup table
    sample_rate = 25000

    min_freq = (2 ** (-69 / 12)) * 440
    duration = 1 / min_freq
    samples = int(round(duration * sample_rate))

    f.write("\n\nconst uint8_t wave_table[128][" + str(samples) + "] = {\n")

    for i in range(128):
        freq = (2 ** ((i - 69) / 12)) * 440
        f.write("   {\n       ")
        for x in range(samples):
            if (not x % 230) and (x > 220):
                f.write("\n       ")
            sine_output = base_wave_function(2 * np.pi * (freq / min_freq) * (x / samples))
            # human ears do not have a flat frequency response
            half_f = 250
            sine_output = ((1000 * half_f) / (freq + half_f)) * sine_output / 1000
            f.write(str(int(round((sine_output + 1) * 127))))
            if not x > (samples - 2):
                f.write(", ")

        f.write("\n   }")
        if not i > (128 - 2):
            f.write(",\n")
    f.write("\n};\n\n")
    f.write("const uint32_t wave_table_length = " + str(samples) + ";\n")

    print("Wave table size: " + str(int(round(samples * 128 / 1000))) + "kb (approx)")
