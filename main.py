#!/usr/bin/python
# New Arg Parse and Cipher Call
# created by : Fyzz | C0SM0 | Soul

# imports
import argparse
import importlib
import os
import shlex
import string
import sys

from colorama import Fore

import mods.bits as b

# Resolve project root (same logic as bits.py)
_main_path = os.path.dirname(os.path.abspath(__file__))


# gets list of available ciphers
def get_ciphers():
    output_list = []
    directory = os.fsencode(b.cipher)

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith('.py') and not filename.startswith('_') and filename != 'template.py':
            output_list.append(filename[:-3])

    return sorted(output_list)


# display names for the keyconsole list command
CIPHER_NAMES = {
    '1337': 'L33T Speak',
    'b64': 'Base64',
    'bin': 'Binary',
    'blowfish': 'Blowfish',
    'cc': 'Caesar Cipher',
    'cp': 'Payloads',
    'ct': 'Code Transcript',
    'hex': 'Hexadecimal',
    'hashid': 'Hash Identifier',
    'mc': 'Multiplicative',
    'md5': 'MD5 Hash',
    'mo': 'Monoalphabetic',
    'mor': 'Morse Code',
    'oct': 'Octal',
    'pho': 'Phonetic Alphabet',
    'pix': 'Image Pixel',
    'r13': 'ROT13',
    'r47': 'ROT47',
    'rc': 'Reverse Cipher',
    'sha1': 'SHA1',
    'sha224': 'SHA224',
    'sha256': 'SHA256',
    'sha384': 'SHA384',
    'sha512': 'SHA512',
    'twofish': 'Twofish',
    'url': 'URL Encoding',
    'vc': 'Vigenere Cipher',
    'xor': 'XOR Cipher',
}


# updates 0xPo11
def update():

    cmd_prefix = f'{Fore.GREEN}[~] {Fore.RESET}'
    print("\n[*] Checking for updates...")

    # get latest version number
    os.system(f"curl -s https://raw.githubusercontent.com/0xClumzzy/0xPo11/main/version.txt | tee {b.local_path}/latest.txt")

    try:
        # save version numbers to memory
        current_version = float(open(f"{b.local_path}/version.txt").read())
        latest_version = float(open(f"{b.local_path}/latest.txt").read())
    except (FileNotFoundError, ValueError):
        print("\n[!] Could not determine version (not installed)")
        return

    # remove version number file
    os.system(f"rm -f {b.local_path}/latest.txt")

    # if new version is available, update
    if latest_version > current_version:
        print("\n[+] Update found")
        print(cmd_prefix + "Update 0xPo11? [y/n]\n")

        # user input, option
        option = input(f"{b.header}")

        # update
        if option == "y":
            os.system(f"sh {b.local_path}/resources/update.sh")
    else:
        print("\n[+] 0xPo11 already up to date")


# output function
def output(data, output):
    if not data:
        return
    if data[1]:
        # file
        if output and ".png" not in output:
            with open(output, 'w') as f:
                f.write(data[0])
            print(f'{b.SUCCESS}[✓] File Output Successful{b.END}')
        # command line interface
        else:
            print(f'\n{b.SUCCESS}[✓] Output:{b.END}\n{data[0]}\n')
    else:
        # exception
        print(f'\n{b.FAIL}[✖] Failed:{b.END}\n{data[0]}\n')


# uninstalls 0xPo11
def remove():

    cmd_prefix = f'{Fore.RED}[~] {Fore.RESET}'

    # confirmation
    print("\n" + cmd_prefix + "Are you sure you want to remove 0xPo11? [y/n]\n")

    # user input
    option = input(b.header)

    # delete 0xPo11
    if option == "y":
        os.system(f"rm -rf {b.local_path}")


# builds the argument parser shared by CLI and console
def build_parser():
    parser = argparse.ArgumentParser(add_help=False, usage="")
    parser.add_argument('cipher', type=str)
    parser.add_argument('-e', '--encode', dest='encode', action='store_true')
    parser.add_argument('-d', '--decode', dest='decode', action='store_true')
    parser.add_argument('-b', '--brute', dest='brute', action='store_true')
    parser.add_argument('-i', '--inputFile', dest='inputFile', type=str)
    parser.add_argument('-ii', '--inputImage', dest='inputImage', type=str)
    parser.add_argument('-o', '--output', dest='output', type=str)
    parser.add_argument('-t', '--text', help='String Input\n', dest='text', type=str)
    parser.add_argument('-k', '--key', help='Str Key\n', dest='key', type=str)
    parser.add_argument('-s', '--salt', help='Hash Salt\n', dest='salt', type=str)
    parser.add_argument('-nc', '--nonce', help='Int Nonce\n', dest='nonce', type=int)
    parser.add_argument('-md', '--mode', dest='mode', type=str)
    parser.add_argument('-iv', dest='iv', type=str)
    parser.add_argument('-c', '--channel', dest='channel', type=str)
    parser.add_argument('-ex', '--exclude', help='Exclude Character\n', dest='exclude', type=str)
    parser.add_argument('-w', '--wordlist', help='Wordlist File\n', dest='wordlist', type=str)
    parser.add_argument('-r', '--range', help='Range\n', dest='range', type=str)
    # code transcripts
    parser.add_argument('-words', '--words', help='Filter out words\n', action='store_true')
    parser.add_argument('-lingo', '--lingo', help='Specify language ("lingo")', type=str, default='en_US')
    parser.add_argument('-a', '--alphabet', help='Specify custom alphabet\n', type=str, default=string.ascii_uppercase)
    # Layered Encryption
    parser.add_argument('-lay', '--layerd', dest='layerd', action='store_true')
    # Google Translate
    parser.add_argument('-tr', '--translate', dest='translate', action='store_true')
    parser.add_argument('-lang', '--languages', dest='lang', action='store_true')
    parser.add_argument('-src', '--src', help='Source Language code\n', dest='src', type=str)
    parser.add_argument('-dest', '--dest', help='Destination Language code\n', dest='dest', type=str)
    # Static Encryption
    parser.add_argument('-f', '--file', help="Give a file path\n", dest='file', type=str)
    parser.add_argument('-iw', '--image_width', help="Image width used for SE", dest="image_width", type=int)
    # cryptographic payloads
    parser.add_argument('-g', '--generate', help='Choose Payload Generation Method\n', dest='generate', type=str)
    parser.add_argument('-p', '--payload', help='Choose Payload\n', dest='payload', type=str)
    parser.add_argument('-wc', '--webcredentials', dest='webcredentials', action='store_true')
    return parser


# executes a parsed cipher call
def execute(args):
    # reads input files for argument parsing
    if args.inputFile:
        with open(args.inputFile) as tmpFileVar:
            args.text = tmpFileVar.read()
    # reads input file for wordlist
    if args.wordlist:
        with open(args.wordlist) as tmpFileVar:
            args.wordlist = tmpFileVar.read().split('\n')
            args.wordlist = list(filter(lambda x: len(x) > 0, args.wordlist))
    # execute 0xPo11 libraries
    try:
        module = importlib.import_module(f'ciphers.{args.cipher}')
    except Exception:
        print(
            f"{b.FAIL}\n{Fore.RED}"
            + f"[✖] Cipher May Not Exist\nTry 'key -h' to see all ciphers{b.END}\n"
            + Fore.RESET
        )
        return

    func = None

    if args.layerd:
        if args.brute or args.translate or args.payload or args.lang:
            output(["For now '-tr', '-b', or '-p' can only be the final step in layered encryption", False], False)
            try:
                os.remove('temp_storage.txt')
            except Exception:
                pass
        else:
            layer_func = module.decode if args.decode else module.encode
            layerd_storage = layer_func(args)[0]
            with open('temp_storage.txt', 'w') as temp:
                temp.write(layerd_storage)
    elif args.encode:
        func = module.encode
    elif args.decode:
        func = module.decode
    elif args.brute:
        func = module.brute
    elif args.translate:
        func = module.translate
    elif args.lang:
        output(module.languages(), args.output)
    elif args.payload:
        func = module.payload
    else:
        print(Fore.CYAN + module.help_menu + Fore.RESET)

    if func:
        output(func(args), args.output)


# tab completion for the keyconsole
def setup_completion():
    try:
        import readline
    except ImportError:
        return

    ciphers = get_ciphers()
    commands = ['help', 'version', 'list', 'update', 'remove', 'uninstall', 'exit', 'quit', 'clear']

    def completer(text, state):
        options = [c + ' ' for c in ciphers + commands if c.startswith(text)]
        try:
            return options[state]
        except IndexError:
            return None

    readline.parse_and_bind('tab: complete')
    readline.set_completer(completer)


# executes a chain of layered ciphers: "cc -e -t x -k 1 + b64 -e + hex -e"
def run_layered(cmd_str):
    layers = cmd_str.split(' + ')
    for index, layer in enumerate(layers):
        if index == 0:
            os.system(f'python3 {_main_path}/main.py {layer} -lay')
        elif index != len(layers) - 1:
            try:
                with open('temp_storage.txt') as temp:
                    layerd_storage = temp.read()
            except Exception:
                pass
            else:
                os.system(f'python3 {_main_path}/main.py {layer} -t "{layerd_storage}" -lay')
        else:
            layer = layer if any(flag in layer for flag in [' -e', ' -d', ' -b']) else f'{layer} -e'
            try:
                with open('temp_storage.txt') as temp:
                    layerd_storage = temp.read()
            except Exception:
                pass
            else:
                os.system(f'python3 {_main_path}/main.py {layer} -t "{layerd_storage}"')
                os.remove('temp_storage.txt')


# command line interface
def cli(args_exist):
    cmd_prefix = f'{Fore.CYAN}[~] {Fore.RESET}'

    # default arguments
    if args_exist:
        first = sys.argv[1]
        if first in ['-h', '--help']:
            print(b.help_menu)
        elif first in ['-v', '--version']:
            print(f'0xPo11 v{b.version}')
        elif first in ['-u', '--update']:
            update()
        elif first in ['-rm', '--remove', '--uninstall']:
            remove()

        elif '+' in sys.argv:
            cmd_str = " ".join(sys.argv[1:])
            run_layered(cmd_str)
        else:
            args = build_parser().parse_args()
            execute(args)
    else:
        # display banner
        setup_completion()
        print(b.banner)
        print(f'{cmd_prefix}Type "help" for help menu :')

        # loop code
        while True:
            try:
                # get user input
                user_input = input(b.header).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not user_input:
                continue

            parts = user_input.split(' ')
            cmd = parts[0]

            # display help menu
            if cmd == 'help':
                print(b.help_menu)

            elif cmd == 'version':
                print(f'0xPo11 v{b.version}')

            elif cmd == 'list':
                print(f'{Fore.CYAN}[+] Available Ciphers{Fore.RESET}')
                for name in get_ciphers():
                    print(f'  {name:<10} {CIPHER_NAMES.get(name, name)}')

            elif cmd in ['exit', 'quit']:
                break

            elif cmd == 'update':
                update()

            elif cmd in ['uninstall', 'remove']:
                remove()

            elif cmd == 'clear':
                os.system('clear')

            elif '+' in user_input:
                run_layered(user_input)

            elif cmd in get_ciphers():
                try:
                    args = build_parser().parse_args(shlex.split(user_input))
                except SystemExit:
                    continue
                execute(args)

            else:
                os.system(user_input)


# main code
def main():
    try:
        sys.argv[1]
    except IndexError:
        args_exist = False
    else:
        args_exist = True

    cli(args_exist)


# executes main code
if __name__ == '__main__':
    main()