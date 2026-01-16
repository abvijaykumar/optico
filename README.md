# Optico

A modern local music player app for Android and iOS with a Spotify-inspired design. Built with Flutter.

## Features

- **Modern Spotify-like UI** - Dark theme with green accents, smooth animations, and familiar navigation
- **Local Music Playback** - Play MP3, M4A, FLAC, WAV, OGG, and other audio formats from your device
- **Folder Management** - Add multiple music folders and scan for audio files
- **Library Organization** - Browse by songs, albums, artists, or playlists
- **Queue Management** - Add songs to queue, play next, shuffle, and repeat
- **Mini Player** - Persistent mini player with quick controls
- **Full Player** - Expanded player view with album art, progress bar, and all controls
- **Playlists** - Create and manage custom playlists
- **Favorites** - Like songs to save them to your favorites
- **Search** - Find songs, albums, and artists quickly
- **Background Playback** - Continue listening while using other apps

## Screenshots

The app features:
- Home screen with recently played and recommended content
- Search screen with browse categories
- Library screen with playlists, artists, albums, and songs tabs
- Full-screen player with queue management
- Settings screen for folder management

## Getting Started

### Prerequisites

- Flutter SDK 3.0.0 or higher
- Android Studio or VS Code with Flutter extensions
- For Android: Android SDK 21+ (Android 5.0 Lollipop)
- For iOS: iOS 12.0+

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/optico.git
cd optico
```

2. Install dependencies:
```bash
flutter pub get
```

3. Run the app:
```bash
flutter run
```

### Building for Release

**Android:**
```bash
flutter build apk --release
```

**iOS:**
```bash
flutter build ios --release
```

## Architecture

The app follows a clean architecture pattern with:

- **Models** - Data classes for Song, Album, Artist, Playlist, and MusicFolder
- **Services** - Database service (SQLite), Audio player service (just_audio), Music scanner service
- **Providers** - State management with Provider package for Library and Player state
- **Screens** - UI screens for navigation, detail views, and settings
- **Widgets** - Reusable UI components like SongTile, AlbumCard, MiniPlayer

## Dependencies

- `just_audio` - Audio playback
- `audio_service` - Background audio support
- `file_picker` - Folder selection
- `flutter_media_metadata` - Audio file metadata extraction
- `provider` - State management
- `sqflite` - Local database
- `permission_handler` - Storage permissions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
