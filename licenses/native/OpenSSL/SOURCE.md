# OpenSSL 3.5.9 (updated from 3.0.18)

Actual CPython 3.14.8 ssl.OPENSSL_VERSION and DLL version resources report
OpenSSL 3.5.9 (29 September 2026). CPython v3.14.8 PCbuild/python.props
also pins this version. The fixed source's unmodified Apache-2.0 license:
https://github.com/openssl/openssl/blob/openssl-3.5.9/LICENSE.txt
Copyright OpenSSL project authors. No source modifications were made.

The old 3.0.18 was replaced as part of the complete official signed
CPython 3.14.8 NuGet runtime, not by mixing DLLs from unrelated distributions.
https://www.python.org/downloads/release/python-3148/
https://www.openssl-library.org/news/vulnerabilities-3.5/index.html
The official runtime package SHA-256 is pinned in prepare-python-runtime.ps1.
Existing LiteRT/Pillow/PyInstaller package versions and model profiles remain
unchanged. Download/SSL, native-dot equivalence, AI and packaged minimal-PATH
tests must accompany runtime updates. This does not establish the SBOM or
security status of the independently bundled LiteRT native library.
