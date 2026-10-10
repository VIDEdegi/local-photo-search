# LiteRT native audit source

LiteRT-LM v0.18.0 WORKSPACE pins google-ai-edge/LiteRT commit
26895c9fbcc25c43faa8c1a98cd1fd28951602c3. LICENSE is the unmodified
Apache-2.0 license at that exact commit:
https://github.com/google-ai-edge/LiteRT/blob/26895c9fbcc25c43faa8c1a98cd1fd28951602c3/LICENSE

This is a verified source license, not proof of a complete Windows wheel
SBOM. The official 0.18.0 Windows wheel has no LICENSE/NOTICE/SBOM files.
The DLL's version resource reports 0.2.0; the Python package reports 0.18.0.
Do not substitute one version for the other or assert that every statically
linked third-party component has Apache terms. Public redistribution stays
blocked until the actual wheel's dependency notices and build provenance
can be established. See docs/DISTRIBUTION_AUDIT.md.

Final dev.2 supplement: ten official dependency license texts are now in
../LiteRT-third-party/. Missing SBOM alone is not a prohibition; the specific
remaining issue is sufficiency of mandatory notices for the actual linked
transitive components. Current assessment: docs/DISTRIBUTION_CLOSURE.md.
