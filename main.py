import subprocess
import json
import argparse
import os
from pprint import pprint
from pathlib import Path
from glob import glob
import datetime
from dataclasses import dataclass


def restore(
    nfs: str, longhorn_version: str, outfile: str, volumeName: str, backupId: str
):
    command = [
        "docker",
        "run",
        "--rm",
        "--privileged",
        "-v",
        f"{Path(outfile).parent}:/restore",
        f"longhornio/longhorn-engine:{longhorn_version}",
        "longhorn",
        "backup",
        "restore-to-file",
        f"{nfs}?backup={backupId}&volume={volumeName}",
        "--output-file",
        f"/restore/{Path(outfile).name}",
        "--output-format",
        "raw",
    ]
    print(f"Running command: {' '.join(command)}")
    try:
        subprocess.run(
            command,
            check=True,
        )

    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print(f"Error output: {e.stderr}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)


class NFSSession:
    def __init__(self, nfs: str, mount_point: str):
        self.nfs = nfs
        self.mount_point = (
            mount_point if mount_point is not None else "./temp_backup_query"
        )

    def __enter__(self):
        os.mkdir(self.mount_point)
        nfs_p = self.nfs.replace("nfs://", "")
        subprocess.run(["sudo", "mount", "-t", "nfs", nfs_p, self.mount_point])
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        subprocess.run(["sudo", "umount", "./temp_backup_query"])
        os.rmdir("./temp_backup_query")


@dataclass
class Backup:
    id: str
    name: str
    creationDate: datetime.datetime


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("nfs", help="NFS path for longhorn backup")
    parser.add_argument("longhorn_version", help="longhorn image tag")
    parser.add_argument(
        "outfile",
        help="Path to write resulting file. Path must exist file must not exist. for example, /tmp/backup.raw where backup.raw does not exist, and /tmp exists",
    )
    parser.add_argument("--mount", help="Mount point for resulting file")
    parser.add_argument("--nfs-mount-point", help="temporary Mount point for NFS")
    args = parser.parse_args()

    if not Path(args.outfile).parent.exists():
        print(f"Output file {args.outfile} does not exist")
        return 1
    if Path(args.outfile).exists():
        print(f"Output file {args.outfile} already exists")
        return 1

    print(f"NFS path: {args.nfs}")

    with NFSSession(args.nfs, args.nfs_mount_point) as nfs:
        print(f"NFS mounted at {nfs.mount_point}")
        backup_files = glob(
            f"{nfs.mount_point}/backupstore/volumes/*/*/*/backups/backup_backup-*.cfg"
        )
        print(f"Found {len(backup_files)} backups")
        backups_info = []
        for backup in backup_files:
            print("Processing backup: ", backup)
            with open(backup, "r") as f:
                backup_info = json.load(f)
                backups_info.append(backup_info)
        backup_list = [
            Backup(
                id=backup.get("Name"),
                name=backup.get("VolumeName"),
                creationDate=datetime.datetime.fromisoformat(
                    backup.get("SnapshotCreatedAt")
                ),
            )
            for backup in backups_info
        ]

    volumes = set(backup.name for backup in backup_list)
    selected_volume = None
    for volume in volumes:
        print(f"\tVolume: {volume}")
    while selected_volume is None:
        selected_volume_i = input("Select a volume: ")
        if selected_volume_i not in volumes:
            print("Invalid volume")
            continue
        selected_volume = selected_volume_i

    for backup in backup_list:
        if backup.name == selected_volume:
            print(f"\tBackup: {backup.id}")
            print(f"\t\tCreation date: {backup.creationDate}")

    selected_backup_id = None
    while selected_backup_id is None:
        selected_backup_id_i = input("Select a backup: ")
        if selected_backup_id_i not in [backup.id for backup in backup_list]:
            print("Invalid backup")
            continue
        selected_backup_id = selected_backup_id_i

    print(f"Restoring backup [{selected_volume}/{selected_backup_id}]")
    restore(
        args.nfs,
        args.longhorn_version,
        args.outfile,
        selected_volume,
        selected_backup_id,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
