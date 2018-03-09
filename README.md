# OrderEdit
An internal skill order list editor for Etrian Odyssey III. Capable of extracting an existing order list from an EO3 arm9.bin, and of inserting a new one into arm9.bin, as well as rearranging npc_char.tbl to match the new order.

# Needed Files
* **arm9.bin**: The game's primary executable. Must be decompressed. Used for both parse mode (spits out the current order inside the game) and insert mode (inserting a new order into the game). 
* **npc_char.tbl**: The Sea Quest NPC table. Contains skill assignments for each NPC, which need to be updated when messing with skill order using insert mode.

# Optional Files
* You can provide an ASCII list of skill names, using whatever filename you want, when using parse mode. This will add comments to the resulting file that denotes the name of the skill being referenced for that assignment.

# Launch Options
To view the launch options, simply run OrderEdit without any arguments.
