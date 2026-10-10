# Reference only - excluded component

LICENSE was fetched from the official OpenVINO 2025.4.0 source repository:
https://github.com/openvinotoolkit/openvino/blob/2025.4.0/LICENSE

This source license does NOT identify the unknown version of OpenVINO that
the wheel's Intel NPU LiteRtDispatch.dll would require, or resolve all Intel
binary redistribution terms. That unused dispatch library imports an
unbundled openvino.dll and is excluded from this development build. Our
WebGPU and XNNPACK CPU backends do not use the Intel NPU dispatch. OpenVINO
runtime is neither installed nor bundled. This reference is not a grant
to redistribute an unidentified Intel/OpenVINO binary.
