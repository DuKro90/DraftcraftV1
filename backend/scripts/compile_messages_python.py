"""
Python-only message compiler (no gettext needed).
Compiles .po files to .mo files using pure Python.
"""

import os
import struct
import array

def generate_mo_file(po_file_path, mo_file_path):
    """
    Convert .po file to .mo file using pure Python.
    Based on msgfmt.py from Python Tools.
    """
    print(f"Compiling: {po_file_path}")

    # Read .po file
    with open(po_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Parse .po file
    messages = {}
    msgid = None
    msgstr = None

    for line in lines:
        line = line.strip()

        if line.startswith('msgid '):
            if msgid and msgstr:
                messages[msgid] = msgstr
            msgid = line[7:-1]  # Remove 'msgid "' and '"'
            msgstr = None

        elif line.startswith('msgstr '):
            msgstr = line[8:-1]  # Remove 'msgstr "' and '"'

        elif line.startswith('"') and msgid and msgstr is None:
            # Continuation of msgid
            msgid += line[1:-1]

        elif line.startswith('"') and msgid and msgstr is not None:
            # Continuation of msgstr
            msgstr += line[1:-1]

    # Add last message
    if msgid and msgstr:
        messages[msgid] = msgstr

    # Remove empty msgid (header)
    if '' in messages:
        del messages['']

    print(f"  Found {len(messages)} translations")

    # Generate .mo file
    keys = sorted(messages.keys())
    offsets = []
    ids = []
    strs = []

    for key in keys:
        ids.append(key.encode('utf-8'))
        strs.append(messages[key].encode('utf-8'))

    # Calculate offsets
    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart + sum(len(k) + 1 for k in ids)

    # Build .mo file
    koffsets = []
    voffsets = []

    for i, (k, v) in enumerate(zip(ids, strs)):
        koffsets.append((len(k), keystart))
        keystart += len(k) + 1
        voffsets.append((len(v), valuestart))
        valuestart += len(v) + 1

    # Write .mo file
    with open(mo_file_path, 'wb') as f:
        # Magic number
        f.write(struct.pack('I', 0x950412de))
        # Version
        f.write(struct.pack('I', 0))
        # Number of entries
        f.write(struct.pack('I', len(keys)))
        # Offset of table with original strings
        f.write(struct.pack('I', 7 * 4))
        # Offset of table with translation strings
        f.write(struct.pack('I', 7 * 4 + len(keys) * 8))
        # Size of hashing table (not used)
        f.write(struct.pack('I', 0))
        # Offset of hashing table (not used)
        f.write(struct.pack('I', 0))

        # Write table with offsets for original strings
        for length, offset in koffsets:
            f.write(struct.pack('I', length))
            f.write(struct.pack('I', offset))

        # Write table with offsets for translated strings
        for length, offset in voffsets:
            f.write(struct.pack('I', length))
            f.write(struct.pack('I', offset))

        # Write original strings
        for k in ids:
            f.write(k + b'\x00')

        # Write translated strings
        for v in strs:
            f.write(v + b'\x00')

    print(f"  Created: {mo_file_path}")
    print()

def main():
    """Compile all .po files in locale directory."""
    print("=" * 60)
    print("Python-only Message Compiler")
    print("=" * 60)
    print()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    locale_dir = os.path.join(base_dir, 'locale')

    if not os.path.exists(locale_dir):
        print("ERROR: locale directory not found!")
        return

    compiled_count = 0

    # Find all .po files
    for lang in os.listdir(locale_dir):
        lang_dir = os.path.join(locale_dir, lang, 'LC_MESSAGES')
        if not os.path.exists(lang_dir):
            continue

        po_file = os.path.join(lang_dir, 'django.po')
        if not os.path.exists(po_file):
            continue

        mo_file = os.path.join(lang_dir, 'django.mo')

        try:
            generate_mo_file(po_file, mo_file)
            compiled_count += 1
        except Exception as e:
            print(f"ERROR compiling {po_file}: {e}")

    print("=" * 60)
    print(f"SUCCESS! Compiled {compiled_count} message files.")
    print("=" * 60)
    print()
    print("Next: Restart Django server and test language switching!")
    print()

if __name__ == '__main__':
    main()
