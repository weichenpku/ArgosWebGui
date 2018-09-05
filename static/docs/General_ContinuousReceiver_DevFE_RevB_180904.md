# General_ContinuousReceiver_DevFE_RevB_180904

## description

In previous studies, I always use receive stream with flag `SOAPY_SDR_END_BURST`, however, it has a limitation that the number of samples in a burst could not exceed 16384 or something like that. If you do so, you'll get a `BAD read` from python

This mode is using `SOAPY_SDR_HAS_TIME` flag only, with continuous data received, so that there might be no that problem.