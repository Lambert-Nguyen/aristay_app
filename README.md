# Aristay App

Aristay App is a cleaning and maintenance management application designed for property management. It features a Flutter-based mobile frontend and a Django-based backend secured with token authentication. This project allows users to register, log in, and manage cleaning tasks with detailed views and ownership-based editing.

## Features

- **User Registration & Authentication:**  
  - Secure token-based authentication (Django REST Framework's authtoken).
  - User registration API endpoint.
- **Task Management:**  
  - Create, read, update, and delete cleaning tasks.
  - Task details include property name, status, creator, assignee, and history.
  - Only task owners (or admins) can edit or delete their tasks.
  - Paginated task list with "Load More" functionality.
- **Frontend:**  
  - Built with Flutter (Dart) for iOS (and optionally Android).
  - Clean UI for login, task listing, task detail, and task creation/editing.
- **Backend:**  
  - Built with Django and Django REST Framework.
  - Uses a SQLite database for development (recommended PostgreSQL for production).
- **Deployment:**  
  - Ready for cost-effective deployment on AWS or similar cloud services.

## Tech Stack

- **Frontend:** Flutter (Dart)
- **Backend:** Django, Django REST Framework (Python)
- **Authentication:** Token Authentication
- **Database:** SQLite (development) / PostgreSQL (production recommended)
- **Deployment:** AWS (or other cost-effective cloud solutions)

## Installation and Setup

### Frontend (Flutter)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd aristay_flutter_frontend
2. **Install Flutter dependencies:**
   ```bash
   flutter pub get
4. **Run the app on your desired device or simulator:**
   ```bash
   flutter run

### Backend (Django)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd aristay_backend
3. **Create and activate a virtual environment:**
      ```bash
   python3 -m venv venv
   source venv/bin/activate
4. **Install Python dependencies:**
      ```bash
   pip install -r requirements.txt
5. **Apply database migrations:**
      ```bash
   python manage.py makemigrations
   python manage.py migrate
6. **Run the development server:**
      ```bash
   python manage.py runserver 0.0.0.0:8000

## Contributing

Nguyen, Phuong Duy Lam

## License

This project is licensed under the MIT License.

```
aristay_app
├─ README.md
├─ aristay_backend
│  ├─ api
│  │  ├─ __init__.py
│  │  ├─ admin.py
│  │  ├─ apps.py
│  │  ├─ migrations
│  │  │  ├─ 0001_initial.py
│  │  │  ├─ 0002_cleaningtask_created_by.py
│  │  │  ├─ 0003_alter_cleaningtask_status.py
│  │  │  ├─ 0004_cleaningtask_assigned_to_cleaningtask_history.py
│  │  │  ├─ 0005_property_task_delete_cleaningtask.py
│  │  │  ├─ 0006_taskimage.py
│  │  │  ├─ 0007_device_notification.py
│  │  │  ├─ 0008_alter_notification_options_alter_notification_task.py
│  │  │  ├─ 0009_notification_read_at.py
│  │  │  ├─ 0010_remove_notification_recipient_and_more.py
│  │  │  └─ __init__.py
│  │  ├─ models.py
│  │  ├─ permissions.py
│  │  ├─ serializers.py
│  │  ├─ services
│  │  ├─ tests.py
│  │  ├─ urls.py
│  │  └─ views.py
│  ├─ backend
│  │  ├─ __init__.py
│  │  ├─ asgi.py
│  │  ├─ settings.py
│  │  ├─ urls.py
│  │  └─ wsgi.py
│  ├─ db.sqlite3
│  ├─ manage.py
│  ├─ media
│  │  └─ task_images
│  │     └─ 2025
│  │        └─ 07
│  │           ├─ 10
│  │           │  ├─ ChatGPT_Image_May_28_2025_at_06_31_35_PM.png
│  │           │  └─ ChatGPT_Image_May_28_2025_at_07_09_06_PM.png
│  │           ├─ 14
│  │           │  ├─ image_picker_055393ED-7804-49B9-A934-4B9DC1D8386C-26574-00000D93E10A76FE.jpg
│  │           │  ├─ image_picker_5DFC9D74-6CD2-47B3-82E4-AA1B208921FD-93243-00000D788453DA5E.jpg
│  │           │  ├─ image_picker_7043489F-9600-4A0F-94C8-A7CA7D3649D3-93243-00000D78996D8488.jpg
│  │           │  ├─ image_picker_72DA8800-4C72-42CE-B991-49201B886AC1-93243-00000D78BA535D0F.jpg
│  │           │  ├─ image_picker_8F4A80B3-89B2-41BF-BF82-876CC999BA05-26574-00000D93D3105882.jpg
│  │           │  ├─ image_picker_9168C61D-0386-4FAC-8699-48D51182FE0D-31963-00000D9A54EE7F87.jpg
│  │           │  ├─ image_picker_A976018A-1F76-4CD8-8554-BD7B58705E4B-12634-00000D88B3037AA0.jpg
│  │           │  ├─ image_picker_DBCC8857-06D0-4717-8BAB-D5B9B81B34F3-31963-00000D9A4B409A78.jpg
│  │           │  ├─ image_picker_E09C3C93-59EF-47C0-A917-9AE33CC7970A-12634-00000D8B6BACAA91.jpg
│  │           │  ├─ image_picker_F0E1978F-35C7-4AC7-9E4E-8C9956FBCCA6-93243-00000D78E0B65090.jpg
│  │           │  └─ image_picker_F539E872-007A-4A2E-9F38-9D37DDF51709-12634-00000D8B40786002.jpg
│  │           └─ 15
│  ├─ requirements.txt
│  └─ static
│     └─ admin
│        └─ js
│           └─ timezone_local.js
└─ aristay_flutter_frontend
   ├─ .dart_tool
   │  ├─ dartpad
   │  │  └─ web_plugin_registrant.dart
   │  ├─ flutter_build
   │  │  ├─ 8ff18bd85c178a14d66b35382f744382
   │  │  │  ├─ .filecache
   │  │  │  ├─ App.framework
   │  │  │  │  └─ App
   │  │  │  ├─ app.dill
   │  │  │  ├─ dart_build.d
   │  │  │  ├─ dart_build.stamp
   │  │  │  ├─ dart_build_result.json
   │  │  │  ├─ debug_ios_bundle_flutter_assets.stamp
   │  │  │  ├─ debug_universal_framework.stamp
   │  │  │  ├─ debug_unpack_ios.stamp
   │  │  │  ├─ flutter_assets.d
   │  │  │  ├─ gen_dart_plugin_registrant.stamp
   │  │  │  ├─ gen_localizations.stamp
   │  │  │  ├─ install_code_assets.d
   │  │  │  ├─ install_code_assets.stamp
   │  │  │  ├─ kernel_snapshot_program.d
   │  │  │  ├─ kernel_snapshot_program.stamp
   │  │  │  ├─ native_assets.json
   │  │  │  └─ outputs.json
   │  │  └─ dart_plugin_registrant.dart
   │  ├─ package_config.json
   │  ├─ package_config_subset
   │  └─ version
   ├─ .flutter-plugins
   ├─ .flutter-plugins-dependencies
   ├─ .metadata
   ├─ README.md
   ├─ analysis_options.yaml
   ├─ android
   │  ├─ .gradle
   │  │  ├─ 8.10.2
   │  │  │  ├─ checksums
   │  │  │  │  ├─ checksums.lock
   │  │  │  │  ├─ md5-checksums.bin
   │  │  │  │  └─ sha1-checksums.bin
   │  │  │  ├─ dependencies-accessors
   │  │  │  │  └─ gc.properties
   │  │  │  ├─ executionHistory
   │  │  │  │  └─ executionHistory.lock
   │  │  │  ├─ expanded
   │  │  │  ├─ fileChanges
   │  │  │  │  └─ last-build.bin
   │  │  │  ├─ fileHashes
   │  │  │  │  ├─ fileHashes.bin
   │  │  │  │  ├─ fileHashes.lock
   │  │  │  │  └─ resourceHashesCache.bin
   │  │  │  ├─ gc.properties
   │  │  │  └─ vcsMetadata
   │  │  ├─ buildOutputCleanup
   │  │  │  ├─ buildOutputCleanup.lock
   │  │  │  └─ cache.properties
   │  │  ├─ kotlin
   │  │  │  └─ errors
   │  │  ├─ noVersion
   │  │  │  └─ buildLogic.lock
   │  │  └─ vcs-1
   │  │     └─ gc.properties
   │  ├─ app
   │  │  ├─ build.gradle.kts
   │  │  └─ src
   │  │     ├─ debug
   │  │     │  └─ AndroidManifest.xml
   │  │     ├─ main
   │  │     │  ├─ AndroidManifest.xml
   │  │     │  ├─ java
   │  │     │  │  └─ io
   │  │     │  │     └─ flutter
   │  │     │  │        └─ plugins
   │  │     │  │           └─ GeneratedPluginRegistrant.java
   │  │     │  ├─ kotlin
   │  │     │  │  └─ com
   │  │     │  │     └─ example
   │  │     │  │        └─ aristay_flutter_frontend
   │  │     │  │           └─ MainActivity.kt
   │  │     │  └─ res
   │  │     │     ├─ drawable
   │  │     │     │  └─ launch_background.xml
   │  │     │     ├─ drawable-v21
   │  │     │     │  └─ launch_background.xml
   │  │     │     ├─ mipmap-hdpi
   │  │     │     │  └─ ic_launcher.png
   │  │     │     ├─ mipmap-mdpi
   │  │     │     │  └─ ic_launcher.png
   │  │     │     ├─ mipmap-xhdpi
   │  │     │     │  └─ ic_launcher.png
   │  │     │     ├─ mipmap-xxhdpi
   │  │     │     │  └─ ic_launcher.png
   │  │     │     ├─ mipmap-xxxhdpi
   │  │     │     │  └─ ic_launcher.png
   │  │     │     ├─ values
   │  │     │     │  └─ styles.xml
   │  │     │     └─ values-night
   │  │     │        └─ styles.xml
   │  │     └─ profile
   │  │        └─ AndroidManifest.xml
   │  ├─ build.gradle.kts
   │  ├─ gradle
   │  │  └─ wrapper
   │  │     ├─ gradle-wrapper.jar
   │  │     └─ gradle-wrapper.properties
   │  ├─ gradle.properties
   │  ├─ gradlew
   │  ├─ gradlew.bat
   │  ├─ local.properties
   │  └─ settings.gradle.kts
   ├─ assets
   │  ├─ 307946795_127220173407088_7525814120016700760_n 2.jpg
   │  ├─ 307946795_127220173407088_7525814120016700760_n.jpg
   │  ├─ 468752154_550978027697965_7345613944854274144_n.jpg
   │  ├─ aristay_logo.jpg
   │  └─ cropped-AriStay-New-Logo-removebg-preview.png
   ├─ build
   │  ├─ 64835ef9c333b019ccaf87fd363b2f52
   │  │  ├─ _composite.stamp
   │  │  ├─ gen_dart_plugin_registrant.stamp
   │  │  └─ gen_localizations.stamp
   │  ├─ cache.dill.track.dill
   │  ├─ ios
   │  │  ├─ Debug-iphonesimulator
   │  │  │  ├─ .last_build_id
   │  │  │  ├─ App.framework
   │  │  │  │  ├─ App
   │  │  │  │  ├─ Info.plist
   │  │  │  │  ├─ _CodeSignature
   │  │  │  │  │  └─ CodeResources
   │  │  │  │  └─ flutter_assets
   │  │  │  │     ├─ AssetManifest.bin
   │  │  │  │     ├─ AssetManifest.json
   │  │  │  │     ├─ FontManifest.json
   │  │  │  │     ├─ NOTICES.Z
   │  │  │  │     ├─ NativeAssetsManifest.json
   │  │  │  │     ├─ assets
   │  │  │  │     │  └─ aristay_logo.jpg
   │  │  │  │     ├─ fonts
   │  │  │  │     │  └─ MaterialIcons-Regular.otf
   │  │  │  │     ├─ isolate_snapshot_data
   │  │  │  │     ├─ kernel_blob.bin
   │  │  │  │     ├─ packages
   │  │  │  │     │  └─ cupertino_icons
   │  │  │  │     │     └─ assets
   │  │  │  │     │        └─ CupertinoIcons.ttf
   │  │  │  │     ├─ shaders
   │  │  │  │     │  └─ ink_sparkle.frag
   │  │  │  │     └─ vm_snapshot_data
   │  │  │  ├─ Flutter
   │  │  │  ├─ Flutter.framework
   │  │  │  │  ├─ Flutter
   │  │  │  │  ├─ Headers
   │  │  │  │  │  ├─ Flutter.h
   │  │  │  │  │  ├─ FlutterAppDelegate.h
   │  │  │  │  │  ├─ FlutterBinaryMessenger.h
   │  │  │  │  │  ├─ FlutterCallbackCache.h
   │  │  │  │  │  ├─ FlutterChannels.h
   │  │  │  │  │  ├─ FlutterCodecs.h
   │  │  │  │  │  ├─ FlutterDartProject.h
   │  │  │  │  │  ├─ FlutterEngine.h
   │  │  │  │  │  ├─ FlutterEngineGroup.h
   │  │  │  │  │  ├─ FlutterHeadlessDartRunner.h
   │  │  │  │  │  ├─ FlutterHourFormat.h
   │  │  │  │  │  ├─ FlutterMacros.h
   │  │  │  │  │  ├─ FlutterPlatformViews.h
   │  │  │  │  │  ├─ FlutterPlugin.h
   │  │  │  │  │  ├─ FlutterPluginAppLifeCycleDelegate.h
   │  │  │  │  │  ├─ FlutterTexture.h
   │  │  │  │  │  └─ FlutterViewController.h
   │  │  │  │  ├─ Info.plist
   │  │  │  │  ├─ Modules
   │  │  │  │  │  └─ module.modulemap
   │  │  │  │  ├─ PrivacyInfo.xcprivacy
   │  │  │  │  ├─ _CodeSignature
   │  │  │  │  │  └─ CodeResources
   │  │  │  │  └─ icudtl.dat
   │  │  │  ├─ Pods_Runner.framework
   │  │  │  │  ├─ Headers
   │  │  │  │  │  └─ Pods-Runner-umbrella.h
   │  │  │  │  ├─ Info.plist
   │  │  │  │  ├─ Modules
   │  │  │  │  │  └─ module.modulemap
   │  │  │  │  ├─ Pods_Runner
   │  │  │  │  └─ _CodeSignature
   │  │  │  │     ├─ CodeDirectory
   │  │  │  │     ├─ CodeRequirements
   │  │  │  │     ├─ CodeRequirements-1
   │  │  │  │     ├─ CodeResources
   │  │  │  │     └─ CodeSignature
   │  │  │  ├─ Runner.app
   │  │  │  │  ├─ AppFrameworkInfo.plist
   │  │  │  │  ├─ AppIcon60x60@2x.png
   │  │  │  │  ├─ AppIcon76x76@2x~ipad.png
   │  │  │  │  ├─ Assets.car
   │  │  │  │  ├─ Base.lproj
   │  │  │  │  │  ├─ LaunchScreen.storyboardc
   │  │  │  │  │  │  ├─ 01J-lp-oVM-view-Ze5-6b-2t3.nib
   │  │  │  │  │  │  ├─ Info.plist
   │  │  │  │  │  │  └─ UIViewController-01J-lp-oVM.nib
   │  │  │  │  │  └─ Main.storyboardc
   │  │  │  │  │     ├─ BYZ-38-t0r-view-8bC-Xf-vdC.nib
   │  │  │  │  │     ├─ Info.plist
   │  │  │  │  │     └─ UIViewController-BYZ-38-t0r.nib
   │  │  │  │  ├─ Frameworks
   │  │  │  │  │  ├─ App.framework
   │  │  │  │  │  │  ├─ App
   │  │  │  │  │  │  ├─ Info.plist
   │  │  │  │  │  │  ├─ _CodeSignature
   │  │  │  │  │  │  │  └─ CodeResources
   │  │  │  │  │  │  └─ flutter_assets
   │  │  │  │  │  │     ├─ AssetManifest.bin
   │  │  │  │  │  │     ├─ AssetManifest.json
   │  │  │  │  │  │     ├─ FontManifest.json
   │  │  │  │  │  │     ├─ NOTICES.Z
   │  │  │  │  │  │     ├─ NativeAssetsManifest.json
   │  │  │  │  │  │     ├─ assets
   │  │  │  │  │  │     │  └─ aristay_logo.jpg
   │  │  │  │  │  │     ├─ fonts
   │  │  │  │  │  │     │  └─ MaterialIcons-Regular.otf
   │  │  │  │  │  │     ├─ isolate_snapshot_data
   │  │  │  │  │  │     ├─ kernel_blob.bin
   │  │  │  │  │  │     ├─ packages
   │  │  │  │  │  │     │  └─ cupertino_icons
   │  │  │  │  │  │     │     └─ assets
   │  │  │  │  │  │     │        └─ CupertinoIcons.ttf
   │  │  │  │  │  │     ├─ shaders
   │  │  │  │  │  │     │  └─ ink_sparkle.frag
   │  │  │  │  │  │     └─ vm_snapshot_data
   │  │  │  │  │  ├─ Flutter.framework
   │  │  │  │  │  │  ├─ Flutter
   │  │  │  │  │  │  ├─ Headers
   │  │  │  │  │  │  │  ├─ Flutter.h
   │  │  │  │  │  │  │  ├─ FlutterAppDelegate.h
   │  │  │  │  │  │  │  ├─ FlutterBinaryMessenger.h
   │  │  │  │  │  │  │  ├─ FlutterCallbackCache.h
   │  │  │  │  │  │  │  ├─ FlutterChannels.h
   │  │  │  │  │  │  │  ├─ FlutterCodecs.h
   │  │  │  │  │  │  │  ├─ FlutterDartProject.h
   │  │  │  │  │  │  │  ├─ FlutterEngine.h
   │  │  │  │  │  │  │  ├─ FlutterEngineGroup.h
   │  │  │  │  │  │  │  ├─ FlutterHeadlessDartRunner.h
   │  │  │  │  │  │  │  ├─ FlutterHourFormat.h
   │  │  │  │  │  │  │  ├─ FlutterMacros.h
   │  │  │  │  │  │  │  ├─ FlutterPlatformViews.h
   │  │  │  │  │  │  │  ├─ FlutterPlugin.h
   │  │  │  │  │  │  │  ├─ FlutterPluginAppLifeCycleDelegate.h
   │  │  │  │  │  │  │  ├─ FlutterTexture.h
   │  │  │  │  │  │  │  └─ FlutterViewController.h
   │  │  │  │  │  │  ├─ Info.plist
   │  │  │  │  │  │  ├─ Modules
   │  │  │  │  │  │  │  └─ module.modulemap
   │  │  │  │  │  │  ├─ PrivacyInfo.xcprivacy
   │  │  │  │  │  │  ├─ _CodeSignature
   │  │  │  │  │  │  │  └─ CodeResources
   │  │  │  │  │  │  └─ icudtl.dat
   │  │  │  │  │  ├─ image_picker_ios.framework
   │  │  │  │  │  │  ├─ Info.plist
   │  │  │  │  │  │  ├─ _CodeSignature
   │  │  │  │  │  │  │  └─ CodeResources
   │  │  │  │  │  │  ├─ image_picker_ios
   │  │  │  │  │  │  └─ image_picker_ios_privacy.bundle
   │  │  │  │  │  │     ├─ Info.plist
   │  │  │  │  │  │     └─ PrivacyInfo.xcprivacy
   │  │  │  │  │  └─ shared_preferences_foundation.framework
   │  │  │  │  │     ├─ Info.plist
   │  │  │  │  │     ├─ _CodeSignature
   │  │  │  │  │     │  └─ CodeResources
   │  │  │  │  │     ├─ shared_preferences_foundation
   │  │  │  │  │     └─ shared_preferences_foundation_privacy.bundle
   │  │  │  │  │        ├─ Info.plist
   │  │  │  │  │        └─ PrivacyInfo.xcprivacy
   │  │  │  │  ├─ Info.plist
   │  │  │  │  ├─ PkgInfo
   │  │  │  │  ├─ Runner
   │  │  │  │  ├─ Runner.debug.dylib
   │  │  │  │  ├─ _CodeSignature
   │  │  │  │  │  └─ CodeResources
   │  │  │  │  └─ __preview.dylib
   │  │  │  ├─ Runner.swiftmodule
   │  │  │  │  ├─ Project
   │  │  │  │  │  └─ arm64-apple-ios-simulator.swiftsourceinfo
   │  │  │  │  ├─ arm64-apple-ios-simulator.abi.json
   │  │  │  │  ├─ arm64-apple-ios-simulator.swiftdoc
   │  │  │  │  └─ arm64-apple-ios-simulator.swiftmodule
   │  │  │  ├─ image_picker_ios
   │  │  │  │  ├─ image_picker_ios.framework
   │  │  │  │  │  ├─ Headers
   │  │  │  │  │  │  ├─ FLTImagePickerImageUtil.h
   │  │  │  │  │  │  ├─ FLTImagePickerMetaDataUtil.h
   │  │  │  │  │  │  ├─ FLTImagePickerPhotoAssetUtil.h
   │  │  │  │  │  │  ├─ FLTImagePickerPlugin.h
   │  │  │  │  │  │  ├─ FLTImagePickerPlugin_Test.h
   │  │  │  │  │  │  ├─ FLTPHPickerSaveImageToPathOperation.h
   │  │  │  │  │  │  ├─ image_picker_ios-umbrella.h
   │  │  │  │  │  │  └─ messages.g.h
   │  │  │  │  │  ├─ Info.plist
   │  │  │  │  │  ├─ Modules
   │  │  │  │  │  │  └─ module.modulemap
   │  │  │  │  │  ├─ _CodeSignature
   │  │  │  │  │  │  └─ CodeResources
   │  │  │  │  │  ├─ image_picker_ios
   │  │  │  │  │  └─ image_picker_ios_privacy.bundle
   │  │  │  │  │     ├─ Info.plist
   │  │  │  │  │     └─ PrivacyInfo.xcprivacy
   │  │  │  │  └─ image_picker_ios_privacy.bundle
   │  │  │  │     ├─ Info.plist
   │  │  │  │     └─ PrivacyInfo.xcprivacy
   │  │  │  └─ shared_preferences_foundation
   │  │  │     ├─ shared_preferences_foundation.framework
   │  │  │     │  ├─ Headers
   │  │  │     │  │  ├─ shared_preferences_foundation-Swift.h
   │  │  │     │  │  └─ shared_preferences_foundation-umbrella.h
   │  │  │     │  ├─ Info.plist
   │  │  │     │  ├─ Modules
   │  │  │     │  │  ├─ module.modulemap
   │  │  │     │  │  └─ shared_preferences_foundation.swiftmodule
   │  │  │     │  │     ├─ Project
   │  │  │     │  │     │  ├─ arm64-apple-ios-simulator.swiftsourceinfo
   │  │  │     │  │     │  └─ x86_64-apple-ios-simulator.swiftsourceinfo
   │  │  │     │  │     ├─ arm64-apple-ios-simulator.abi.json
   │  │  │     │  │     ├─ arm64-apple-ios-simulator.swiftdoc
   │  │  │     │  │     ├─ arm64-apple-ios-simulator.swiftmodule
   │  │  │     │  │     ├─ x86_64-apple-ios-simulator.abi.json
   │  │  │     │  │     ├─ x86_64-apple-ios-simulator.swiftdoc
   │  │  │     │  │     └─ x86_64-apple-ios-simulator.swiftmodule
   │  │  │     │  ├─ _CodeSignature
   │  │  │     │  │  └─ CodeResources
   │  │  │     │  ├─ shared_preferences_foundation
   │  │  │     │  └─ shared_preferences_foundation_privacy.bundle
   │  │  │     │     ├─ Info.plist
   │  │  │     │     └─ PrivacyInfo.xcprivacy
   │  │  │     └─ shared_preferences_foundation_privacy.bundle
   │  │  │        ├─ Info.plist
   │  │  │        └─ PrivacyInfo.xcprivacy
   │  │  ├─ XCBuildData
   │  │  │  └─ PIFCache
   │  │  │     ├─ project
   │  │  │     │  └─ PROJECT@v11_mod=347f83010b3105617d984ce95266a9de_hash=bfdfe7dc352907fc980b868725387e98plugins=1OJSG6M1FOV3XYQCBH7Z29RZ0FPR9XDE1-json
   │  │  │     ├─ target
   │  │  │     │  ├─ TARGET@v11_hash=0914298d9d2a0d521b0edd6e70ba8539-json
   │  │  │     │  ├─ TARGET@v11_hash=20dbe05d549f4dc4c0caeed518358b99-json
   │  │  │     │  ├─ TARGET@v11_hash=338bb8163559e0eb18e8d8a0b8f201d0-json
   │  │  │     │  ├─ TARGET@v11_hash=9894f155468bc34aca17ec82a973c41d-json
   │  │  │     │  ├─ TARGET@v11_hash=af04f9e68c71e4e2c8ee2d02cfb9c040-json
   │  │  │     │  ├─ TARGET@v11_hash=c5e137bc161d7ca9a8efb3627a7ef6a1-json
   │  │  │     │  └─ TARGET@v11_hash=f30c78287d60143170b77a25101c1a89-json
   │  │  │     └─ workspace
   │  │  │        └─ WORKSPACE@v11_hash=(null)_subobjects=9c1d3ee88ec6a83c8d18870859b792e5-json
   │  │  ├─ iphonesimulator
   │  │  │  └─ Runner.app
   │  │  │     ├─ AppFrameworkInfo.plist
   │  │  │     ├─ AppIcon60x60@2x.png
   │  │  │     ├─ AppIcon76x76@2x~ipad.png
   │  │  │     ├─ Assets.car
   │  │  │     ├─ Base.lproj
   │  │  │     │  ├─ LaunchScreen.storyboardc
   │  │  │     │  │  ├─ 01J-lp-oVM-view-Ze5-6b-2t3.nib
   │  │  │     │  │  ├─ Info.plist
   │  │  │     │  │  └─ UIViewController-01J-lp-oVM.nib
   │  │  │     │  └─ Main.storyboardc
   │  │  │     │     ├─ BYZ-38-t0r-view-8bC-Xf-vdC.nib
   │  │  │     │     ├─ Info.plist
   │  │  │     │     └─ UIViewController-BYZ-38-t0r.nib
   │  │  │     ├─ Frameworks
   │  │  │     │  ├─ App.framework
   │  │  │     │  │  ├─ App
   │  │  │     │  │  ├─ Info.plist
   │  │  │     │  │  ├─ _CodeSignature
   │  │  │     │  │  │  └─ CodeResources
   │  │  │     │  │  └─ flutter_assets
   │  │  │     │  │     ├─ AssetManifest.bin
   │  │  │     │  │     ├─ AssetManifest.json
   │  │  │     │  │     ├─ FontManifest.json
   │  │  │     │  │     ├─ NOTICES.Z
   │  │  │     │  │     ├─ NativeAssetsManifest.json
   │  │  │     │  │     ├─ assets
   │  │  │     │  │     │  └─ aristay_logo.jpg
   │  │  │     │  │     ├─ fonts
   │  │  │     │  │     │  └─ MaterialIcons-Regular.otf
   │  │  │     │  │     ├─ isolate_snapshot_data
   │  │  │     │  │     ├─ kernel_blob.bin
   │  │  │     │  │     ├─ packages
   │  │  │     │  │     │  └─ cupertino_icons
   │  │  │     │  │     │     └─ assets
   │  │  │     │  │     │        └─ CupertinoIcons.ttf
   │  │  │     │  │     ├─ shaders
   │  │  │     │  │     │  └─ ink_sparkle.frag
   │  │  │     │  │     └─ vm_snapshot_data
   │  │  │     │  ├─ Flutter.framework
   │  │  │     │  │  ├─ Flutter
   │  │  │     │  │  ├─ Headers
   │  │  │     │  │  │  ├─ Flutter.h
   │  │  │     │  │  │  ├─ FlutterAppDelegate.h
   │  │  │     │  │  │  ├─ FlutterBinaryMessenger.h
   │  │  │     │  │  │  ├─ FlutterCallbackCache.h
   │  │  │     │  │  │  ├─ FlutterChannels.h
   │  │  │     │  │  │  ├─ FlutterCodecs.h
   │  │  │     │  │  │  ├─ FlutterDartProject.h
   │  │  │     │  │  │  ├─ FlutterEngine.h
   │  │  │     │  │  │  ├─ FlutterEngineGroup.h
   │  │  │     │  │  │  ├─ FlutterHeadlessDartRunner.h
   │  │  │     │  │  │  ├─ FlutterHourFormat.h
   │  │  │     │  │  │  ├─ FlutterMacros.h
   │  │  │     │  │  │  ├─ FlutterPlatformViews.h
   │  │  │     │  │  │  ├─ FlutterPlugin.h
   │  │  │     │  │  │  ├─ FlutterPluginAppLifeCycleDelegate.h
   │  │  │     │  │  │  ├─ FlutterTexture.h
   │  │  │     │  │  │  └─ FlutterViewController.h
   │  │  │     │  │  ├─ Info.plist
   │  │  │     │  │  ├─ Modules
   │  │  │     │  │  │  └─ module.modulemap
   │  │  │     │  │  ├─ PrivacyInfo.xcprivacy
   │  │  │     │  │  ├─ _CodeSignature
   │  │  │     │  │  │  └─ CodeResources
   │  │  │     │  │  └─ icudtl.dat
   │  │  │     │  ├─ image_picker_ios.framework
   │  │  │     │  │  ├─ Info.plist
   │  │  │     │  │  ├─ _CodeSignature
   │  │  │     │  │  │  └─ CodeResources
   │  │  │     │  │  ├─ image_picker_ios
   │  │  │     │  │  └─ image_picker_ios_privacy.bundle
   │  │  │     │  │     ├─ Info.plist
   │  │  │     │  │     └─ PrivacyInfo.xcprivacy
   │  │  │     │  └─ shared_preferences_foundation.framework
   │  │  │     │     ├─ Info.plist
   │  │  │     │     ├─ _CodeSignature
   │  │  │     │     │  └─ CodeResources
   │  │  │     │     ├─ shared_preferences_foundation
   │  │  │     │     └─ shared_preferences_foundation_privacy.bundle
   │  │  │     │        ├─ Info.plist
   │  │  │     │        └─ PrivacyInfo.xcprivacy
   │  │  │     ├─ Info.plist
   │  │  │     ├─ PkgInfo
   │  │  │     ├─ Runner
   │  │  │     ├─ Runner.debug.dylib
   │  │  │     ├─ _CodeSignature
   │  │  │     │  └─ CodeResources
   │  │  │     └─ __preview.dylib
   │  │  └─ pod_inputs.fingerprint
   │  └─ native_assets
   │     └─ ios
   ├─ ios
   │  ├─ .symlinks
   │  │  └─ plugins
   │  │     ├─ image_picker_ios
   │  │     │  ├─ AUTHORS
   │  │     │  ├─ CHANGELOG.md
   │  │     │  ├─ LICENSE
   │  │     │  ├─ README.md
   │  │     │  ├─ example
   │  │     │  │  ├─ README.md
   │  │     │  │  ├─ integration_test
   │  │     │  │  │  └─ image_picker_test.dart
   │  │     │  │  ├─ ios
   │  │     │  │  │  ├─ Flutter
   │  │     │  │  │  │  ├─ AppFrameworkInfo.plist
   │  │     │  │  │  │  ├─ Debug.xcconfig
   │  │     │  │  │  │  └─ Release.xcconfig
   │  │     │  │  │  ├─ Podfile
   │  │     │  │  │  ├─ Runner
   │  │     │  │  │  │  ├─ AppDelegate.h
   │  │     │  │  │  │  ├─ AppDelegate.m
   │  │     │  │  │  │  ├─ Assets.xcassets
   │  │     │  │  │  │  │  ├─ AppIcon.appiconset
   │  │     │  │  │  │  │  │  ├─ Contents.json
   │  │     │  │  │  │  │  │  ├─ Icon-App-20x20@1x.png
   │  │     │  │  │  │  │  │  ├─ Icon-App-20x20@2x.png
   │  │     │  │  │  │  │  │  ├─ Icon-App-20x20@3x.png
   │  │     │  │  │  │  │  │  ├─ Icon-App-29x29@1x.png
   │  │     │  │  │  │  │  │  ├─ Icon-App-29x29@2x.png
   │  │     │  │  │  │  │  │  ├─ Icon-App-29x29@3x.png
   │  │     │  │  │  │  │  │  ├─ Icon-App-40x40@1x.png
   │  │     │  │  │  │  │  │  ├─ Icon-App-40x40@2x.png
   │  │     │  │  │  │  │  │  ├─ Icon-App-40x40@3x.png
   │  │     │  │  │  │  │  │  ├─ Icon-App-60x60@2x.png
   │  │     │  │  │  │  │  │  ├─ Icon-App-60x60@3x.png
   │  │     │  │  │  │  │  │  ├─ Icon-App-76x76@1x.png
   │  │     │  │  │  │  │  │  ├─ Icon-App-76x76@2x.png
   │  │     │  │  │  │  │  │  └─ Icon-App-83.5x83.5@2x.png
   │  │     │  │  │  │  │  └─ Contents.json
   │  │     │  │  │  │  ├─ Base.lproj
   │  │     │  │  │  │  │  ├─ LaunchScreen.storyboard
   │  │     │  │  │  │  │  └─ Main.storyboard
   │  │     │  │  │  │  ├─ Info.plist
   │  │     │  │  │  │  └─ main.m
   │  │     │  │  │  ├─ Runner.xcodeproj
   │  │     │  │  │  │  ├─ project.pbxproj
   │  │     │  │  │  │  ├─ project.xcworkspace
   │  │     │  │  │  │  │  ├─ contents.xcworkspacedata
   │  │     │  │  │  │  │  └─ xcshareddata
   │  │     │  │  │  │  │     └─ swiftpm
   │  │     │  │  │  │  │        └─ Package.resolved
   │  │     │  │  │  │  └─ xcshareddata
   │  │     │  │  │  │     └─ xcschemes
   │  │     │  │  │  │        ├─ Runner.xcscheme
   │  │     │  │  │  │        └─ RunnerUITests.xcscheme
   │  │     │  │  │  ├─ Runner.xcworkspace
   │  │     │  │  │  │  ├─ contents.xcworkspacedata
   │  │     │  │  │  │  └─ xcshareddata
   │  │     │  │  │  │     ├─ IDEWorkspaceChecks.plist
   │  │     │  │  │  │     └─ swiftpm
   │  │     │  │  │  │        └─ Package.resolved
   │  │     │  │  │  ├─ RunnerTests
   │  │     │  │  │  │  ├─ ImagePickerPluginTests.m
   │  │     │  │  │  │  ├─ ImagePickerTestImages.h
   │  │     │  │  │  │  ├─ ImagePickerTestImages.m
   │  │     │  │  │  │  ├─ ImageUtilTests.m
   │  │     │  │  │  │  ├─ Info.plist
   │  │     │  │  │  │  ├─ MetaDataUtilTests.m
   │  │     │  │  │  │  ├─ PhotoAssetUtilTests.m
   │  │     │  │  │  │  └─ PickerSaveImageToPathOperationTests.m
   │  │     │  │  │  ├─ RunnerUITests
   │  │     │  │  │  │  ├─ ImagePickerFromGalleryUITests.m
   │  │     │  │  │  │  ├─ ImagePickerFromLimitedGalleryUITests.m
   │  │     │  │  │  │  └─ Info.plist
   │  │     │  │  │  ├─ TestImages
   │  │     │  │  │  │  ├─ bmpImage.bmp
   │  │     │  │  │  │  ├─ gifImage.gif
   │  │     │  │  │  │  ├─ heicImage.heic
   │  │     │  │  │  │  ├─ icnsImage.icns
   │  │     │  │  │  │  ├─ icoImage.ico
   │  │     │  │  │  │  ├─ jpgImage.jpg
   │  │     │  │  │  │  ├─ jpgImageTall.jpg
   │  │     │  │  │  │  ├─ jpgImageWithRightOrientation.jpg
   │  │     │  │  │  │  ├─ pngImage.png
   │  │     │  │  │  │  ├─ proRawImage.dng
   │  │     │  │  │  │  ├─ tiffImage.tiff
   │  │     │  │  │  │  └─ webpImage.webp
   │  │     │  │  │  └─ image_picker_exampleTests
   │  │     │  │  │     └─ Info.plist
   │  │     │  │  ├─ lib
   │  │     │  │  │  └─ main.dart
   │  │     │  │  ├─ pubspec.yaml
   │  │     │  │  └─ test_driver
   │  │     │  │     └─ integration_test.dart
   │  │     │  ├─ ios
   │  │     │  │  ├─ image_picker_ios
   │  │     │  │  │  ├─ Package.swift
   │  │     │  │  │  └─ Sources
   │  │     │  │  │     └─ image_picker_ios
   │  │     │  │  │        ├─ FLTImagePickerImageUtil.m
   │  │     │  │  │        ├─ FLTImagePickerMetaDataUtil.m
   │  │     │  │  │        ├─ FLTImagePickerPhotoAssetUtil.m
   │  │     │  │  │        ├─ FLTImagePickerPlugin.m
   │  │     │  │  │        ├─ FLTPHPickerSaveImageToPathOperation.m
   │  │     │  │  │        ├─ Resources
   │  │     │  │  │        │  └─ PrivacyInfo.xcprivacy
   │  │     │  │  │        ├─ include
   │  │     │  │  │        │  ├─ ImagePickerPlugin.modulemap
   │  │     │  │  │        │  ├─ image_picker_ios
   │  │     │  │  │        │  │  ├─ FLTImagePickerImageUtil.h
   │  │     │  │  │        │  │  ├─ FLTImagePickerMetaDataUtil.h
   │  │     │  │  │        │  │  ├─ FLTImagePickerPhotoAssetUtil.h
   │  │     │  │  │        │  │  ├─ FLTImagePickerPlugin.h
   │  │     │  │  │        │  │  ├─ FLTImagePickerPlugin_Test.h
   │  │     │  │  │        │  │  ├─ FLTPHPickerSaveImageToPathOperation.h
   │  │     │  │  │        │  │  └─ messages.g.h
   │  │     │  │  │        │  └─ image_picker_ios-umbrella.h
   │  │     │  │  │        └─ messages.g.m
   │  │     │  │  └─ image_picker_ios.podspec
   │  │     │  ├─ lib
   │  │     │  │  ├─ image_picker_ios.dart
   │  │     │  │  └─ src
   │  │     │  │     └─ messages.g.dart
   │  │     │  ├─ pigeons
   │  │     │  │  ├─ copyright.txt
   │  │     │  │  └─ messages.dart
   │  │     │  ├─ pubspec.yaml
   │  │     │  └─ test
   │  │     │     ├─ image_picker_ios_test.dart
   │  │     │     └─ test_api.g.dart
   │  │     └─ shared_preferences_foundation
   │  │        ├─ AUTHORS
   │  │        ├─ CHANGELOG.md
   │  │        ├─ LICENSE
   │  │        ├─ README.md
   │  │        ├─ darwin
   │  │        │  ├─ Tests
   │  │        │  │  └─ RunnerTests.swift
   │  │        │  ├─ shared_preferences_foundation
   │  │        │  │  ├─ Package.swift
   │  │        │  │  └─ Sources
   │  │        │  │     └─ shared_preferences_foundation
   │  │        │  │        ├─ Resources
   │  │        │  │        │  └─ PrivacyInfo.xcprivacy
   │  │        │  │        ├─ SharedPreferencesPlugin.swift
   │  │        │  │        └─ messages.g.swift
   │  │        │  └─ shared_preferences_foundation.podspec
   │  │        ├─ example
   │  │        │  ├─ README.md
   │  │        │  ├─ integration_test
   │  │        │  │  └─ shared_preferences_test.dart
   │  │        │  ├─ ios
   │  │        │  │  ├─ Flutter
   │  │        │  │  │  ├─ AppFrameworkInfo.plist
   │  │        │  │  │  ├─ Debug.xcconfig
   │  │        │  │  │  └─ Release.xcconfig
   │  │        │  │  ├─ Podfile
   │  │        │  │  ├─ Runner
   │  │        │  │  │  ├─ AppDelegate.swift
   │  │        │  │  │  ├─ Assets.xcassets
   │  │        │  │  │  │  ├─ AppIcon.appiconset
   │  │        │  │  │  │  │  ├─ Contents.json
   │  │        │  │  │  │  │  ├─ Icon-App-1024x1024@1x.png
   │  │        │  │  │  │  │  ├─ Icon-App-20x20@1x.png
   │  │        │  │  │  │  │  ├─ Icon-App-20x20@2x.png
   │  │        │  │  │  │  │  ├─ Icon-App-20x20@3x.png
   │  │        │  │  │  │  │  ├─ Icon-App-29x29@1x.png
   │  │        │  │  │  │  │  ├─ Icon-App-29x29@2x.png
   │  │        │  │  │  │  │  ├─ Icon-App-29x29@3x.png
   │  │        │  │  │  │  │  ├─ Icon-App-40x40@1x.png
   │  │        │  │  │  │  │  ├─ Icon-App-40x40@2x.png
   │  │        │  │  │  │  │  ├─ Icon-App-40x40@3x.png
   │  │        │  │  │  │  │  ├─ Icon-App-60x60@2x.png
   │  │        │  │  │  │  │  ├─ Icon-App-60x60@3x.png
   │  │        │  │  │  │  │  ├─ Icon-App-76x76@1x.png
   │  │        │  │  │  │  │  ├─ Icon-App-76x76@2x.png
   │  │        │  │  │  │  │  └─ Icon-App-83.5x83.5@2x.png
   │  │        │  │  │  │  └─ LaunchImage.imageset
   │  │        │  │  │  │     ├─ Contents.json
   │  │        │  │  │  │     ├─ LaunchImage.png
   │  │        │  │  │  │     ├─ LaunchImage@2x.png
   │  │        │  │  │  │     ├─ LaunchImage@3x.png
   │  │        │  │  │  │     └─ README.md
   │  │        │  │  │  ├─ Base.lproj
   │  │        │  │  │  │  ├─ LaunchScreen.storyboard
   │  │        │  │  │  │  └─ Main.storyboard
   │  │        │  │  │  ├─ Info.plist
   │  │        │  │  │  └─ Runner-Bridging-Header.h
   │  │        │  │  ├─ Runner.xcodeproj
   │  │        │  │  │  ├─ project.pbxproj
   │  │        │  │  │  ├─ project.xcworkspace
   │  │        │  │  │  │  ├─ contents.xcworkspacedata
   │  │        │  │  │  │  └─ xcshareddata
   │  │        │  │  │  │     ├─ IDEWorkspaceChecks.plist
   │  │        │  │  │  │     └─ WorkspaceSettings.xcsettings
   │  │        │  │  │  └─ xcshareddata
   │  │        │  │  │     └─ xcschemes
   │  │        │  │  │        └─ Runner.xcscheme
   │  │        │  │  └─ Runner.xcworkspace
   │  │        │  │     ├─ contents.xcworkspacedata
   │  │        │  │     └─ xcshareddata
   │  │        │  │        ├─ IDEWorkspaceChecks.plist
   │  │        │  │        └─ WorkspaceSettings.xcsettings
   │  │        │  ├─ lib
   │  │        │  │  └─ main.dart
   │  │        │  ├─ macos
   │  │        │  │  ├─ Flutter
   │  │        │  │  │  ├─ Flutter-Debug.xcconfig
   │  │        │  │  │  └─ Flutter-Release.xcconfig
   │  │        │  │  ├─ Podfile
   │  │        │  │  ├─ Runner
   │  │        │  │  │  ├─ AppDelegate.swift
   │  │        │  │  │  ├─ Assets.xcassets
   │  │        │  │  │  │  └─ AppIcon.appiconset
   │  │        │  │  │  │     ├─ Contents.json
   │  │        │  │  │  │     ├─ app_icon_1024.png
   │  │        │  │  │  │     ├─ app_icon_128.png
   │  │        │  │  │  │     ├─ app_icon_16.png
   │  │        │  │  │  │     ├─ app_icon_256.png
   │  │        │  │  │  │     ├─ app_icon_32.png
   │  │        │  │  │  │     ├─ app_icon_512.png
   │  │        │  │  │  │     └─ app_icon_64.png
   │  │        │  │  │  ├─ Base.lproj
   │  │        │  │  │  │  └─ MainMenu.xib
   │  │        │  │  │  ├─ Configs
   │  │        │  │  │  │  ├─ AppInfo.xcconfig
   │  │        │  │  │  │  ├─ Debug.xcconfig
   │  │        │  │  │  │  ├─ Release.xcconfig
   │  │        │  │  │  │  └─ Warnings.xcconfig
   │  │        │  │  │  ├─ DebugProfile.entitlements
   │  │        │  │  │  ├─ Info.plist
   │  │        │  │  │  ├─ MainFlutterWindow.swift
   │  │        │  │  │  └─ Release.entitlements
   │  │        │  │  ├─ Runner.xcodeproj
   │  │        │  │  │  ├─ project.pbxproj
   │  │        │  │  │  └─ xcshareddata
   │  │        │  │  │     └─ xcschemes
   │  │        │  │  │        └─ Runner.xcscheme
   │  │        │  │  ├─ Runner.xcworkspace
   │  │        │  │  │  ├─ contents.xcworkspacedata
   │  │        │  │  │  └─ xcshareddata
   │  │        │  │  │     └─ IDEWorkspaceChecks.plist
   │  │        │  │  └─ RunnerTests
   │  │        │  │     └─ Info.plist
   │  │        │  ├─ pubspec.yaml
   │  │        │  └─ test_driver
   │  │        │     └─ integration_test.dart
   │  │        ├─ lib
   │  │        │  ├─ shared_preferences_foundation.dart
   │  │        │  └─ src
   │  │        │     ├─ messages.g.dart
   │  │        │     ├─ shared_preferences_async_foundation.dart
   │  │        │     └─ shared_preferences_foundation.dart
   │  │        ├─ pigeons
   │  │        │  ├─ copyright_header.txt
   │  │        │  └─ messages.dart
   │  │        ├─ pubspec.yaml
   │  │        └─ test
   │  │           ├─ shared_preferences_async_foundation_test.dart
   │  │           ├─ shared_preferences_foundation_test.dart
   │  │           └─ test_api.g.dart
   │  ├─ Flutter
   │  │  ├─ AppFrameworkInfo.plist
   │  │  ├─ Debug.xcconfig
   │  │  ├─ Flutter.podspec
   │  │  ├─ Generated.xcconfig
   │  │  ├─ Release.xcconfig
   │  │  └─ flutter_export_environment.sh
   │  ├─ Podfile
   │  ├─ Podfile.lock
   │  ├─ Pods
   │  │  ├─ Firebase
   │  │  │  ├─ CoreOnly
   │  │  │  │  └─ Sources
   │  │  │  │     ├─ Firebase.h
   │  │  │  │     └─ module.modulemap
   │  │  │  ├─ LICENSE
   │  │  │  └─ README.md
   │  │  ├─ FirebaseCore
   │  │  │  ├─ FirebaseCore
   │  │  │  │  ├─ Extension
   │  │  │  │  │  ├─ FIRAppInternal.h
   │  │  │  │  │  ├─ FIRComponent.h
   │  │  │  │  │  ├─ FIRComponentContainer.h
   │  │  │  │  │  ├─ FIRComponentType.h
   │  │  │  │  │  ├─ FIRHeartbeatLogger.h
   │  │  │  │  │  ├─ FIRLibrary.h
   │  │  │  │  │  ├─ FIRLogger.h
   │  │  │  │  │  └─ FirebaseCoreInternal.h
   │  │  │  │  └─ Sources
   │  │  │  │     ├─ FIRAnalyticsConfiguration.h
   │  │  │  │     ├─ FIRAnalyticsConfiguration.m
   │  │  │  │     ├─ FIRApp.m
   │  │  │  │     ├─ FIRBundleUtil.h
   │  │  │  │     ├─ FIRBundleUtil.m
   │  │  │  │     ├─ FIRComponent.m
   │  │  │  │     ├─ FIRComponentContainer.m
   │  │  │  │     ├─ FIRComponentContainerInternal.h
   │  │  │  │     ├─ FIRComponentType.m
   │  │  │  │     ├─ FIRConfiguration.m
   │  │  │  │     ├─ FIRConfigurationInternal.h
   │  │  │  │     ├─ FIRFirebaseUserAgent.h
   │  │  │  │     ├─ FIRFirebaseUserAgent.m
   │  │  │  │     ├─ FIRHeartbeatLogger.m
   │  │  │  │     ├─ FIRLogger.m
   │  │  │  │     ├─ FIROptions.m
   │  │  │  │     ├─ FIROptionsInternal.h
   │  │  │  │     ├─ FIRTimestamp.m
   │  │  │  │     ├─ FIRTimestampInternal.h
   │  │  │  │     ├─ FIRVersion.m
   │  │  │  │     ├─ Public
   │  │  │  │     │  └─ FirebaseCore
   │  │  │  │     │     ├─ FIRApp.h
   │  │  │  │     │     ├─ FIRConfiguration.h
   │  │  │  │     │     ├─ FIRLoggerLevel.h
   │  │  │  │     │     ├─ FIROptions.h
   │  │  │  │     │     ├─ FIRTimestamp.h
   │  │  │  │     │     ├─ FIRVersion.h
   │  │  │  │     │     └─ FirebaseCore.h
   │  │  │  │     └─ Resources
   │  │  │  │        └─ PrivacyInfo.xcprivacy
   │  │  │  ├─ LICENSE
   │  │  │  └─ README.md
   │  │  ├─ FirebaseCoreInternal
   │  │  │  ├─ FirebaseCore
   │  │  │  │  └─ Internal
   │  │  │  │     └─ Sources
   │  │  │  │        ├─ HeartbeatLogging
   │  │  │  │        │  ├─ Heartbeat.swift
   │  │  │  │        │  ├─ HeartbeatController.swift
   │  │  │  │        │  ├─ HeartbeatLoggingTestUtils.swift
   │  │  │  │        │  ├─ HeartbeatStorage.swift
   │  │  │  │        │  ├─ HeartbeatsBundle.swift
   │  │  │  │        │  ├─ HeartbeatsPayload.swift
   │  │  │  │        │  ├─ RingBuffer.swift
   │  │  │  │        │  ├─ Storage.swift
   │  │  │  │        │  ├─ StorageFactory.swift
   │  │  │  │        │  ├─ WeakContainer.swift
   │  │  │  │        │  ├─ _ObjC_HeartbeatController.swift
   │  │  │  │        │  └─ _ObjC_HeartbeatsPayload.swift
   │  │  │  │        ├─ Resources
   │  │  │  │        │  └─ PrivacyInfo.xcprivacy
   │  │  │  │        └─ Utilities
   │  │  │  │           ├─ AtomicBox.swift
   │  │  │  │           └─ FIRAllocatedUnfairLock.swift
   │  │  │  ├─ LICENSE
   │  │  │  └─ README.md
   │  │  ├─ FirebaseInstallations
   │  │  │  ├─ FirebaseCore
   │  │  │  │  └─ Extension
   │  │  │  │     ├─ FIRAppInternal.h
   │  │  │  │     ├─ FIRComponent.h
   │  │  │  │     ├─ FIRComponentContainer.h
   │  │  │  │     ├─ FIRComponentType.h
   │  │  │  │     ├─ FIRHeartbeatLogger.h
   │  │  │  │     ├─ FIRLibrary.h
   │  │  │  │     ├─ FIRLogger.h
   │  │  │  │     └─ FirebaseCoreInternal.h
   │  │  │  ├─ FirebaseInstallations
   │  │  │  │  └─ Source
   │  │  │  │     └─ Library
   │  │  │  │        ├─ Errors
   │  │  │  │        │  ├─ FIRInstallationsErrorUtil.h
   │  │  │  │        │  ├─ FIRInstallationsErrorUtil.m
   │  │  │  │        │  ├─ FIRInstallationsHTTPError.h
   │  │  │  │        │  └─ FIRInstallationsHTTPError.m
   │  │  │  │        ├─ FIRInstallations.m
   │  │  │  │        ├─ FIRInstallationsAuthTokenResult.m
   │  │  │  │        ├─ FIRInstallationsAuthTokenResultInternal.h
   │  │  │  │        ├─ FIRInstallationsItem.h
   │  │  │  │        ├─ FIRInstallationsItem.m
   │  │  │  │        ├─ FIRInstallationsLogger.h
   │  │  │  │        ├─ FIRInstallationsLogger.m
   │  │  │  │        ├─ IIDMigration
   │  │  │  │        │  ├─ FIRInstallationsIIDStore.h
   │  │  │  │        │  ├─ FIRInstallationsIIDStore.m
   │  │  │  │        │  ├─ FIRInstallationsIIDTokenStore.h
   │  │  │  │        │  └─ FIRInstallationsIIDTokenStore.m
   │  │  │  │        ├─ InstallationsAPI
   │  │  │  │        │  ├─ FIRInstallationsAPIService.h
   │  │  │  │        │  ├─ FIRInstallationsAPIService.m
   │  │  │  │        │  ├─ FIRInstallationsItem+RegisterInstallationAPI.h
   │  │  │  │        │  └─ FIRInstallationsItem+RegisterInstallationAPI.m
   │  │  │  │        ├─ InstallationsIDController
   │  │  │  │        │  ├─ FIRCurrentDateProvider.h
   │  │  │  │        │  ├─ FIRCurrentDateProvider.m
   │  │  │  │        │  ├─ FIRInstallationsBackoffController.h
   │  │  │  │        │  ├─ FIRInstallationsBackoffController.m
   │  │  │  │        │  ├─ FIRInstallationsIDController.h
   │  │  │  │        │  ├─ FIRInstallationsIDController.m
   │  │  │  │        │  ├─ FIRInstallationsSingleOperationPromiseCache.h
   │  │  │  │        │  ├─ FIRInstallationsSingleOperationPromiseCache.m
   │  │  │  │        │  └─ FIRInstallationsStatus.h
   │  │  │  │        ├─ InstallationsStore
   │  │  │  │        │  ├─ FIRInstallationsStore.h
   │  │  │  │        │  ├─ FIRInstallationsStore.m
   │  │  │  │        │  ├─ FIRInstallationsStoredAuthToken.h
   │  │  │  │        │  ├─ FIRInstallationsStoredAuthToken.m
   │  │  │  │        │  ├─ FIRInstallationsStoredItem.h
   │  │  │  │        │  └─ FIRInstallationsStoredItem.m
   │  │  │  │        ├─ Private
   │  │  │  │        │  └─ FirebaseInstallationsInternal.h
   │  │  │  │        ├─ Public
   │  │  │  │        │  └─ FirebaseInstallations
   │  │  │  │        │     ├─ FIRInstallations.h
   │  │  │  │        │     ├─ FIRInstallationsAuthTokenResult.h
   │  │  │  │        │     ├─ FIRInstallationsErrors.h
   │  │  │  │        │     └─ FirebaseInstallations.h
   │  │  │  │        └─ Resources
   │  │  │  │           └─ PrivacyInfo.xcprivacy
   │  │  │  ├─ LICENSE
   │  │  │  └─ README.md
   │  │  ├─ FirebaseMessaging
   │  │  │  ├─ FirebaseCore
   │  │  │  │  └─ Extension
   │  │  │  │     ├─ FIRAppInternal.h
   │  │  │  │     ├─ FIRComponent.h
   │  │  │  │     ├─ FIRComponentContainer.h
   │  │  │  │     ├─ FIRComponentType.h
   │  │  │  │     ├─ FIRHeartbeatLogger.h
   │  │  │  │     ├─ FIRLibrary.h
   │  │  │  │     ├─ FIRLogger.h
   │  │  │  │     └─ FirebaseCoreInternal.h
   │  │  │  ├─ FirebaseInstallations
   │  │  │  │  └─ Source
   │  │  │  │     └─ Library
   │  │  │  │        └─ Private
   │  │  │  │           └─ FirebaseInstallationsInternal.h
   │  │  │  ├─ FirebaseMessaging
   │  │  │  │  ├─ Interop
   │  │  │  │  │  └─ FIRMessagingInterop.h
   │  │  │  │  └─ Sources
   │  │  │  │     ├─ FIRMessaging+ExtensionHelper.m
   │  │  │  │     ├─ FIRMessaging.m
   │  │  │  │     ├─ FIRMessagingAnalytics.h
   │  │  │  │     ├─ FIRMessagingAnalytics.m
   │  │  │  │     ├─ FIRMessagingCode.h
   │  │  │  │     ├─ FIRMessagingConstants.h
   │  │  │  │     ├─ FIRMessagingConstants.m
   │  │  │  │     ├─ FIRMessagingContextManagerService.h
   │  │  │  │     ├─ FIRMessagingContextManagerService.m
   │  │  │  │     ├─ FIRMessagingDefines.h
   │  │  │  │     ├─ FIRMessagingExtensionHelper.m
   │  │  │  │     ├─ FIRMessagingLogger.h
   │  │  │  │     ├─ FIRMessagingLogger.m
   │  │  │  │     ├─ FIRMessagingPendingTopicsList.h
   │  │  │  │     ├─ FIRMessagingPendingTopicsList.m
   │  │  │  │     ├─ FIRMessagingPersistentSyncMessage.h
   │  │  │  │     ├─ FIRMessagingPersistentSyncMessage.m
   │  │  │  │     ├─ FIRMessagingPubSub.h
   │  │  │  │     ├─ FIRMessagingPubSub.m
   │  │  │  │     ├─ FIRMessagingRemoteNotificationsProxy.h
   │  │  │  │     ├─ FIRMessagingRemoteNotificationsProxy.m
   │  │  │  │     ├─ FIRMessagingRmqManager.h
   │  │  │  │     ├─ FIRMessagingRmqManager.m
   │  │  │  │     ├─ FIRMessagingSyncMessageManager.h
   │  │  │  │     ├─ FIRMessagingSyncMessageManager.m
   │  │  │  │     ├─ FIRMessagingTopicOperation.h
   │  │  │  │     ├─ FIRMessagingTopicOperation.m
   │  │  │  │     ├─ FIRMessagingTopicsCommon.h
   │  │  │  │     ├─ FIRMessagingUtilities.h
   │  │  │  │     ├─ FIRMessagingUtilities.m
   │  │  │  │     ├─ FIRMessaging_Private.h
   │  │  │  │     ├─ FirebaseMessaging.h
   │  │  │  │     ├─ NSDictionary+FIRMessaging.h
   │  │  │  │     ├─ NSDictionary+FIRMessaging.m
   │  │  │  │     ├─ NSError+FIRMessaging.h
   │  │  │  │     ├─ NSError+FIRMessaging.m
   │  │  │  │     ├─ Protogen
   │  │  │  │     │  └─ nanopb
   │  │  │  │     │     ├─ me.nanopb.c
   │  │  │  │     │     └─ me.nanopb.h
   │  │  │  │     ├─ Public
   │  │  │  │     │  └─ FirebaseMessaging
   │  │  │  │     │     ├─ FIRMessaging+ExtensionHelper.h
   │  │  │  │     │     ├─ FIRMessaging.h
   │  │  │  │     │     ├─ FIRMessagingExtensionHelper.h
   │  │  │  │     │     └─ FirebaseMessaging.h
   │  │  │  │     ├─ Resources
   │  │  │  │     │  └─ PrivacyInfo.xcprivacy
   │  │  │  │     └─ Token
   │  │  │  │        ├─ FIRMessagingAPNSInfo.h
   │  │  │  │        ├─ FIRMessagingAPNSInfo.m
   │  │  │  │        ├─ FIRMessagingAuthKeychain.h
   │  │  │  │        ├─ FIRMessagingAuthKeychain.m
   │  │  │  │        ├─ FIRMessagingAuthService.h
   │  │  │  │        ├─ FIRMessagingAuthService.m
   │  │  │  │        ├─ FIRMessagingBackupExcludedPlist.h
   │  │  │  │        ├─ FIRMessagingBackupExcludedPlist.m
   │  │  │  │        ├─ FIRMessagingCheckinPreferences.h
   │  │  │  │        ├─ FIRMessagingCheckinPreferences.m
   │  │  │  │        ├─ FIRMessagingCheckinService.h
   │  │  │  │        ├─ FIRMessagingCheckinService.m
   │  │  │  │        ├─ FIRMessagingCheckinStore.h
   │  │  │  │        ├─ FIRMessagingCheckinStore.m
   │  │  │  │        ├─ FIRMessagingKeychain.h
   │  │  │  │        ├─ FIRMessagingKeychain.m
   │  │  │  │        ├─ FIRMessagingTokenDeleteOperation.h
   │  │  │  │        ├─ FIRMessagingTokenDeleteOperation.m
   │  │  │  │        ├─ FIRMessagingTokenFetchOperation.h
   │  │  │  │        ├─ FIRMessagingTokenFetchOperation.m
   │  │  │  │        ├─ FIRMessagingTokenInfo.h
   │  │  │  │        ├─ FIRMessagingTokenInfo.m
   │  │  │  │        ├─ FIRMessagingTokenManager.h
   │  │  │  │        ├─ FIRMessagingTokenManager.m
   │  │  │  │        ├─ FIRMessagingTokenOperation.h
   │  │  │  │        ├─ FIRMessagingTokenOperation.m
   │  │  │  │        ├─ FIRMessagingTokenStore.h
   │  │  │  │        └─ FIRMessagingTokenStore.m
   │  │  │  ├─ Interop
   │  │  │  │  └─ Analytics
   │  │  │  │     └─ Public
   │  │  │  │        ├─ FIRAnalyticsInterop.h
   │  │  │  │        ├─ FIRAnalyticsInteropListener.h
   │  │  │  │        ├─ FIRInteropEventNames.h
   │  │  │  │        └─ FIRInteropParameterNames.h
   │  │  │  ├─ LICENSE
   │  │  │  └─ README.md
   │  │  ├─ GoogleDataTransport
   │  │  │  ├─ GoogleDataTransport
   │  │  │  │  ├─ GDTCCTLibrary
   │  │  │  │  │  ├─ GDTCCTCompressionHelper.m
   │  │  │  │  │  ├─ GDTCCTNanopbHelpers.m
   │  │  │  │  │  ├─ GDTCCTURLSessionDataResponse.m
   │  │  │  │  │  ├─ GDTCCTUploadOperation.m
   │  │  │  │  │  ├─ GDTCCTUploader.m
   │  │  │  │  │  ├─ GDTCOREvent+GDTCCTSupport.m
   │  │  │  │  │  ├─ GDTCOREvent+GDTMetricsSupport.m
   │  │  │  │  │  ├─ GDTCORMetrics+GDTCCTSupport.m
   │  │  │  │  │  ├─ Private
   │  │  │  │  │  │  ├─ GDTCCTCompressionHelper.h
   │  │  │  │  │  │  ├─ GDTCCTNanopbHelpers.h
   │  │  │  │  │  │  ├─ GDTCCTURLSessionDataResponse.h
   │  │  │  │  │  │  ├─ GDTCCTUploadOperation.h
   │  │  │  │  │  │  ├─ GDTCCTUploader.h
   │  │  │  │  │  │  ├─ GDTCOREvent+GDTMetricsSupport.h
   │  │  │  │  │  │  └─ GDTCORMetrics+GDTCCTSupport.h
   │  │  │  │  │  ├─ Protogen
   │  │  │  │  │  │  └─ nanopb
   │  │  │  │  │  │     ├─ cct.nanopb.c
   │  │  │  │  │  │     ├─ cct.nanopb.h
   │  │  │  │  │  │     ├─ client_metrics.nanopb.c
   │  │  │  │  │  │     ├─ client_metrics.nanopb.h
   │  │  │  │  │  │     ├─ compliance.nanopb.c
   │  │  │  │  │  │     ├─ compliance.nanopb.h
   │  │  │  │  │  │     ├─ external_prequest_context.nanopb.c
   │  │  │  │  │  │     ├─ external_prequest_context.nanopb.h
   │  │  │  │  │  │     ├─ external_privacy_context.nanopb.c
   │  │  │  │  │  │     └─ external_privacy_context.nanopb.h
   │  │  │  │  │  └─ Public
   │  │  │  │  │     └─ GDTCOREvent+GDTCCTSupport.h
   │  │  │  │  ├─ GDTCORLibrary
   │  │  │  │  │  ├─ GDTCORAssert.m
   │  │  │  │  │  ├─ GDTCORClock.m
   │  │  │  │  │  ├─ GDTCORConsoleLogger.m
   │  │  │  │  │  ├─ GDTCORDirectorySizeTracker.m
   │  │  │  │  │  ├─ GDTCOREndpoints.m
   │  │  │  │  │  ├─ GDTCOREvent.m
   │  │  │  │  │  ├─ GDTCORFlatFileStorage+Promises.m
   │  │  │  │  │  ├─ GDTCORFlatFileStorage.m
   │  │  │  │  │  ├─ GDTCORLifecycle.m
   │  │  │  │  │  ├─ GDTCORLogSourceMetrics.m
   │  │  │  │  │  ├─ GDTCORMetrics.m
   │  │  │  │  │  ├─ GDTCORMetricsController.m
   │  │  │  │  │  ├─ GDTCORMetricsMetadata.m
   │  │  │  │  │  ├─ GDTCORPlatform.m
   │  │  │  │  │  ├─ GDTCORProductData.m
   │  │  │  │  │  ├─ GDTCORReachability.m
   │  │  │  │  │  ├─ GDTCORRegistrar.m
   │  │  │  │  │  ├─ GDTCORStorageEventSelector.m
   │  │  │  │  │  ├─ GDTCORStorageMetadata.m
   │  │  │  │  │  ├─ GDTCORTransformer.m
   │  │  │  │  │  ├─ GDTCORTransport.m
   │  │  │  │  │  ├─ GDTCORUploadBatch.m
   │  │  │  │  │  ├─ GDTCORUploadCoordinator.m
   │  │  │  │  │  ├─ Internal
   │  │  │  │  │  │  ├─ GDTCORAssert.h
   │  │  │  │  │  │  ├─ GDTCORDirectorySizeTracker.h
   │  │  │  │  │  │  ├─ GDTCOREventDropReason.h
   │  │  │  │  │  │  ├─ GDTCORLifecycle.h
   │  │  │  │  │  │  ├─ GDTCORMetricsControllerProtocol.h
   │  │  │  │  │  │  ├─ GDTCORPlatform.h
   │  │  │  │  │  │  ├─ GDTCORReachability.h
   │  │  │  │  │  │  ├─ GDTCORRegistrar.h
   │  │  │  │  │  │  ├─ GDTCORStorageEventSelector.h
   │  │  │  │  │  │  ├─ GDTCORStorageProtocol.h
   │  │  │  │  │  │  ├─ GDTCORStorageSizeBytes.h
   │  │  │  │  │  │  └─ GDTCORUploader.h
   │  │  │  │  │  ├─ Private
   │  │  │  │  │  │  ├─ GDTCOREndpoints_Private.h
   │  │  │  │  │  │  ├─ GDTCOREvent_Private.h
   │  │  │  │  │  │  ├─ GDTCORFlatFileStorage+Promises.h
   │  │  │  │  │  │  ├─ GDTCORFlatFileStorage.h
   │  │  │  │  │  │  ├─ GDTCORLogSourceMetrics.h
   │  │  │  │  │  │  ├─ GDTCORMetrics.h
   │  │  │  │  │  │  ├─ GDTCORMetricsController.h
   │  │  │  │  │  │  ├─ GDTCORMetricsMetadata.h
   │  │  │  │  │  │  ├─ GDTCORReachability_Private.h
   │  │  │  │  │  │  ├─ GDTCORRegistrar_Private.h
   │  │  │  │  │  │  ├─ GDTCORStorageMetadata.h
   │  │  │  │  │  │  ├─ GDTCORTransformer.h
   │  │  │  │  │  │  ├─ GDTCORTransformer_Private.h
   │  │  │  │  │  │  ├─ GDTCORTransport_Private.h
   │  │  │  │  │  │  ├─ GDTCORUploadBatch.h
   │  │  │  │  │  │  └─ GDTCORUploadCoordinator.h
   │  │  │  │  │  └─ Public
   │  │  │  │  │     └─ GoogleDataTransport
   │  │  │  │  │        ├─ GDTCORClock.h
   │  │  │  │  │        ├─ GDTCORConsoleLogger.h
   │  │  │  │  │        ├─ GDTCOREndpoints.h
   │  │  │  │  │        ├─ GDTCOREvent.h
   │  │  │  │  │        ├─ GDTCOREventDataObject.h
   │  │  │  │  │        ├─ GDTCOREventTransformer.h
   │  │  │  │  │        ├─ GDTCORProductData.h
   │  │  │  │  │        ├─ GDTCORTargets.h
   │  │  │  │  │        ├─ GDTCORTransport.h
   │  │  │  │  │        └─ GoogleDataTransport.h
   │  │  │  │  └─ Resources
   │  │  │  │     └─ PrivacyInfo.xcprivacy
   │  │  │  ├─ LICENSE
   │  │  │  └─ README.md
   │  │  ├─ GoogleUtilities
   │  │  │  ├─ GoogleUtilities
   │  │  │  │  ├─ AppDelegateSwizzler
   │  │  │  │  │  ├─ GULAppDelegateSwizzler.m
   │  │  │  │  │  ├─ GULSceneDelegateSwizzler.m
   │  │  │  │  │  ├─ Internal
   │  │  │  │  │  │  ├─ GULAppDelegateSwizzler_Private.h
   │  │  │  │  │  │  └─ GULSceneDelegateSwizzler_Private.h
   │  │  │  │  │  └─ Public
   │  │  │  │  │     └─ GoogleUtilities
   │  │  │  │  │        ├─ GULAppDelegateSwizzler.h
   │  │  │  │  │        ├─ GULApplication.h
   │  │  │  │  │        └─ GULSceneDelegateSwizzler.h
   │  │  │  │  ├─ Common
   │  │  │  │  │  └─ GULLoggerCodes.h
   │  │  │  │  ├─ Environment
   │  │  │  │  │  ├─ GULAppEnvironmentUtil.m
   │  │  │  │  │  ├─ NetworkInfo
   │  │  │  │  │  │  └─ GULNetworkInfo.m
   │  │  │  │  │  ├─ Public
   │  │  │  │  │  │  └─ GoogleUtilities
   │  │  │  │  │  │     ├─ GULAppEnvironmentUtil.h
   │  │  │  │  │  │     ├─ GULKeychainStorage.h
   │  │  │  │  │  │     ├─ GULKeychainUtils.h
   │  │  │  │  │  │     └─ GULNetworkInfo.h
   │  │  │  │  │  └─ SecureStorage
   │  │  │  │  │     ├─ GULKeychainStorage.m
   │  │  │  │  │     └─ GULKeychainUtils.m
   │  │  │  │  ├─ Logger
   │  │  │  │  │  ├─ GULLogger.m
   │  │  │  │  │  └─ Public
   │  │  │  │  │     └─ GoogleUtilities
   │  │  │  │  │        ├─ GULLogger.h
   │  │  │  │  │        └─ GULLoggerLevel.h
   │  │  │  │  ├─ NSData+zlib
   │  │  │  │  │  ├─ GULNSData+zlib.m
   │  │  │  │  │  └─ Public
   │  │  │  │  │     └─ GoogleUtilities
   │  │  │  │  │        └─ GULNSData+zlib.h
   │  │  │  │  ├─ Network
   │  │  │  │  │  ├─ GULMutableDictionary.m
   │  │  │  │  │  ├─ GULNetwork.m
   │  │  │  │  │  ├─ GULNetworkConstants.m
   │  │  │  │  │  ├─ GULNetworkInternal.h
   │  │  │  │  │  ├─ GULNetworkURLSession.m
   │  │  │  │  │  └─ Public
   │  │  │  │  │     └─ GoogleUtilities
   │  │  │  │  │        ├─ GULMutableDictionary.h
   │  │  │  │  │        ├─ GULNetwork.h
   │  │  │  │  │        ├─ GULNetworkConstants.h
   │  │  │  │  │        ├─ GULNetworkLoggerProtocol.h
   │  │  │  │  │        ├─ GULNetworkMessageCode.h
   │  │  │  │  │        └─ GULNetworkURLSession.h
   │  │  │  │  ├─ Privacy
   │  │  │  │  │  └─ Resources
   │  │  │  │  │     └─ PrivacyInfo.xcprivacy
   │  │  │  │  ├─ Reachability
   │  │  │  │  │  ├─ GULReachabilityChecker+Internal.h
   │  │  │  │  │  ├─ GULReachabilityChecker.m
   │  │  │  │  │  ├─ GULReachabilityMessageCode.h
   │  │  │  │  │  └─ Public
   │  │  │  │  │     └─ GoogleUtilities
   │  │  │  │  │        └─ GULReachabilityChecker.h
   │  │  │  │  └─ UserDefaults
   │  │  │  │     ├─ GULUserDefaults.m
   │  │  │  │     └─ Public
   │  │  │  │        └─ GoogleUtilities
   │  │  │  │           └─ GULUserDefaults.h
   │  │  │  ├─ LICENSE
   │  │  │  ├─ README.md
   │  │  │  └─ third_party
   │  │  │     └─ IsAppEncrypted
   │  │  │        ├─ IsAppEncrypted.m
   │  │  │        └─ Public
   │  │  │           └─ IsAppEncrypted.h
   │  │  ├─ Headers
   │  │  │  ├─ Private
   │  │  │  └─ Public
   │  │  ├─ Local Podspecs
   │  │  │  ├─ Flutter.podspec.json
   │  │  │  ├─ firebase_core.podspec.json
   │  │  │  ├─ firebase_messaging.podspec.json
   │  │  │  ├─ flutter_local_notifications.podspec.json
   │  │  │  ├─ image_picker_ios.podspec.json
   │  │  │  └─ shared_preferences_foundation.podspec.json
   │  │  ├─ Manifest.lock
   │  │  ├─ Pods.xcodeproj
   │  │  │  ├─ project.pbxproj
   │  │  │  └─ xcuserdata
   │  │  │     └─ duylam1407.xcuserdatad
   │  │  │        └─ xcschemes
   │  │  │           ├─ Flutter.xcscheme
   │  │  │           ├─ Pods-Runner.xcscheme
   │  │  │           ├─ Pods-RunnerTests.xcscheme
   │  │  │           ├─ image_picker_ios-image_picker_ios_privacy.xcscheme
   │  │  │           ├─ image_picker_ios.xcscheme
   │  │  │           ├─ shared_preferences_foundation-shared_preferences_foundation_privacy.xcscheme
   │  │  │           ├─ shared_preferences_foundation.xcscheme
   │  │  │           └─ xcschememanagement.plist
   │  │  ├─ PromisesObjC
   │  │  │  ├─ LICENSE
   │  │  │  ├─ README.md
   │  │  │  └─ Sources
   │  │  │     └─ FBLPromises
   │  │  │        ├─ FBLPromise+All.m
   │  │  │        ├─ FBLPromise+Always.m
   │  │  │        ├─ FBLPromise+Any.m
   │  │  │        ├─ FBLPromise+Async.m
   │  │  │        ├─ FBLPromise+Await.m
   │  │  │        ├─ FBLPromise+Catch.m
   │  │  │        ├─ FBLPromise+Delay.m
   │  │  │        ├─ FBLPromise+Do.m
   │  │  │        ├─ FBLPromise+Race.m
   │  │  │        ├─ FBLPromise+Recover.m
   │  │  │        ├─ FBLPromise+Reduce.m
   │  │  │        ├─ FBLPromise+Retry.m
   │  │  │        ├─ FBLPromise+Testing.m
   │  │  │        ├─ FBLPromise+Then.m
   │  │  │        ├─ FBLPromise+Timeout.m
   │  │  │        ├─ FBLPromise+Validate.m
   │  │  │        ├─ FBLPromise+Wrap.m
   │  │  │        ├─ FBLPromise.m
   │  │  │        ├─ FBLPromiseError.m
   │  │  │        ├─ Resources
   │  │  │        │  └─ PrivacyInfo.xcprivacy
   │  │  │        └─ include
   │  │  │           ├─ FBLPromise+All.h
   │  │  │           ├─ FBLPromise+Always.h
   │  │  │           ├─ FBLPromise+Any.h
   │  │  │           ├─ FBLPromise+Async.h
   │  │  │           ├─ FBLPromise+Await.h
   │  │  │           ├─ FBLPromise+Catch.h
   │  │  │           ├─ FBLPromise+Delay.h
   │  │  │           ├─ FBLPromise+Do.h
   │  │  │           ├─ FBLPromise+Race.h
   │  │  │           ├─ FBLPromise+Recover.h
   │  │  │           ├─ FBLPromise+Reduce.h
   │  │  │           ├─ FBLPromise+Retry.h
   │  │  │           ├─ FBLPromise+Testing.h
   │  │  │           ├─ FBLPromise+Then.h
   │  │  │           ├─ FBLPromise+Timeout.h
   │  │  │           ├─ FBLPromise+Validate.h
   │  │  │           ├─ FBLPromise+Wrap.h
   │  │  │           ├─ FBLPromise.h
   │  │  │           ├─ FBLPromiseError.h
   │  │  │           ├─ FBLPromisePrivate.h
   │  │  │           └─ FBLPromises.h
   │  │  ├─ Target Support Files
   │  │  │  ├─ Flutter
   │  │  │  │  ├─ Flutter.debug.xcconfig
   │  │  │  │  └─ Flutter.release.xcconfig
   │  │  │  ├─ Pods-Runner
   │  │  │  │  ├─ Pods-Runner-Info.plist
   │  │  │  │  ├─ Pods-Runner-acknowledgements.markdown
   │  │  │  │  ├─ Pods-Runner-acknowledgements.plist
   │  │  │  │  ├─ Pods-Runner-dummy.m
   │  │  │  │  ├─ Pods-Runner-frameworks-Debug-input-files.xcfilelist
   │  │  │  │  ├─ Pods-Runner-frameworks-Debug-output-files.xcfilelist
   │  │  │  │  ├─ Pods-Runner-frameworks-Profile-input-files.xcfilelist
   │  │  │  │  ├─ Pods-Runner-frameworks-Profile-output-files.xcfilelist
   │  │  │  │  ├─ Pods-Runner-frameworks-Release-input-files.xcfilelist
   │  │  │  │  ├─ Pods-Runner-frameworks-Release-output-files.xcfilelist
   │  │  │  │  ├─ Pods-Runner-frameworks.sh
   │  │  │  │  ├─ Pods-Runner-resources-Debug-input-files.xcfilelist
   │  │  │  │  ├─ Pods-Runner-resources-Debug-output-files.xcfilelist
   │  │  │  │  ├─ Pods-Runner-resources-Profile-input-files.xcfilelist
   │  │  │  │  ├─ Pods-Runner-resources-Profile-output-files.xcfilelist
   │  │  │  │  ├─ Pods-Runner-resources-Release-input-files.xcfilelist
   │  │  │  │  ├─ Pods-Runner-resources-Release-output-files.xcfilelist
   │  │  │  │  ├─ Pods-Runner-resources.sh
   │  │  │  │  ├─ Pods-Runner-umbrella.h
   │  │  │  │  ├─ Pods-Runner.debug.xcconfig
   │  │  │  │  ├─ Pods-Runner.modulemap
   │  │  │  │  ├─ Pods-Runner.profile.xcconfig
   │  │  │  │  └─ Pods-Runner.release.xcconfig
   │  │  │  ├─ Pods-RunnerTests
   │  │  │  │  ├─ Pods-RunnerTests-Info.plist
   │  │  │  │  ├─ Pods-RunnerTests-acknowledgements.markdown
   │  │  │  │  ├─ Pods-RunnerTests-acknowledgements.plist
   │  │  │  │  ├─ Pods-RunnerTests-dummy.m
   │  │  │  │  ├─ Pods-RunnerTests-umbrella.h
   │  │  │  │  ├─ Pods-RunnerTests.debug.xcconfig
   │  │  │  │  ├─ Pods-RunnerTests.modulemap
   │  │  │  │  ├─ Pods-RunnerTests.profile.xcconfig
   │  │  │  │  └─ Pods-RunnerTests.release.xcconfig
   │  │  │  ├─ image_picker_ios
   │  │  │  │  ├─ ResourceBundle-image_picker_ios_privacy-image_picker_ios-Info.plist
   │  │  │  │  ├─ image_picker_ios-Info.plist
   │  │  │  │  ├─ image_picker_ios-dummy.m
   │  │  │  │  ├─ image_picker_ios-prefix.pch
   │  │  │  │  ├─ image_picker_ios.debug.xcconfig
   │  │  │  │  ├─ image_picker_ios.modulemap
   │  │  │  │  └─ image_picker_ios.release.xcconfig
   │  │  │  └─ shared_preferences_foundation
   │  │  │     ├─ ResourceBundle-shared_preferences_foundation_privacy-shared_preferences_foundation-Info.plist
   │  │  │     ├─ shared_preferences_foundation-Info.plist
   │  │  │     ├─ shared_preferences_foundation-dummy.m
   │  │  │     ├─ shared_preferences_foundation-prefix.pch
   │  │  │     ├─ shared_preferences_foundation-umbrella.h
   │  │  │     ├─ shared_preferences_foundation.debug.xcconfig
   │  │  │     ├─ shared_preferences_foundation.modulemap
   │  │  │     └─ shared_preferences_foundation.release.xcconfig
   │  │  └─ nanopb
   │  │     ├─ LICENSE.txt
   │  │     ├─ README.md
   │  │     ├─ pb.h
   │  │     ├─ pb_common.c
   │  │     ├─ pb_common.h
   │  │     ├─ pb_decode.c
   │  │     ├─ pb_decode.h
   │  │     ├─ pb_encode.c
   │  │     ├─ pb_encode.h
   │  │     └─ spm_resources
   │  │        └─ PrivacyInfo.xcprivacy
   │  ├─ Runner
   │  │  ├─ AppDelegate.swift
   │  │  ├─ Assets.xcassets
   │  │  │  ├─ AppIcon.appiconset
   │  │  │  │  ├─ Contents.json
   │  │  │  │  ├─ Icon-App-1024x1024@1x.png
   │  │  │  │  ├─ Icon-App-20x20@1x.png
   │  │  │  │  ├─ Icon-App-20x20@2x.png
   │  │  │  │  ├─ Icon-App-20x20@3x.png
   │  │  │  │  ├─ Icon-App-29x29@1x.png
   │  │  │  │  ├─ Icon-App-29x29@2x.png
   │  │  │  │  ├─ Icon-App-29x29@3x.png
   │  │  │  │  ├─ Icon-App-40x40@1x.png
   │  │  │  │  ├─ Icon-App-40x40@2x.png
   │  │  │  │  ├─ Icon-App-40x40@3x.png
   │  │  │  │  ├─ Icon-App-60x60@2x.png
   │  │  │  │  ├─ Icon-App-60x60@3x.png
   │  │  │  │  ├─ Icon-App-76x76@1x.png
   │  │  │  │  ├─ Icon-App-76x76@2x.png
   │  │  │  │  └─ Icon-App-83.5x83.5@2x.png
   │  │  │  └─ LaunchImage.imageset
   │  │  │     ├─ Contents.json
   │  │  │     ├─ LaunchImage.png
   │  │  │     ├─ LaunchImage@2x.png
   │  │  │     ├─ LaunchImage@3x.png
   │  │  │     └─ README.md
   │  │  ├─ Base.lproj
   │  │  │  ├─ LaunchScreen.storyboard
   │  │  │  └─ Main.storyboard
   │  │  ├─ GeneratedPluginRegistrant.h
   │  │  ├─ GeneratedPluginRegistrant.m
   │  │  ├─ Info.plist
   │  │  └─ Runner-Bridging-Header.h
   │  ├─ Runner.xcodeproj
   │  │  ├─ project.pbxproj
   │  │  ├─ project.xcworkspace
   │  │  │  ├─ contents.xcworkspacedata
   │  │  │  └─ xcshareddata
   │  │  │     ├─ IDEWorkspaceChecks.plist
   │  │  │     ├─ WorkspaceSettings.xcsettings
   │  │  │     └─ swiftpm
   │  │  │        └─ configuration
   │  │  └─ xcshareddata
   │  │     └─ xcschemes
   │  │        └─ Runner.xcscheme
   │  ├─ Runner.xcworkspace
   │  │  ├─ contents.xcworkspacedata
   │  │  ├─ xcshareddata
   │  │  │  ├─ IDEWorkspaceChecks.plist
   │  │  │  ├─ WorkspaceSettings.xcsettings
   │  │  │  └─ swiftpm
   │  │  │     └─ configuration
   │  │  └─ xcuserdata
   │  │     └─ duylam1407.xcuserdatad
   │  │        └─ UserInterfaceState.xcuserstate
   │  └─ RunnerTests
   │     └─ RunnerTests.swift
   ├─ lib
   │  ├─ main.dart
   │  ├─ models
   │  │  ├─ property.dart
   │  │  ├─ task.dart
   │  │  └─ user.dart
   │  ├─ screens
   │  │  ├─ admin_invite_screen.dart
   │  │  ├─ admin_reset_password_screen.dart
   │  │  ├─ admin_user_create_screen.dart
   │  │  ├─ admin_user_list_screen.dart
   │  │  ├─ edit_task_screen.dart
   │  │  ├─ home_screen.dart
   │  │  ├─ login_screen.dart
   │  │  ├─ property_form_screen.dart
   │  │  ├─ property_list_screen.dart
   │  │  ├─ task_detail_screen.dart
   │  │  ├─ task_form_screen.dart
   │  │  ├─ task_list_screen.dart
   │  │  └─ task_search_delegate.dart
   │  ├─ services
   │  │  └─ api_service.dart
   │  └─ widgets
   │     ├─ task_advanced_filter_sheet.dart
   │     └─ task_filter_bar.dart
   ├─ linux
   │  ├─ CMakeLists.txt
   │  ├─ flutter
   │  │  ├─ CMakeLists.txt
   │  │  ├─ ephemeral
   │  │  │  └─ .plugin_symlinks
   │  │  │     ├─ file_selector_linux
   │  │  │     │  ├─ AUTHORS
   │  │  │     │  ├─ CHANGELOG.md
   │  │  │     │  ├─ LICENSE
   │  │  │     │  ├─ README.md
   │  │  │     │  ├─ example
   │  │  │     │  │  ├─ README.md
   │  │  │     │  │  ├─ lib
   │  │  │     │  │  │  ├─ get_directory_page.dart
   │  │  │     │  │  │  ├─ get_multiple_directories_page.dart
   │  │  │     │  │  │  ├─ home_page.dart
   │  │  │     │  │  │  ├─ main.dart
   │  │  │     │  │  │  ├─ open_image_page.dart
   │  │  │     │  │  │  ├─ open_multiple_images_page.dart
   │  │  │     │  │  │  ├─ open_text_page.dart
   │  │  │     │  │  │  └─ save_text_page.dart
   │  │  │     │  │  ├─ linux
   │  │  │     │  │  │  ├─ CMakeLists.txt
   │  │  │     │  │  │  ├─ flutter
   │  │  │     │  │  │  │  ├─ CMakeLists.txt
   │  │  │     │  │  │  │  └─ generated_plugins.cmake
   │  │  │     │  │  │  ├─ main.cc
   │  │  │     │  │  │  ├─ my_application.cc
   │  │  │     │  │  │  └─ my_application.h
   │  │  │     │  │  └─ pubspec.yaml
   │  │  │     │  ├─ lib
   │  │  │     │  │  ├─ file_selector_linux.dart
   │  │  │     │  │  └─ src
   │  │  │     │  │     └─ messages.g.dart
   │  │  │     │  ├─ linux
   │  │  │     │  │  ├─ CMakeLists.txt
   │  │  │     │  │  ├─ file_selector_plugin.cc
   │  │  │     │  │  ├─ file_selector_plugin_private.h
   │  │  │     │  │  ├─ include
   │  │  │     │  │  │  └─ file_selector_linux
   │  │  │     │  │  │     └─ file_selector_plugin.h
   │  │  │     │  │  ├─ messages.g.cc
   │  │  │     │  │  ├─ messages.g.h
   │  │  │     │  │  └─ test
   │  │  │     │  │     ├─ file_selector_plugin_test.cc
   │  │  │     │  │     └─ test_main.cc
   │  │  │     │  ├─ pigeons
   │  │  │     │  │  ├─ copyright.txt
   │  │  │     │  │  └─ messages.dart
   │  │  │     │  ├─ pubspec.yaml
   │  │  │     │  └─ test
   │  │  │     │     └─ file_selector_linux_test.dart
   │  │  │     ├─ image_picker_linux
   │  │  │     │  ├─ AUTHORS
   │  │  │     │  ├─ CHANGELOG.md
   │  │  │     │  ├─ LICENSE
   │  │  │     │  ├─ README.md
   │  │  │     │  ├─ example
   │  │  │     │  │  ├─ README.md
   │  │  │     │  │  ├─ lib
   │  │  │     │  │  │  └─ main.dart
   │  │  │     │  │  ├─ linux
   │  │  │     │  │  │  ├─ CMakeLists.txt
   │  │  │     │  │  │  ├─ flutter
   │  │  │     │  │  │  │  ├─ CMakeLists.txt
   │  │  │     │  │  │  │  └─ generated_plugins.cmake
   │  │  │     │  │  │  ├─ main.cc
   │  │  │     │  │  │  ├─ my_application.cc
   │  │  │     │  │  │  └─ my_application.h
   │  │  │     │  │  └─ pubspec.yaml
   │  │  │     │  ├─ lib
   │  │  │     │  │  └─ image_picker_linux.dart
   │  │  │     │  ├─ pubspec.yaml
   │  │  │     │  └─ test
   │  │  │     │     ├─ image_picker_linux_test.dart
   │  │  │     │     └─ image_picker_linux_test.mocks.dart
   │  │  │     ├─ path_provider_linux
   │  │  │     │  ├─ AUTHORS
   │  │  │     │  ├─ CHANGELOG.md
   │  │  │     │  ├─ LICENSE
   │  │  │     │  ├─ README.md
   │  │  │     │  ├─ example
   │  │  │     │  │  ├─ README.md
   │  │  │     │  │  ├─ integration_test
   │  │  │     │  │  │  └─ path_provider_test.dart
   │  │  │     │  │  ├─ lib
   │  │  │     │  │  │  └─ main.dart
   │  │  │     │  │  ├─ linux
   │  │  │     │  │  │  ├─ CMakeLists.txt
   │  │  │     │  │  │  ├─ flutter
   │  │  │     │  │  │  │  ├─ CMakeLists.txt
   │  │  │     │  │  │  │  └─ generated_plugins.cmake
   │  │  │     │  │  │  ├─ main.cc
   │  │  │     │  │  │  ├─ my_application.cc
   │  │  │     │  │  │  └─ my_application.h
   │  │  │     │  │  ├─ pubspec.yaml
   │  │  │     │  │  └─ test_driver
   │  │  │     │  │     └─ integration_test.dart
   │  │  │     │  ├─ lib
   │  │  │     │  │  ├─ path_provider_linux.dart
   │  │  │     │  │  └─ src
   │  │  │     │  │     ├─ get_application_id.dart
   │  │  │     │  │     ├─ get_application_id_real.dart
   │  │  │     │  │     ├─ get_application_id_stub.dart
   │  │  │     │  │     └─ path_provider_linux.dart
   │  │  │     │  ├─ pubspec.yaml
   │  │  │     │  └─ test
   │  │  │     │     ├─ get_application_id_test.dart
   │  │  │     │     └─ path_provider_linux_test.dart
   │  │  │     └─ shared_preferences_linux
   │  │  │        ├─ AUTHORS
   │  │  │        ├─ CHANGELOG.md
   │  │  │        ├─ LICENSE
   │  │  │        ├─ README.md
   │  │  │        ├─ example
   │  │  │        │  ├─ README.md
   │  │  │        │  ├─ integration_test
   │  │  │        │  │  └─ shared_preferences_test.dart
   │  │  │        │  ├─ lib
   │  │  │        │  │  └─ main.dart
   │  │  │        │  ├─ linux
   │  │  │        │  │  ├─ CMakeLists.txt
   │  │  │        │  │  ├─ flutter
   │  │  │        │  │  │  ├─ CMakeLists.txt
   │  │  │        │  │  │  └─ generated_plugins.cmake
   │  │  │        │  │  ├─ main.cc
   │  │  │        │  │  ├─ my_application.cc
   │  │  │        │  │  └─ my_application.h
   │  │  │        │  ├─ pubspec.yaml
   │  │  │        │  └─ test_driver
   │  │  │        │     └─ integration_test.dart
   │  │  │        ├─ lib
   │  │  │        │  └─ shared_preferences_linux.dart
   │  │  │        ├─ pubspec.yaml
   │  │  │        └─ test
   │  │  │           ├─ fake_path_provider_linux.dart
   │  │  │           ├─ legacy_shared_preferences_linux_test.dart
   │  │  │           └─ shared_preferences_linux_async_test.dart
   │  │  ├─ generated_plugin_registrant.cc
   │  │  ├─ generated_plugin_registrant.h
   │  │  └─ generated_plugins.cmake
   │  └─ runner
   │     ├─ CMakeLists.txt
   │     ├─ main.cc
   │     ├─ my_application.cc
   │     └─ my_application.h
   ├─ macos
   │  ├─ Flutter
   │  │  ├─ Flutter-Debug.xcconfig
   │  │  ├─ Flutter-Release.xcconfig
   │  │  ├─ GeneratedPluginRegistrant.swift
   │  │  └─ ephemeral
   │  │     ├─ Flutter-Generated.xcconfig
   │  │     └─ flutter_export_environment.sh
   │  ├─ Podfile
   │  ├─ Runner
   │  │  ├─ AppDelegate.swift
   │  │  ├─ Assets.xcassets
   │  │  │  └─ AppIcon.appiconset
   │  │  │     ├─ Contents.json
   │  │  │     ├─ app_icon_1024.png
   │  │  │     ├─ app_icon_128.png
   │  │  │     ├─ app_icon_16.png
   │  │  │     ├─ app_icon_256.png
   │  │  │     ├─ app_icon_32.png
   │  │  │     ├─ app_icon_512.png
   │  │  │     └─ app_icon_64.png
   │  │  ├─ Base.lproj
   │  │  │  └─ MainMenu.xib
   │  │  ├─ Configs
   │  │  │  ├─ AppInfo.xcconfig
   │  │  │  ├─ Debug.xcconfig
   │  │  │  ├─ Release.xcconfig
   │  │  │  └─ Warnings.xcconfig
   │  │  ├─ DebugProfile.entitlements
   │  │  ├─ Info.plist
   │  │  ├─ MainFlutterWindow.swift
   │  │  └─ Release.entitlements
   │  ├─ Runner.xcodeproj
   │  │  ├─ project.pbxproj
   │  │  ├─ project.xcworkspace
   │  │  │  └─ xcshareddata
   │  │  │     ├─ IDEWorkspaceChecks.plist
   │  │  │     └─ swiftpm
   │  │  │        └─ configuration
   │  │  └─ xcshareddata
   │  │     └─ xcschemes
   │  │        └─ Runner.xcscheme
   │  ├─ Runner.xcworkspace
   │  │  ├─ contents.xcworkspacedata
   │  │  └─ xcshareddata
   │  │     ├─ IDEWorkspaceChecks.plist
   │  │     └─ swiftpm
   │  │        └─ configuration
   │  └─ RunnerTests
   │     └─ RunnerTests.swift
   ├─ pubspec.lock
   ├─ pubspec.yaml
   ├─ test
   │  └─ widget_test.dart
   ├─ web
   │  ├─ favicon.png
   │  ├─ icons
   │  │  ├─ Icon-192.png
   │  │  ├─ Icon-512.png
   │  │  ├─ Icon-maskable-192.png
   │  │  └─ Icon-maskable-512.png
   │  ├─ index.html
   │  └─ manifest.json
   └─ windows
      ├─ CMakeLists.txt
      ├─ flutter
      │  ├─ CMakeLists.txt
      │  ├─ ephemeral
      │  │  └─ .plugin_symlinks
      │  │     ├─ file_selector_windows
      │  │     │  ├─ AUTHORS
      │  │     │  ├─ CHANGELOG.md
      │  │     │  ├─ LICENSE
      │  │     │  ├─ README.md
      │  │     │  ├─ example
      │  │     │  │  ├─ README.md
      │  │     │  │  ├─ lib
      │  │     │  │  │  ├─ get_directory_page.dart
      │  │     │  │  │  ├─ get_multiple_directories_page.dart
      │  │     │  │  │  ├─ home_page.dart
      │  │     │  │  │  ├─ main.dart
      │  │     │  │  │  ├─ open_image_page.dart
      │  │     │  │  │  ├─ open_multiple_images_page.dart
      │  │     │  │  │  ├─ open_text_page.dart
      │  │     │  │  │  └─ save_text_page.dart
      │  │     │  │  ├─ pubspec.yaml
      │  │     │  │  └─ windows
      │  │     │  │     ├─ CMakeLists.txt
      │  │     │  │     ├─ flutter
      │  │     │  │     │  ├─ CMakeLists.txt
      │  │     │  │     │  └─ generated_plugins.cmake
      │  │     │  │     └─ runner
      │  │     │  │        ├─ CMakeLists.txt
      │  │     │  │        ├─ Runner.rc
      │  │     │  │        ├─ flutter_window.cpp
      │  │     │  │        ├─ flutter_window.h
      │  │     │  │        ├─ main.cpp
      │  │     │  │        ├─ resource.h
      │  │     │  │        ├─ resources
      │  │     │  │        │  └─ app_icon.ico
      │  │     │  │        ├─ runner.exe.manifest
      │  │     │  │        ├─ utils.cpp
      │  │     │  │        ├─ utils.h
      │  │     │  │        ├─ win32_window.cpp
      │  │     │  │        └─ win32_window.h
      │  │     │  ├─ lib
      │  │     │  │  ├─ file_selector_windows.dart
      │  │     │  │  └─ src
      │  │     │  │     └─ messages.g.dart
      │  │     │  ├─ pigeons
      │  │     │  │  ├─ copyright.txt
      │  │     │  │  └─ messages.dart
      │  │     │  ├─ pubspec.yaml
      │  │     │  ├─ test
      │  │     │  │  ├─ file_selector_windows_test.dart
      │  │     │  │  ├─ file_selector_windows_test.mocks.dart
      │  │     │  │  └─ test_api.g.dart
      │  │     │  └─ windows
      │  │     │     ├─ CMakeLists.txt
      │  │     │     ├─ file_dialog_controller.cpp
      │  │     │     ├─ file_dialog_controller.h
      │  │     │     ├─ file_selector_plugin.cpp
      │  │     │     ├─ file_selector_plugin.h
      │  │     │     ├─ file_selector_windows.cpp
      │  │     │     ├─ include
      │  │     │     │  └─ file_selector_windows
      │  │     │     │     └─ file_selector_windows.h
      │  │     │     ├─ messages.g.cpp
      │  │     │     ├─ messages.g.h
      │  │     │     ├─ string_utils.cpp
      │  │     │     ├─ string_utils.h
      │  │     │     └─ test
      │  │     │        ├─ file_selector_plugin_test.cpp
      │  │     │        ├─ test_file_dialog_controller.cpp
      │  │     │        ├─ test_file_dialog_controller.h
      │  │     │        ├─ test_main.cpp
      │  │     │        ├─ test_utils.cpp
      │  │     │        └─ test_utils.h
      │  │     ├─ image_picker_windows
      │  │     │  ├─ AUTHORS
      │  │     │  ├─ CHANGELOG.md
      │  │     │  ├─ LICENSE
      │  │     │  ├─ README.md
      │  │     │  ├─ example
      │  │     │  │  ├─ README.md
      │  │     │  │  ├─ lib
      │  │     │  │  │  └─ main.dart
      │  │     │  │  ├─ pubspec.yaml
      │  │     │  │  └─ windows
      │  │     │  │     ├─ CMakeLists.txt
      │  │     │  │     ├─ flutter
      │  │     │  │     │  ├─ CMakeLists.txt
      │  │     │  │     │  └─ generated_plugins.cmake
      │  │     │  │     └─ runner
      │  │     │  │        ├─ CMakeLists.txt
      │  │     │  │        ├─ Runner.rc
      │  │     │  │        ├─ flutter_window.cpp
      │  │     │  │        ├─ flutter_window.h
      │  │     │  │        ├─ main.cpp
      │  │     │  │        ├─ resource.h
      │  │     │  │        ├─ resources
      │  │     │  │        │  └─ app_icon.ico
      │  │     │  │        ├─ runner.exe.manifest
      │  │     │  │        ├─ utils.cpp
      │  │     │  │        ├─ utils.h
      │  │     │  │        ├─ win32_window.cpp
      │  │     │  │        └─ win32_window.h
      │  │     │  ├─ lib
      │  │     │  │  └─ image_picker_windows.dart
      │  │     │  ├─ pubspec.yaml
      │  │     │  └─ test
      │  │     │     ├─ image_picker_windows_test.dart
      │  │     │     └─ image_picker_windows_test.mocks.dart
      │  │     ├─ path_provider_windows
      │  │     │  ├─ AUTHORS
      │  │     │  ├─ CHANGELOG.md
      │  │     │  ├─ LICENSE
      │  │     │  ├─ README.md
      │  │     │  ├─ example
      │  │     │  │  ├─ README.md
      │  │     │  │  ├─ integration_test
      │  │     │  │  │  └─ path_provider_test.dart
      │  │     │  │  ├─ lib
      │  │     │  │  │  └─ main.dart
      │  │     │  │  ├─ pubspec.yaml
      │  │     │  │  ├─ test_driver
      │  │     │  │  │  └─ integration_test.dart
      │  │     │  │  └─ windows
      │  │     │  │     ├─ CMakeLists.txt
      │  │     │  │     ├─ flutter
      │  │     │  │     │  ├─ CMakeLists.txt
      │  │     │  │     │  └─ generated_plugins.cmake
      │  │     │  │     └─ runner
      │  │     │  │        ├─ CMakeLists.txt
      │  │     │  │        ├─ Runner.rc
      │  │     │  │        ├─ flutter_window.cpp
      │  │     │  │        ├─ flutter_window.h
      │  │     │  │        ├─ main.cpp
      │  │     │  │        ├─ resource.h
      │  │     │  │        ├─ resources
      │  │     │  │        │  └─ app_icon.ico
      │  │     │  │        ├─ run_loop.cpp
      │  │     │  │        ├─ run_loop.h
      │  │     │  │        ├─ runner.exe.manifest
      │  │     │  │        ├─ utils.cpp
      │  │     │  │        ├─ utils.h
      │  │     │  │        ├─ win32_window.cpp
      │  │     │  │        └─ win32_window.h
      │  │     │  ├─ lib
      │  │     │  │  ├─ path_provider_windows.dart
      │  │     │  │  └─ src
      │  │     │  │     ├─ folders.dart
      │  │     │  │     ├─ folders_stub.dart
      │  │     │  │     ├─ guid.dart
      │  │     │  │     ├─ path_provider_windows_real.dart
      │  │     │  │     ├─ path_provider_windows_stub.dart
      │  │     │  │     └─ win32_wrappers.dart
      │  │     │  ├─ pubspec.yaml
      │  │     │  └─ test
      │  │     │     ├─ guid_test.dart
      │  │     │     └─ path_provider_windows_test.dart
      │  │     └─ shared_preferences_windows
      │  │        ├─ AUTHORS
      │  │        ├─ CHANGELOG.md
      │  │        ├─ LICENSE
      │  │        ├─ README.md
      │  │        ├─ example
      │  │        │  ├─ AUTHORS
      │  │        │  ├─ LICENSE
      │  │        │  ├─ README.md
      │  │        │  ├─ integration_test
      │  │        │  │  └─ shared_preferences_test.dart
      │  │        │  ├─ lib
      │  │        │  │  └─ main.dart
      │  │        │  ├─ pubspec.yaml
      │  │        │  ├─ test_driver
      │  │        │  │  └─ integration_test.dart
      │  │        │  └─ windows
      │  │        │     ├─ CMakeLists.txt
      │  │        │     ├─ flutter
      │  │        │     │  ├─ CMakeLists.txt
      │  │        │     │  └─ generated_plugins.cmake
      │  │        │     └─ runner
      │  │        │        ├─ CMakeLists.txt
      │  │        │        ├─ Runner.rc
      │  │        │        ├─ flutter_window.cpp
      │  │        │        ├─ flutter_window.h
      │  │        │        ├─ main.cpp
      │  │        │        ├─ resource.h
      │  │        │        ├─ resources
      │  │        │        │  └─ app_icon.ico
      │  │        │        ├─ run_loop.cpp
      │  │        │        ├─ run_loop.h
      │  │        │        ├─ runner.exe.manifest
      │  │        │        ├─ utils.cpp
      │  │        │        ├─ utils.h
      │  │        │        ├─ win32_window.cpp
      │  │        │        └─ win32_window.h
      │  │        ├─ lib
      │  │        │  └─ shared_preferences_windows.dart
      │  │        ├─ pubspec.yaml
      │  │        └─ test
      │  │           ├─ fake_path_provider_windows.dart
      │  │           ├─ legacy_shared_preferences_windows_test.dart
      │  │           └─ shared_preferences_windows_async_test.dart
      │  ├─ generated_plugin_registrant.cc
      │  ├─ generated_plugin_registrant.h
      │  └─ generated_plugins.cmake
      └─ runner
         ├─ CMakeLists.txt
         ├─ Runner.rc
         ├─ flutter_window.cpp
         ├─ flutter_window.h
         ├─ main.cpp
         ├─ resource.h
         ├─ resources
         │  └─ app_icon.ico
         ├─ runner.exe.manifest
         ├─ utils.cpp
         ├─ utils.h
         ├─ win32_window.cpp
         └─ win32_window.h

```