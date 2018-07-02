import pyembroidery.EmbThread as EmbThread
import pyembroidery.ReadHelper as helper


def read_vp3_string_16(stream):
    # Reads the header strings which are 16le numbers of size followed by utf-16 text
    string_length = helper.read_int_16be(stream)
    return helper.read_string_16(stream, string_length)


def read_vp3_string_8(stream):
    # Reads the body strings which are 16be numbers followed by utf-8 text
    string_length = helper.read_int_16be(stream)
    return helper.read_string_8(stream, string_length)


def skip_vp3_string(stream):
    string_length = helper.read_int_16be(stream);
    stream.seek(string_length, 1);


def signed32(b):
    b = b & 0xFFFFFFFF;
    if b > 0x7FFFFFFF:
        return - 0x100000000 + b;
    else:
        return b


def signed16(b0, b1):
    b0 = b0 & 0xFF
    b1 = b1 & 0xFF;
    b = (b0 << 8) | b1
    if b > 0x7FFF:
        return - 0x10000 + b;
    else:
        return b


def read(f, read_object):
    b = f.read(6)
    # magic code: %vsm%\0
    skip_vp3_string(f)  # "Produced by     Software Ltd"
    f.seek(7, 1)
    skip_vp3_string(f)  # "" comments and note string.
    f.seek(32, 1)
    center_x = (signed32(helper.read_int_32be(f)) / 100);
    center_y = -(signed32(helper.read_int_32be(f)) / 100);
    f.seek(27, 1)
    skip_vp3_string(f)  # ""
    f.seek(24, 1)
    skip_vp3_string(f)  # "Produced by     Software Ltd"
    count_colors = helper.read_int_16be(f)
    for i in range(0, count_colors):
        colorblock = vp3_read_colorblock(f, read_object, center_x, center_y)


def vp3_read_colorblock(f, read_object, center_x, center_y):
    bytescheck = f.read(3);  # \x00\x05\x00
    distance_to_next_block_050 = helper.read_int_32be(f)
    block_end_position = distance_to_next_block_050 + f.tell();

    start_position_x = (signed32(helper.read_int_32be(f)) / 100);
    start_position_y = -(signed32(helper.read_int_32be(f)) / 100);
    abs_x = start_position_x + center_x
    abs_y = start_position_y + center_y;
    if abs_x != 0 and abs_y != 0:
        read_object.move_abs(abs_x, abs_y)
    thread = vp3_read_thread(f)
    read_object.add_thread(thread)
    f.seek(15, 1);
    bytescheck = f.read(3);  # \x0A\xF6\x00
    stitch_byte_length = block_end_position - f.tell();
    stitch_bytes = helper.read_signed(f, stitch_byte_length)

    i = 0
    ended = False;
    while i < len(stitch_bytes) - 1:
        x = stitch_bytes[i]
        y = stitch_bytes[i + 1]
        i += 2;
        if (x & 0xFF) == 0x80:
            if y == 0x01:
                x = signed16(stitch_bytes[i], stitch_bytes[i + 1])
                i += 2
                y = signed16(stitch_bytes[i], stitch_bytes[i + 1])
                i += 2
                if abs(x) > 255 or abs(y) > 255:
                    read_object.trim(0, 0)
                    read_object.move(x, y)
                else:
                    read_object.stitch(x, y)
            elif y == 0x02:
                pass  # ends long stitch mode.
            elif y == 0x03:
                read_object.end(0, 0);
                return
        else:
            read_object.stitch(x, y)
    read_object.trim(0, 0)
    read_object.color_change(0, 0)


def vp3_read_thread(f):
    thread = EmbThread.EmbThread()
    colors = helper.read_int_8(f);
    transition = helper.read_int_8(f);
    for m in range(0,colors):
        thread.color = helper.read_int_24be(f)
        parts = helper.read_int_8(f);
        color_length = helper.read_int_16be(f)
    thread_type = helper.read_int_8(f)
    weight = helper.read_int_8(f)
    thread.catalog_number = read_vp3_string_8(f)
    thread.description = read_vp3_string_8(f)
    thread.brand = read_vp3_string_8(f)
    return thread;