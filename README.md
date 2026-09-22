# Sohdow Official Applications 0.1

This repository contains the four official Sohdow 0.1 desktop applications. Each application is maintained in its own directory and uses the existing **Sohd App Format 0.1** with the local `Sohd-App-Format` SDK.

## Applications

| Application | Directory | Package ID | Runtime |
|---|---|---|---|
| Sohd Browser | `Sohd-Browser/` | `org.sohdow.browser` | `python3` |
| Sohd File Manager | `Sohd-File-Manager/` | `org.sohdow.filemanager` | `python3` |
| Sohd Settings | `Sohd-Settings/` | `org.sohdow.settings` | `python3` |
| Sohd Document Editor | `Sohd-Document-Editor/` | `org.sohdow.documenteditor` | `python3` |

Each application includes its own README, `LICENSE`, dependency/license documentation, tests, manifest, source tree, and validated `.soh` package in `dist/`.

## Requirements

The applications are designed for a $0 local development workflow. They use Python 3.11+ and free/open-source-compatible host runtimes:

- PyQt6 for native desktop widgets;
- Qt WebEngine for Sohd Browser;
- Python standard library services for application logic and local persistence.

Install only the runtime needed for the application you want to run. See each app’s `docs/DEPENDENCIES.md` and `docs/RUNTIME.md`.

## Build and validate an application

The repository does not include the SDK as a nested dependency. Use the existing local SDK checkout:

```bash
/home/ubuntu/Sohd-App-Format/bin/sohd build /home/ubuntu/Sohdow-Apps/Sohd-Browser
/home/ubuntu/Sohd-App-Format/bin/sohd package /home/ubuntu/Sohdow-Apps/Sohd-Browser \
  --output /home/ubuntu/Sohdow-Apps/Sohd-Browser/dist/Sohd-Browser.soh
/home/ubuntu/Sohd-App-Format/bin/sohd validate \
  /home/ubuntu/Sohdow-Apps/Sohd-Browser/dist/Sohd-Browser.soh
```

Replace the Browser paths with the directory and package name of another application. The package format, manifest schema, and SDK behavior are not changed by this repository.

## Repository scope

This repository contains only the four official applications listed above. It does not contain Sohdow OS, Sohd Store, a cloud service, a package registry, or additional applications. Current manifest permissions are declarative under Sohd App Format 0.1; runtime sandbox enforcement remains a future OS responsibility.

## License

The application source is MIT licensed unless a file states otherwise. Third-party components retain their own licenses, documented per application.
