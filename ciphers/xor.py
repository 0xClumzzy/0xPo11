#!/usr/bin/python
# XOR Cipher
# created by : Fyzz

# help menu for cipheringing process
help_menu = """
USAGE:
  key xor [FLAGS] [OPTIONS]

FLAGS:
  -d, --decrypt  Decrypt input text or file
  -e, --encrypt  Encrypt input text or file

OPTIONS:
  -i, --inputFile <input file>  Input file to encrypt or decrypt
  -o, --output <output file>    Output file for encrypted or decrypted text
  -t, --text <text>             Input text to encrypt or decrypt
  -k, --key <key>               Encryption key

EXAMPLES:
  key xor -e -t "hello" -k key
"""

def encode(input):
    key = input.key
    text = input.text

    if key and text:
        output = " ".join([chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text)])
        return [output, True]
    else:
        return ["Please provide -k <key> argument", False]

def decode(input):
    key = input.key
    text = input.text

    if key and text:
        text = text.replace(" ", "")
        output = " ".join([chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text)])
        return [output, True]
    else:
        return ["Please provide -k <key> argument", False]

