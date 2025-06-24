import modal
import shutil
import os

image = (
    modal.Image.debian_slim()
    .add_local_dir("test_files/250616 DPVs Pprot382int-2007B concentrated in Eric MM", "/test_files/250616 DPVs Pprot382int-2007B concentrated in Eric MM")
    .add_local_dir("my_files", "/my_files")
)

with modal.App("create-volume-w-files").run() as app:
    # make a sandbox and mount a volume
    sb = modal.Sandbox.create(
        app=app,
        image=image,
        volumes={"/workspace": modal.Volume.from_name("dataset-processor-agent-volume-test", create_if_missing=True)},
        workdir="/workspace"
    )
    print("Sandbox created successfully!")

    # copy files from test_files to the sandbox
    p = sb.exec("cp" ,"-r", "/test_files/250616 DPVs Pprot382int-2007B concentrated in Eric MM", "/workspace")
    print(p.stdout.read())

    # copy files from my_files to the sandbox
    p = sb.exec("cp" ,"-r", "/my_files/.", "/workspace")
    print(p.stdout.read())

    # print what's in a folder
    p = sb.exec("ls" ,"-la", "/workspace")
    print(p.stdout.read())

    print("Files copied successfully!")