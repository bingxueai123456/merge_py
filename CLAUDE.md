# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyQt5 desktop application for merging binary files (BIN format) for embedded systems development - specifically for battery swap cabinet control boards. Single-file application (`bin_merger.py`) with ~710 lines of code.

**Technologies:** Python 3.13, PyQt5, binary file manipulation

## Architecture

### Core Components
- **MemoryMapWidget**: Visualizes BOOT/APP memory regions with color-coded layout
- **HexViewer**: Hex editor with address search and ASCII display
- **FileLoaderThread**: Background file loading with progress reporting
- **BinMergerApp**: Main window with tabbed interface for BOOT/APP/merged content

### Key Features
- Binary file merging at configurable memory addresses
- Real-time memory visualization showing usage
- Vector table repair and checksum validation (CRC32/MD5)
- Background operations with progress tracking

### Memory Layout
Default configuration:
- BOOT: 0x8000000 - 0x8010000 (1MB)
- APP: 0x8020000 - 0x8040000 (128KB)
- Unused memory filled with 0xFF (erased Flash simulation)

## Development

### Commands
```bash
# Install dependencies
pip install PyQt5

# Run application
python bin_merger.py
```

### Class Structure
```
BinMergerApp (QMainWindow)
├── MemoryMapWidget (visualization)
├── HexViewer (hex editor)
├── FileLoaderThread (background loading)
├── AddressDialog (memory config)
└── VectorTableDialog (vector analysis)
```

### Key Methods
- `select_file()`: File selection with address configuration
- `merge_files()`: Core merging with validation
- `save_file()`: Save with CRC32/MD5 checksum
- `update_memory_map()`: Refresh visualization
- `fix_interrupt_vector_table()`: Repair vectors

## Development Guidelines

### Code Conventions
- Chinese comments in source code (maintain consistency)
- Qt naming conventions for UI elements
- Thread-safe operations for file I/O
- Memory address validation before operations

### Testing
- Test with various binary file sizes
- Verify memory address calculations
- Check vector table repair functionality
- Validate CRC32/MD5 checksums

### Security Notes
Tool processes binary files - use with trusted input only. Basic validation performed but no malicious content scanning.

### Threading Pattern
```python
self.boot_loader = FileLoaderThread(file_path, "boot", start_addr, size)
self.boot_loader.finished.connect(self.on_file_loaded)
self.boot_loader.progress.connect(self.progress_bar.setValue)
self.boot_loader.start()
```