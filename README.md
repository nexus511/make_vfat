# make_vfat.py

This is a simple script that packs a set of files into a drive image
containing a vfat formated partition by creating a sparse file to comsume as
small disk space as possible.

## Requirements

The script requires a few packages being installed:

- mtools
- util-linux
- dosfstools
- python3

To make sure those tools are installed, you can use the following command on
ubuntu/debian:

```
sudo apt install util-linux mtools dosfstools python3
```

## Usage

Let's say you created a directory called `files` containing the files you
want to see on the disk image, you can use the following command to create
the image file:

```
python3 make_vfat.py files output.img
```

This will create a 32GB image named `output.img`. You can modify the size
for the image using the `--size` parameter. The size can be provided in MB
only. You can also set a label for the vfat partition, using the `--label`
parameter. 

The script will check, if the output file already exists. Using `--force`
will delete the output file, before starting to write.

This command will create a 8192MB sized image containing a partition with
the filesystem label TRANSFER holding all the files from the usb directory:

```
python3 usb/scripts/make_vfat.py --size=8192 --label=TRANSFER --force usb output.img
```

