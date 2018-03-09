import linecache
import os
import struct
import sys

# where the common skills end and Princess starts
CLASS_SKILLS_START = 0xA

# how many skills a class has and how long a given skill block should be
SKILLS_PER_CLASS = 0x13

# the first entry's not used, but we might as well be comprehensive
ARM9_BIN_ORDER_LIST_START = 0xE7728
ARM9_BIN_ORDER_LIST_END = 0xE7904
ARM9_BIN_ORDER_LIST_LENGTH = ARM9_BIN_ORDER_LIST_END - ARM9_BIN_ORDER_LIST_START

# each entry is a halfword, so divide by two to get number of entries
NUMBER_OF_ORDER_ENTRIES = int(ARM9_BIN_ORDER_LIST_LENGTH / 2)

# where the weird extra stuff stops in npc_char.tbl
NPC_CHAR_OFFSET = 0x478

# where various things are in a given npc char block
NPC_CHAR_MAINCLASS_ID = 0x4
NPC_CHAR_SUBCLASS_ID = 0x8
NPC_CHAR_COMMON_SKILLS = 0x2A
NPC_CHAR_MAINCLASS_SKILLS = 0x32
NPC_CHAR_SUBCLASS_SKILLS = 0x45
NPC_CHAR_BOSS_ID = 0x5A

NPC_CHAR_DEFINITION_LENGTH = 0x68

# npcs only have 8 common skill entries
NPC_CHAR_COMMON_SKILL_ENTRIES = 0x8


def display_help():
    print("OrderEdit for Etrian Odyssey III")
    print("By Rea")
    print("v1.0; March 7, 2018\n")

    print("Command-line switches needed.")
    print("-p / --parse: Enables parse mode.")
    print("-i / --insert: Enables insert mode.\n")

    print("-o / --output: Parse mode: REQUIRED. Where the resulting file is written.")
    print("-n / --names: Parse mode only: OPTIONAL. Where the skill names file to be read is.\n")

    print("-os / --oldskillorder: Insert mode only: REQUIRED. Where the old skill order file to use is.")
    print("-ns / --newskillorder: Insert mode only: REQUIRED. Where the new skill order file to use is.")
    print("-a / --arm9in: Insert mode only: REQUIRED. Where arm9.bin is. arm9.bin must be decompressed.")
    print("-c / --charin: Insert mode only: REQUIRED. Where npc_char.tbl is.")
    print("-ao / --arm9out: Insert mode only: REQUIRED. Where to write the new arm9.bin to.")
    print("-co / --charout: Insert mode only: REQUIRED. Where to write the new npc_char.tbl to.")


def main():
    # eh, screw it, who's gonna notice
    if len(sys.argv) > 1:
        if '-p' in sys.argv or '--parse' in sys.argv:
            parse_mode()

        elif '-i' in sys.argv or '--insert' in sys.argv:
            insert_mode()

        else:
            display_help()


def parse_mode():
    skill_names_present = False

    # skill name list parsing
    if '-n' in sys.argv or '--names' in sys.argv:
        names_path = get_argument('n', 'names')

        if not os.path.isfile(names_path):
            print("WARNING: " + names_path + "doesn't exist or is not a file.")

    if '-o' in sys.argv or '--output' in sys.argv:
        out_name = get_argument('o', 'output')

        # keys are position in the skill list, values are the internal skill ID
        raw_bytes = {}

        with open('input/arm9.bin', 'rb') as arm9_bin:
            arm9_bin.seek(ARM9_BIN_ORDER_LIST_START)

            for i in range(0, NUMBER_OF_ORDER_ENTRIES):
                raw_bytes[i] = int.from_bytes(arm9_bin.read(2), byteorder='little')

        with open(out_name, 'w') as parsed_order:
            parsed_order.write("// Format is:\n")
            parsed_order.write("// [OrderListPosition], [InternalSkillId]\n")

            if skill_names_present:
                parsed_order.write("// Skill names are provided for convenience, but are not actually used.\n\n")

            else:
                parsed_order.write("\n")

            for order_list_position in raw_bytes.keys():
                parsed_order.write(str(order_list_position) +
                                   ", " +
                                   str(raw_bytes[order_list_position]))

                if skill_names_present:
                    parsed_order.write("\t// " +
                                       linecache.getline(names_path, raw_bytes[order_list_position] + 1).strip()
                                       + "\n")

                else:
                    parsed_order.write("\n")

    else:
        display_help()


def insert_mode():
    #<editor-fold desc="Insert mode required arguments checking.">
    if '-os' not in sys.argv and '--oldskillorder' not in sys.argv:
        print("ERROR: Old skill order file missing.\n")
        display_help()

    if '-ns' not in sys.argv and '--newskillorder' not in sys.argv:
        print("ERROR: New skill order file missing.\n")
        display_help()

    if '-a' not in sys.argv and '--arm9in' not in sys.argv:
        print("ERROR: arm9.bin input location missing.\n")
        display_help()

    if '-c' not in sys.argv and '--charin' not in sys.argv:
        print("ERROR: npc_char.tbl input location missing.\n")
        display_help()

    if '-ao' not in sys.argv and '--arm9out' not in sys.argv:
        print("ERROR: arm9.bin output location missing.\n")
        display_help()

    if '-co' not in sys.argv and '--charout' not in sys.argv:
        print("ERROR: npc_char.tbl output location missing.\n")
        display_help()
    #</editor-fold>

    old_order = get_argument('os', 'oldskillorder')
    new_order = get_argument('ns', 'newskillorder')
    arm9_in = get_argument('a', 'arm9in')
    char_in = get_argument('c', 'charin')
    arm9_out = get_argument('ao', 'arm9out')
    char_out = get_argument('co', 'charout')

    arm9_insert(arm9_in, arm9_out, new_order)
    char_insert(char_in ,char_out, old_order, new_order)


def arm9_insert(arm9_in, arm9_out, new_order_filename):
    with open(arm9_in, 'rb') as arm9_old, open(arm9_out, 'wb') as arm9_new:
        arm9_new.write(arm9_old.read(ARM9_BIN_ORDER_LIST_START))

        new_order = parse_order_file(new_order_filename)

        for i in range(0, len(new_order)):
            arm9_new.write(struct.pack("<h", new_order[i]))

        arm9_old.seek(ARM9_BIN_ORDER_LIST_END)
        arm9_new.write(arm9_old.read())


def char_insert(char_in, char_out, old_order_filename, new_order_filename):
    old_order = parse_order_file(old_order_filename)
    new_order = parse_order_file(new_order_filename)

    with open(char_in, 'rb') as old_table, open(char_out, 'wb') as new_table:
        old_table_len = os.stat(char_in).st_size
        char_entries = int((old_table_len - NPC_CHAR_OFFSET) / NPC_CHAR_DEFINITION_LENGTH)
        new_table.write(old_table.read(NPC_CHAR_OFFSET))

        for i in range(0, char_entries):
            new_table.write(old_table.read(4))
            main_class = int.from_bytes(old_table.read(4), byteorder='little')
            sub_class = int.from_bytes(old_table.read(4), byteorder='little')

            new_table.write(struct.pack('<I', main_class))
            new_table.write(struct.pack('<I', sub_class))
            new_table.write(old_table.read(0x1E))

            # logic for common skills reorganizing would go here if I felt it would be needed
            # for now, though: nah
            old_table.seek(NPC_CHAR_OFFSET + (i * NPC_CHAR_DEFINITION_LENGTH) + NPC_CHAR_COMMON_SKILLS)
            new_table.write(old_table.read(NPC_CHAR_COMMON_SKILL_ENTRIES))

            old_table.seek(NPC_CHAR_OFFSET + (i * NPC_CHAR_DEFINITION_LENGTH) + NPC_CHAR_MAINCLASS_SKILLS)
            main_assignments = []

            for j in range(0, SKILLS_PER_CLASS):
                main_assignments.append(int.from_bytes(old_table.read(1), byteorder='little'))

            old_table.seek(NPC_CHAR_OFFSET + (i * NPC_CHAR_DEFINITION_LENGTH) + NPC_CHAR_SUBCLASS_SKILLS)
            sub_assignments = []

            for j in range(0, SKILLS_PER_CLASS):
                sub_assignments.append(int.from_bytes(old_table.read(1), byteorder='little'))

            new_main_assignments = reorganize_skills(main_class, old_order, new_order, main_assignments)
            new_sub_assignments = sub_assignments

            if sub_class != 0xFFFFFFFF:
                new_sub_assignments = reorganize_skills(sub_class, old_order, new_order, sub_assignments)

            for j in range(0, len(new_main_assignments)):
                new_table.write(struct.pack('<B', new_main_assignments[j]))

            for j in range(0, len(new_sub_assignments)):
                new_table.write(struct.pack('<B', new_sub_assignments[j]))

            # there's an empty two bytes between the sub list and the boss ID. why? who the hell knows.
            new_table.write(struct.pack('<B', 0x0))
            new_table.write(struct.pack('<B', 0x0))

            old_table.seek(NPC_CHAR_OFFSET + (i * NPC_CHAR_DEFINITION_LENGTH) + NPC_CHAR_BOSS_ID)
            new_table.write(old_table.read(0xE))


def reorganize_skills(class_id, old_order, new_order, skill_assignments):
    skill_start = (SKILLS_PER_CLASS * class_id) + CLASS_SKILLS_START
    skill_end = skill_start + SKILLS_PER_CLASS

    old_class_order = old_order[skill_start : skill_end]
    new_class_order = new_order[skill_start : skill_end]
    new_skill_assignments = []

    for i in range(0, SKILLS_PER_CLASS):
        old_skill_index = old_class_order.index(new_class_order[i])
        new_skill_assignments.insert(i, skill_assignments[old_skill_index])

    return new_skill_assignments


def parse_order_file(order_file):
    # index is order ID, value is skill ID
    skill_order = []

    with open(order_file, 'r') as input_order:
        for line in input_order:
            # skip lines that are just comments or are empty
            if line.startswith("//") or line == "\n":
                continue

            no_comment = line.split("//")[0].strip()
            order_id = int(no_comment.split(", ")[0])
            skill_id = int(no_comment.split(", ")[1].replace(", ", ""))
            skill_order.insert(order_id, skill_id)

    return skill_order


def get_argument(short, fancy):
    index = 0

    if '-' + short in sys.argv:
        index = sys.argv.index('-' + short)

    elif '--' + fancy in sys.argv:
        index = sys.argv.index('--' + fancy)

    return sys.argv[index + 1]


if __name__ == '__main__':
    main()