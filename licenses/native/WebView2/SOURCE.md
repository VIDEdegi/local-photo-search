# WebView2 SDK and Runtime are separate

SDK: Microsoft.Web.WebView2 1.0.3800.47 official NuGet package:
https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/1.0.3800.47/microsoft.web.webview2.1.0.3800.47.nupkg
LICENSE.txt and NOTICE.txt are copied verbatim from that package.
The x64 WebView2LoaderStatic.lib used by webview2-com-sys 0.39.1 matches
the NuGet library byte for byte. The static SDK loader is inside the app;
the Rust crate version is not the Microsoft SDK binary version.

Runtime Bootstrapper: official Tauri embedBootstrapper downloaded
MicrosoftEdgeWebview2Setup.exe (1.3.279.5, 1,857,232 bytes) with valid
Microsoft Corporation Authenticode signature. SHA is in the artifact
manifest. Microsoft's official distribution documentation permits bundling
the small Evergreen Bootstrapper:
https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution
https://developer.microsoft.com/en-us/microsoft-edge/webview2/

The bootstrapper installs the separately licensed Microsoft Evergreen
Runtime. The SDK BSD license and SDK third-party NOTICE do not license
the Runtime. Users review the official Runtime terms at Microsoft's
download/install flow. We do not bundle the Runtime itself or an altered
bootstrapper, suppress Microsoft's terms, or claim our application
license overrides them. The full environment without WebView2 still
needs clean-Windows acceptance testing; see docs/CLEAN_WINDOWS_ACCEPTANCE.md.

2026-10-10 supplement: the official developer download page's BlockWebView2
component retrieves Evergreen terms from:
https://developer.microsoft.com/microsoft-edge/api/eula/webview2?locale=en-us
The successful response's complete evergreenHtml is preserved as
RUNTIME_EULA.html. RUNTIME_EULA.txt is its readable text, with HTML tags
removed and all text retained. Neither is the SDK's BSD license nor generic
Edge browser terms. Sections 2 and 9 impose distribution and notice duties;
the full text is included in the installer consent and SmartScreen/privacy
notice is in the user guide and THIRD_PARTY_NOTICES.md. Actual installation
on a clean PC without WebView2 remains unverified.

RUNTIME_EULA.html: 22094 bytes; SHA-256 26efdd3c89a83c426ed1a127fa0c81936ac70043af4cbaa9c12f9aadfa1d2f94

RUNTIME_EULA.txt: 19341 bytes; SHA-256 1170534bd6a8ce0a7bbd8a272d92781791738b4cff4a6eb65b85b576d5f2e54c
