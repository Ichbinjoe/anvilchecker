# AnvilChecker

AnvilChecker is a python script which is able to validate files in the [Region
file format](https://minecraft.gamepedia.com/Region_file_format). This script
attempts to validate all points of possible breakage within these files. The
script was made to help diagnose a flakey Region file engine.

## Running

AnvilChecker can be run using the following command:

```
./anvilchecker.py <name of file or directory>
```

If passed a directory, AnvilChecker will assume it is the region directory and
check all region files contained. If no directory or file is passed,
AnvilChecker will work in the current directory.

## Checks AnvilChecker runs

+ Region file is of proper length
+ Chunks in the region file don't accidentally write off the end of the file
  according to the offset buffer
+ Chunks in the region file don't accidentally write over each other according
  to the offset buffer
+ Length reported inside the chunk is actually the correct length given the
  amount of sectors it was allocated
+ Compression reported by the chunk is valid
    + Warning thrown when using GZip, since no one actually ever uses it since
      its stupid
+ Attempts to find chunks which were not allocated but still in the file using
  the compression flag as a heuristic
+ Displays a usage of the sector

## License

AnvilChecker is licensed under the MIT License. This license can be viewed in
[LICENSE](./LICENSE)
