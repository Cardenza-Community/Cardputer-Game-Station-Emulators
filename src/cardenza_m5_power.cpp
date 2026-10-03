// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Cardenza contributors
// M5Unified's automatic Power.begin otherwise initializes a battery ADC.
// Compile/link only for an explicit Cardenza target, using:
// -Wl,--wrap=_ZN2m511Power_Class5beginEv
// -Wl,--wrap=_ZN2m59M5Unified10_setup_ledEN4lgfx6boards7board_tE
#if defined(CARDENZA_TARGET)
extern "C" bool __wrap__ZN2m511Power_Class5beginEv(void *) { return true; }
// Newer M5Unified otherwise allocates RMT and configures the RGB LED at begin.
extern "C" void __wrap__ZN2m59M5Unified10_setup_ledEN4lgfx6boards7board_tE(void *, int) {}
#endif
