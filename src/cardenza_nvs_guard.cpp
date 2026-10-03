// SPDX-License-Identifier: MIT
#ifdef CARDENZA_TARGET
#include <esp_partition.h>
extern "C" esp_err_t __real_esp_partition_erase_range(const esp_partition_t *, size_t, size_t);
extern "C" esp_err_t __wrap_esp_partition_erase_range(const esp_partition_t *partition, size_t offset, size_t size) {
    // Preserve normal NVS page garbage collection; refuse complete shared-NVS erasure.
    if (partition && partition->type == ESP_PARTITION_TYPE_DATA &&
        partition->subtype == ESP_PARTITION_SUBTYPE_DATA_NVS &&
        offset == 0 && size == partition->size) return ESP_ERR_NOT_SUPPORTED;
    return __real_esp_partition_erase_range(partition, offset, size);
}
#endif
