# Runtime Cardputer / ADV / Cardenza support

Build `pio run -e m5stack-stamps3` normally; `cardenza` retains 3.5 MiB app metadata for the existing Launcher test slot while sharing the same runtime source/dependencies. No generated bootloader/table is installed.

The normal default build uses [203Null/M5Unified](https://github.com/203Null/M5Unified/tree/74fe31c6d9a2bd7c04f81eb4f8f0af99262e3bc2) at immutable commit `74fe31c6d9a2bd7c04f81eb4f8f0af99262e3bc2`, M5GFX 0.2.31 and M5Cardputer 1.1.1. One app image selects original Cardputer, Cardputer ADV or Cardenza at runtime. ES8156 identification, codec initialization, GPIO21 LED hold, and Cardenza-only suppression of battery ADC/charging, RGB and IMU are owned by M5Unified. No `CARDENZA_TARGET`, forced board identity, or Power/LED linker wrappers are used by these builds. Original/ADV initialization remains the library's normal path.

Install only the app BIN through Launcher; preserve its bootloader and partition table. The new unified images have been compiled and audited on the host; they have not been flashed or physically tested. Earlier device logs under `../artifacts/` apply only to the older forced Cardenza images.

The vendored M5Cardputer 1.1.1 keyboard reader uses the physical board identity provided by M5Unified. Emulator sound engines use M5 Speaker begin/playRaw; the fork restores the ES8156 configuration each time Speaker restarts. USB CDC is enabled at boot so startup logging does not configure UART0 on audio LRCK GPIO43. No battery UI or direct RGB driver is used.

ROM partition choice is runtime, through a small C bridge to M5.isCardenza. On Cardenza only, ROM loading/mapping requires dedicated `cardenza_rom` data subtype 0x40; registered, sector aligned, nonempty, entirely within [0x400000,0x800000), and non-overlapping with every other partition. No filesystem fallback/unmount or table rewrite is allowed. Existing scratch is 512 KiB at 0x780000; larger ROMs require an explicit Launcher layout change. ROM writes round erasure to 64 KiB and copy exactly the file size in 8 KiB chunks. Missing/oversize ROMs fail before writing.

Original/ADV retain upstream generic spiffs scratch/unmount behavior; it destroys that selected scratch filesystem when loading a ROM. Users must allocate scratch deliberately rather than point it at shared Launcher data. The app never changes the partition table. `python support/test_rom_scratch.py` tests actual runtime-branch flash-copy code with synthetic bytes, both device branches, malformed tables, overlap/bounds/alignment, size limits, erase/write failures and exact copy. No ROM was downloaded or emulated; gameplay/audio remains unverified.

Windows build fix includes MSX ../EMULib/Sound.h explicitly to avoid a case-insensitive collision with Arnold sound.h. Private build core: C:/pio-utility. Historical HAL/Power wrapper source files are inactive because no force-target macro/wrapper flags are selected.

## Launcher publication protection

The published `cardenza` compatibility target adds `LAUNCHER_NVS_GUARD` and wraps only esp_partition_erase_range to refuse a whole shared NVS erase. This install-context guard is independent of runtime hardware detection and is retained in the guarded test aliases. Normal NVS page garbage collection and app/filesystem erases still pass through. Run `python support/test_nvs_guard.py`. Build/publication CI retains the cardenza alias and its existing app/license asset paths. See docs/LAUNCHER_PUBLISHING.md.
