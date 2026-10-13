# Security policy

## Supported versions

StampAlbum Pro is alpha software maintained by one person. Only the latest release gets security fixes. Fixes are not backported.

## Reporting a vulnerability

Please don't open a public issue. Report it privately, in either of these ways:

- **GitHub (preferred):** the repository's **Security** tab › **Report a vulnerability**
- **Email:** jsganesh@gmail.com, with "StampAlbum Pro security" in the subject

Include what you found, how to reproduce it, and which version and operating system you used.

I'll reply within 7 days. When a fix is released, I'll publish a GitHub security advisory and credit you, unless you'd rather not be named.

## How the app is meant to run

StampAlbum Pro runs a small web server on your own computer. By default it listens only on `127.0.0.1`, so nothing else on your network can reach it. Its API has no sign-in.

If you set `STAMP_ALBUM_HOST` to make it reachable from other devices, for example to use it from an iPhone on home Wi-Fi, anyone on that network can read and change your albums. Do this only on a network you trust, and never expose the app to the internet.

## Out of scope

- The warnings macOS and Windows show for the apps, which are not signed yet
- Problems that need someone to already control your computer or your user account
