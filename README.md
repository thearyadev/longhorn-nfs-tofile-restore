# Longhorn NFS tofile restore

this is a simple script to restore a longhorn backup from an NFS share to a RAW file.

This program will scan the NFS share for backups and allow you to interactively select a backup to restore. 

## Usage

```
$ python main.py -h

usage: main.py [-h] [--mount MOUNT] [--nfs-mount-point NFS_MOUNT_POINT]
               nfs longhorn_version outfile

positional arguments:
  nfs                   NFS path for longhorn backup
  longhorn_version      longhorn image tag
  outfile               Path to write resulting file. Path must exist file must not exist.
                        for example, /tmp/backup.raw where backup.raw does not exist, and
                        /tmp exists

options:
  -h, --help            show this help message and exit
  --mount MOUNT         Mount point for resulting file
  --nfs-mount-point NFS_MOUNT_POINT
                        temporary Mount point for NFS

```

```bash
python3 main.py nfs://192.168.1.34:/mnt/critical/backups/longhorn v1.6.2 ./bak.raw
```
where v1.6.2 is the longhorn version, and bak.raw is the path to the resulting file.

inside the longhorn folder is the "backkupstore" folder which contains the backups

tested on python 3.11.9. uses no external libraries.
should work on python 3.9+


## License

wtfpl





