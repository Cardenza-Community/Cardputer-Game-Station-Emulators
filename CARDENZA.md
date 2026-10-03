# Cardenza support

This target retains the original Cardputer display and matrix-keyboard layout.
It verifies the ES8156 codec on SDA2/SCL1 and uses stereo Philips I2S,
16-bit samples and 32 BCLK per frame on BCLK41/LRCK43/DOUT42.
GPIO21 is held high to disable the keyboard LED. Cardenza has no battery,
charging detector, IMU or PSRAM; unavailable hardware is not simulated.
The original application license and third-party notices remain in force.

Build the normal application with `pio run -e cardenza`. Install only
`.pio/build/cardenza/firmware.bin` through Software Launcher. Preserve the
existing bootloader, partition table, otadata and shared NVS.
The target refuses whole shared-NVS erasure during Arduino recovery while
allowing normal NVS page garbage collection and unrelated partition writes.
Run `python3 support/test_nvs_guard.py` to verify this forwarding contract.
Successful compilation does not prove physical display, keys, audio or RF.
No wireless/security functionality is executed by these build checks.

Upstream's default branch is `xip_load`, not `main`.
ROM loading requires a dedicated `cardenza_rom` data partition, subtype `0x40`,
sector aligned and wholly within `[0x400000, 0x800000)`, without overlapping
any app/data partition. Missing/invalid scratch is refused before writes.
The documented 512 KiB scratch at `0x780000` limits ROM size to 512 KiB.
No shared SPIFFS fallback or app-driven partition resizing is permitted.
Run `python3 support/test_rom_scratch.py` to test the actual flash-copy path
with synthetic ROM bytes. No ROM is included or downloaded by validation.
M5Unified is pinned to separately compiled 0.2.22; power/RGB setup is wrapped.
USB CDC avoids UART0 initialization on GPIO43/audio LRCK.
The HAL license is `support/CARDENZA-HAL-LICENSE`.
