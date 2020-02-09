/*

THINGSPEAK MODULE

Copyright (C) 2019 by Xose Pérez <xose dot perez at gmail dot com>

*/

#pragma once

#if THINGSPEAK_SUPPORT

#if THINGSPEAK_USE_ASYNC
#include <ESPAsyncTCP.h>
#endif

constexpr const size_t tspkDataBufferSize = 256;

bool tspkEnqueueRelay(unsigned char index, bool status);
bool tspkEnqueueMeasurement(unsigned char index, const char * payload);
void tspkFlush();

bool tspkEnabled();
void tspkSetup();

#endif // THINGSPEAK_SUPPORT == 1
