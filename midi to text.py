#  embarrassingly bad python code

import mido
import numpy as np
import os.path


midifilepath = 'replace with absolute input path (midi file)'
textdestpath = 'replace with absolute output path (a text file will be generated)'

mid = mido.MidiFile(midifilepath)

# msg.type, 'note_on'
# msg.note, (a number)
# msg.time, (a number, in seconds)

output_array = []
time_ac = 0  # time accumulation
length = 0


def base_wave_function(x):  # change this if you want lol
    # return np.sin(x)  # sounds boring and is too quiet
    return ((x / (np.pi / 2)) % 2) - 1


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
    f.write("// Written by hand in 28 days, https://github.com/thaumatichthys\n\nconst uint32_t midi_array[] = {")
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
            f.write(str(int(round((sine_output + 1) * 127))))
            if not x > (samples - 2):
                f.write(", ")

        f.write("\n   }")
        if not i > (128 - 2):
            f.write(",\n")
    f.write("\n};\n\n")
    f.write("const uint32_t wave_table_length = " + str(samples) + ";\n")

    print("Wave table size: " + str(int(round(samples * 128 / 1000))) + "kb (approx)")
