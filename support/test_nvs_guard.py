"""Compile the actual guard and check whole-NVS refusal and normal erase forwarding."""
from pathlib import Path
import os
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = root / "src/cardenza_nvs_guard.cpp"
if not source.exists():
    source = root / "support/cardenza_nvs_guard.cpp"
with tempfile.TemporaryDirectory() as directory:
    temporary = Path(directory)
    (temporary / "esp_partition.h").write_text("""#pragma once
#include <stddef.h>
typedef int esp_err_t;
#define ESP_PARTITION_TYPE_DATA 1
#define ESP_PARTITION_SUBTYPE_DATA_NVS 2
#define ESP_ERR_NOT_SUPPORTED 0x106
typedef struct { int type; int subtype; size_t size; } esp_partition_t;
""")
    (temporary / "test.cpp").write_text("""#include <assert.h>
#include <esp_partition.h>
extern "C" esp_err_t __wrap_esp_partition_erase_range(const esp_partition_t *, size_t, size_t);
static int calls;
extern "C" esp_err_t __real_esp_partition_erase_range(const esp_partition_t *, size_t, size_t) { ++calls; return 17; }
int main() {
    esp_partition_t nvs = {1, 2, 0x6000}, app = {0, 0, 0x200000}, fs = {1, 0x82, 0x80000};
    assert(__wrap_esp_partition_erase_range(&nvs, 0, nvs.size) == ESP_ERR_NOT_SUPPORTED);
    assert(calls == 0);
    assert(__wrap_esp_partition_erase_range(&nvs, 0, 0x1000) == 17);
    assert(__wrap_esp_partition_erase_range(&nvs, 0x1000, 0x1000) == 17);
    assert(__wrap_esp_partition_erase_range(&app, 0, app.size) == 17);
    assert(__wrap_esp_partition_erase_range(&fs, 0, fs.size) == 17);
    assert(__wrap_esp_partition_erase_range(nullptr, 0, 0) == 17);
    assert(calls == 5);
}
""")
    executable = temporary / ("guard.exe" if os.name == "nt" else "guard")
    subprocess.run([os.environ.get("CXX", "c++"), "-DCARDENZA_TARGET=1", "-I", str(temporary), str(source), str(temporary / "test.cpp"), "-o", str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
print("PASS: whole shared NVS protected; NVS page GC, app and filesystem erases forwarded")
